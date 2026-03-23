#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# HireRanker — Full deployment script
# Provisions: Neon DB, Upstash Redis, Render (API + Worker), Vercel (Frontend)
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

: "${NEON_API_KEY:?'Set NEON_API_KEY'}"
# Optional — required only for org-based Neon accounts
NEON_ORG_ID="${NEON_ORG_ID:-}"
: "${UPSTASH_EMAIL:?'Set UPSTASH_EMAIL (your Upstash account email)'}"
: "${UPSTASH_API_KEY:?'Set UPSTASH_API_KEY'}"
: "${RENDER_API_KEY:?'Set RENDER_API_KEY'}"
: "${VERCEL_API_KEY:?'Set VERCEL_API_KEY'}"
: "${ANTHROPIC_API_KEY:?'Set ANTHROPIC_API_KEY'}"

GITHUB_REPO_OWNER="${GITHUB_REPO_OWNER:-SarswaManish}"
GITHUB_REPO_NAME="${GITHUB_REPO_NAME:-hireranker}"
GITHUB_BRANCH="${GITHUB_BRANCH:-main}"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${GREEN}[✓]${NC} $*"; }
warn()    { echo -e "${YELLOW}[!]${NC} $*"; }
err()     { echo -e "${RED}[✗]${NC} $*" >&2; }
section() { echo -e "\n${YELLOW}══ $* ══${NC}"; }

die() { err "$1"; exit 1; }

api_call() {
  local label="$1"; local method="$2"; local url="$3"
  shift 3
  local resp http_code tmp
  tmp=$(mktemp)
  http_code=$(curl -s -o "$tmp" -w "%{http_code}" -X "$method" "$url" "$@")
  resp=$(cat "$tmp"); rm -f "$tmp"
  if [[ "$http_code" -ge 400 ]]; then
    die "$label failed (HTTP $http_code): $resp"
  fi
  echo "$resp"
}

api_post() { api_call "$1" POST "$2" "${@:3}"; }
api_get()  { api_call "$1" GET  "$2" "${@:3}"; }

# ─────────────────────────────────────────────────────────────────────────────
section "1/4 — Neon PostgreSQL"
# ─────────────────────────────────────────────────────────────────────────────

# Build project payload — include org_id when available.
# For org-based accounts, org_id is required. Auto-discover from existing
# projects, or fall back to the NEON_ORG_ID env var / secret.
if [[ -z "$NEON_ORG_ID" ]]; then
  NEON_PROJECTS_RESP=$(curl -s \
    "https://console.neon.tech/api/v2/projects?limit=20" \
    -H "Authorization: Bearer $NEON_API_KEY")
  NEON_ORG_ID=$(echo "$NEON_PROJECTS_RESP" | jq -r \
    '[.projects[]? | select(.org_id? and .org_id != null and .org_id != "")] | .[0].org_id // empty')
fi

if [[ -n "$NEON_ORG_ID" ]]; then
  info "Neon org: $NEON_ORG_ID"
  NEON_PROJECT_BODY=$(jq -n --arg oid "$NEON_ORG_ID" \
    '{"project":{"name":"hireranker","pg_version":16,"region_id":"aws-us-east-2","org_id":$oid}}')
else
  NEON_PROJECT_BODY='{"project":{"name":"hireranker","pg_version":16,"region_id":"aws-us-east-2"}}'
fi

NEON_RESPONSE=$(api_post "Neon create project" \
  "https://console.neon.tech/api/v2/projects" \
  -H "Authorization: Bearer $NEON_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$NEON_PROJECT_BODY")

NEON_PROJECT_ID=$(echo "$NEON_RESPONSE" | jq -r '.project.id')

# Parse connection URI or fallback to connection_parameters
NEON_URI=$(echo "$NEON_RESPONSE" | jq -r '.connection_uris[0].connection_uri // empty')
if [[ -n "$NEON_URI" && "$NEON_URI" != "null" ]]; then
  DB_USER=$(echo "$NEON_URI"     | sed 's|postgresql://||' | cut -d: -f1)
  DB_PASSWORD=$(echo "$NEON_URI" | sed 's|postgresql://[^:]*:||' | cut -d@ -f1)
  DB_HOST=$(echo "$NEON_URI"     | cut -d@ -f2 | cut -d/ -f1 | cut -d: -f1)
  DB_NAME=$(echo "$NEON_URI"     | cut -d/ -f4 | cut -d? -f1)
else
  DB_HOST=$(echo "$NEON_RESPONSE"     | jq -r '.connection_uris[0].connection_parameters.host')
  DB_NAME=$(echo "$NEON_RESPONSE"     | jq -r '.connection_uris[0].connection_parameters.database')
  DB_USER=$(echo "$NEON_RESPONSE"     | jq -r '.connection_uris[0].connection_parameters.user')
  DB_PASSWORD=$(echo "$NEON_RESPONSE" | jq -r '.connection_uris[0].connection_parameters.password')
fi
DB_PORT="5432"

info "Neon project: $NEON_PROJECT_ID"
info "DB: $DB_USER@$DB_HOST/$DB_NAME"

# ─────────────────────────────────────────────────────────────────────────────
section "2/4 — Upstash Redis"
# ─────────────────────────────────────────────────────────────────────────────
# Upstash Management API v2 uses HTTP Basic auth: email:api_key

UPSTASH_AUTH=$(printf '%s:%s' "$UPSTASH_EMAIL" "$UPSTASH_API_KEY" | base64 -w0)

UPSTASH_RESPONSE=$(api_post "Upstash create Redis" \
  "https://api.upstash.com/v2/redis/database" \
  -H "Authorization: Basic $UPSTASH_AUTH" \
  -H "Content-Type: application/json" \
  -d '{"name":"hireranker","platform":"aws","primary_region":"us-east-1","tls":true}')

REDIS_ENDPOINT=$(echo "$UPSTASH_RESPONSE" | jq -r '.endpoint')
REDIS_PORT=$(echo "$UPSTASH_RESPONSE"     | jq -r '.port')
REDIS_PASSWORD=$(echo "$UPSTASH_RESPONSE" | jq -r '.password')

REDIS_URL="rediss://default:${REDIS_PASSWORD}@${REDIS_ENDPOINT}:${REDIS_PORT}"
CELERY_BROKER_URL="${REDIS_URL}/1"
CELERY_RESULT_BACKEND="${REDIS_URL}/2"

info "Upstash Redis: $REDIS_ENDPOINT:$REDIS_PORT"

# ─────────────────────────────────────────────────────────────────────────────
section "3/4 — Render (web service + background worker)"
# ─────────────────────────────────────────────────────────────────────────────
warn "Repo: github.com/$GITHUB_REPO_OWNER/$GITHUB_REPO_NAME  branch: $GITHUB_BRANCH"

RENDER_OWNER=$(api_get "Render owner" \
  "https://api.render.com/v1/owners?limit=1" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Accept: application/json")
RENDER_OWNER_ID=$(echo "$RENDER_OWNER" | jq -r '.[0].owner.id // .[0].id')
info "Render owner: $RENDER_OWNER_ID"

COMMON_ENV=$(jq -n \
  --arg ds "config.settings.production" \
  --arg dh "$DB_HOST" --arg dn "$DB_NAME" --arg du "$DB_USER" \
  --arg dp "$DB_PASSWORD" --arg dport "$DB_PORT" \
  --arg ru "$REDIS_URL" --arg cb "$CELERY_BROKER_URL" --arg cr "$CELERY_RESULT_BACKEND" \
  --arg ak "$ANTHROPIC_API_KEY" \
  '[
    {"key":"DJANGO_SETTINGS_MODULE","value":$ds},
    {"key":"DB_HOST","value":$dh},
    {"key":"DB_NAME","value":$dn},
    {"key":"DB_USER","value":$du},
    {"key":"DB_PASSWORD","value":$dp},
    {"key":"DB_PORT","value":$dport},
    {"key":"REDIS_URL","value":$ru},
    {"key":"CELERY_BROKER_URL","value":$cb},
    {"key":"CELERY_RESULT_BACKEND","value":$cr},
    {"key":"ANTHROPIC_API_KEY","value":$ak},
    {"key":"ANTHROPIC_DEFAULT_MODEL","value":"claude-sonnet-4-6"},
    {"key":"ANTHROPIC_FAST_MODEL","value":"claude-haiku-4-5-20251001"},
    {"key":"USE_S3","value":"false"},
    {"key":"STRIPE_SECRET_KEY","value":""},
    {"key":"STRIPE_PUBLISHABLE_KEY","value":""},
    {"key":"STRIPE_WEBHOOK_SECRET","value":""},
    {"key":"DJANGO_LOG_LEVEL","value":"WARNING"}
  ]')

API_ENV=$(echo "$COMMON_ENV" | jq \
  '. + [
    {"key":"ALLOWED_HOSTS","value":"hireranker-api.onrender.com"},
    {"key":"WEB_CONCURRENCY","value":"2"},
    {"key":"CORS_ALLOWED_ORIGINS","value":"https://hireranker.vercel.app"}
  ]')

# Render API v1 requires "env" (runtime) inside serviceDetails
API_PAYLOAD=$(jq -n \
  --arg oid "$RENDER_OWNER_ID" \
  --arg repo "https://github.com/$GITHUB_REPO_OWNER/$GITHUB_REPO_NAME" \
  --arg branch "$GITHUB_BRANCH" \
  --argjson env "$API_ENV" \
  '{
    "autoDeploy": "yes",
    "branch": $branch,
    "name": "hireranker-api",
    "ownerId": $oid,
    "repo": $repo,
    "rootDir": "backend",
    "serviceDetails": {
      "env": "python",
      "envSpecificDetails": {
        "buildCommand": "./build.sh",
        "startCommand": "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120 --log-level info"
      },
      "healthCheckPath": "/api/health/",
      "numInstances": 1,
      "plan": "free"
    },
    "type": "web_service",
    "envVars": $env
  }')

API_RESPONSE=$(api_post "Render web service" \
  "https://api.render.com/v1/services" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d "$API_PAYLOAD")

API_SERVICE_ID=$(echo "$API_RESPONSE" | jq -r '.service.id // .id')
API_URL="https://hireranker-api.onrender.com"
info "Render API service: $API_SERVICE_ID  →  $API_URL"

WORKER_PAYLOAD=$(jq -n \
  --arg oid "$RENDER_OWNER_ID" \
  --arg repo "https://github.com/$GITHUB_REPO_OWNER/$GITHUB_REPO_NAME" \
  --arg branch "$GITHUB_BRANCH" \
  --argjson env "$COMMON_ENV" \
  '{
    "autoDeploy": "yes",
    "branch": $branch,
    "name": "hireranker-worker",
    "ownerId": $oid,
    "repo": $repo,
    "rootDir": "backend",
    "serviceDetails": {
      "env": "python",
      "envSpecificDetails": {
        "buildCommand": "pip install -r requirements.txt",
        "startCommand": "celery -A celery_app worker -l info -Q resumes,evaluations,default --concurrency 1 --max-tasks-per-child 50"
      },
      "numInstances": 1,
      "plan": "free"
    },
    "type": "background_worker",
    "envVars": $env
  }')

WORKER_TMP=$(mktemp)
WORKER_CODE=$(curl -s -o "$WORKER_TMP" -w "%{http_code}" \
  -X POST "https://api.render.com/v1/services" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d "$WORKER_PAYLOAD")
WORKER_RESPONSE=$(cat "$WORKER_TMP"); rm -f "$WORKER_TMP"

if [[ "$WORKER_CODE" -ge 400 ]]; then
  err "Render background worker failed (HTTP $WORKER_CODE): $WORKER_RESPONSE"
  warn "Celery worker skipped — background workers require a paid Render plan."
  warn "Add a card at https://dashboard.render.com/billing, then re-run or"
  warn "create the worker manually (rootDir: backend, start: celery -A celery_app worker)."
  WORKER_SERVICE_ID=""
else
  WORKER_SERVICE_ID=$(echo "$WORKER_RESPONSE" | jq -r '.service.id // .id')
  info "Render worker: $WORKER_SERVICE_ID"
fi

# ─────────────────────────────────────────────────────────────────────────────
section "4/4 — Vercel (Next.js frontend)"
# ─────────────────────────────────────────────────────────────────────────────

VERCEL_USER=$(api_get "Vercel auth" \
  "https://api.vercel.com/v2/user" \
  -H "Authorization: Bearer $VERCEL_API_KEY")
VERCEL_USERNAME=$(echo "$VERCEL_USER" | jq -r '.user.username')
info "Vercel user: $VERCEL_USERNAME"

# Check for teams — project creation may need a teamId
VERCEL_TEAMS=$(curl -s "https://api.vercel.com/v2/teams?limit=1" \
  -H "Authorization: Bearer $VERCEL_API_KEY")
VERCEL_TEAM_ID=$(echo "$VERCEL_TEAMS" | jq -r '.teams[0].id // empty')

if [[ -n "$VERCEL_TEAM_ID" && "$VERCEL_TEAM_ID" != "null" ]]; then
  info "Vercel team: $VERCEL_TEAM_ID"
  VERCEL_QUERY="?teamId=${VERCEL_TEAM_ID}"
else
  VERCEL_QUERY=""
fi

# Get GitHub repo ID (required by Vercel gitSource)
GH_REPO_INFO=$(curl -s "https://api.github.com/repos/$GITHUB_REPO_OWNER/$GITHUB_REPO_NAME")
GH_REPO_ID=$(echo "$GH_REPO_INFO" | jq -r '.id')
if [[ -z "$GH_REPO_ID" || "$GH_REPO_ID" == "null" ]]; then
  die "Could not fetch GitHub repo ID for $GITHUB_REPO_OWNER/$GITHUB_REPO_NAME"
fi
info "GitHub repo ID: $GH_REPO_ID"

VERCEL_PROJECT_ID=""
VERCEL_PROJECT_NAME=""
VERCEL_SKIP=false

# Check for existing project first (idempotent re-runs)
VERCEL_EXISTING_TMP=$(mktemp)
VERCEL_EXISTING_CODE=$(curl -s -o "$VERCEL_EXISTING_TMP" -w "%{http_code}" \
  "https://api.vercel.com/v9/projects/hireranker${VERCEL_QUERY}" \
  -H "Authorization: Bearer $VERCEL_API_KEY")
VERCEL_EXISTING_BODY=$(cat "$VERCEL_EXISTING_TMP"); rm -f "$VERCEL_EXISTING_TMP"

if [[ "$VERCEL_EXISTING_CODE" == "200" ]]; then
  VERCEL_PROJECT_ID=$(echo "$VERCEL_EXISTING_BODY" | jq -r '.id')
  VERCEL_PROJECT_NAME=$(echo "$VERCEL_EXISTING_BODY" | jq -r '.name')
  info "Vercel project (existing): $VERCEL_PROJECT_ID  ($VERCEL_PROJECT_NAME)"
else
  VERCEL_PROJECT_PAYLOAD=$(jq -n '{
    "name": "hireranker",
    "framework": "nextjs",
    "rootDirectory": "frontend",
    "buildCommand": "npm run build",
    "outputDirectory": ".next",
    "installCommand": "npm install"
  }')

  # Try personal scope first, then team scope
  for query in "" "$VERCEL_QUERY"; do
    VERCEL_CREATE_TMP=$(mktemp)
    VERCEL_CREATE_CODE=$(curl -s -o "$VERCEL_CREATE_TMP" -w "%{http_code}" \
      -X POST "https://api.vercel.com/v9/projects${query}" \
      -H "Authorization: Bearer $VERCEL_API_KEY" \
      -H "Content-Type: application/json" \
      -d "$VERCEL_PROJECT_PAYLOAD")
    VERCEL_PROJECT=$(cat "$VERCEL_CREATE_TMP"); rm -f "$VERCEL_CREATE_TMP"
    [[ "$VERCEL_CREATE_CODE" -lt 400 ]] && break
  done

  if [[ "$VERCEL_CREATE_CODE" -ge 400 ]]; then
    err "Vercel project failed (HTTP $VERCEL_CREATE_CODE): $VERCEL_PROJECT"
    warn "Vercel project could not be created automatically (token lacks create-project scope)."
    warn "Create it manually at vercel.com/new, import github.com/$GITHUB_REPO_OWNER/$GITHUB_REPO_NAME,"
    warn "set Root Directory to 'frontend', and add env var NEXT_PUBLIC_API_URL=$API_URL"
    VERCEL_SKIP=true
  else
    VERCEL_PROJECT_ID=$(echo "$VERCEL_PROJECT" | jq -r '.id')
    VERCEL_PROJECT_NAME=$(echo "$VERCEL_PROJECT" | jq -r '.name')
    info "Vercel project: $VERCEL_PROJECT_ID  ($VERCEL_PROJECT_NAME)"
  fi
fi

if [[ "$VERCEL_SKIP" != "true" && -n "$VERCEL_PROJECT_ID" ]]; then
  ENV_PAYLOAD=$(jq -n --arg apiurl "$API_URL" '[
    {"key":"NEXT_PUBLIC_API_URL","value":$apiurl,"type":"plain","target":["production","preview","development"]},
    {"key":"NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY","value":"","type":"plain","target":["production","preview","development"]}
  ]')
  VERCEL_ENV_TMP=$(mktemp)
  VERCEL_ENV_CODE=$(curl -s -o "$VERCEL_ENV_TMP" -w "%{http_code}" \
    -X POST "https://api.vercel.com/v9/projects/${VERCEL_PROJECT_ID}/env${VERCEL_QUERY}" \
    -H "Authorization: Bearer $VERCEL_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$ENV_PAYLOAD")
  rm -f "$VERCEL_ENV_TMP"
  [[ "$VERCEL_ENV_CODE" -lt 400 ]] && info "Vercel env vars set" \
    || warn "Vercel env vars failed (HTTP $VERCEL_ENV_CODE) — set manually in dashboard"
  warn "ACTION REQUIRED: Connect GitHub repo in Vercel dashboard:"
  warn "  vercel.com/${VERCEL_USERNAME}/hireranker/settings/git"
  warn "  → connect  github.com/$GITHUB_REPO_OWNER/$GITHUB_REPO_NAME  (root dir: frontend)"
fi

VERCEL_URL="https://${VERCEL_PROJECT_NAME:-hireranker}.vercel.app"

# ─────────────────────────────────────────────────────────────────────────────
section "Done"
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "  Backend API:  $API_URL"
echo "  Frontend:     $VERCEL_URL"
echo "  Neon DB:      $DB_HOST / $DB_NAME"
echo "  Redis:        $REDIS_ENDPOINT"
echo ""
echo "  ⚠  Render first deploy takes ~5 min. Check: https://dashboard.render.com"
echo ""
