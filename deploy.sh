#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# HireRanker — Full deployment script
# Provisions: Neon DB, Upstash Redis, Render (API + Worker), Vercel (Frontend)
#
# Usage:
#   export NEON_API_KEY UPSTASH_API_KEY RENDER_API_KEY VERCEL_API_KEY ANTHROPIC_API_KEY
#   ./deploy.sh
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail   # no -e so we can show friendly errors

: "${NEON_API_KEY:?'Set NEON_API_KEY'}"
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

# Helper: POST with full error output
api_post() {
  local label="$1"; local url="$2"; local data="$3"
  shift 3
  local resp http_code tmp
  tmp=$(mktemp)
  http_code=$(curl -s -o "$tmp" -w "%{http_code}" -X POST "$url" "$@" -d "$data")
  resp=$(cat "$tmp"); rm -f "$tmp"
  if [[ "$http_code" -ge 400 ]]; then
    err "$label failed (HTTP $http_code)"
    echo "  Response: $resp" >&2
    return 1
  fi
  echo "$resp"
}

api_get() {
  local label="$1"; local url="$2"
  shift 2
  local resp http_code tmp
  tmp=$(mktemp)
  http_code=$(curl -s -o "$tmp" -w "%{http_code}" "$url" "$@")
  resp=$(cat "$tmp"); rm -f "$tmp"
  if [[ "$http_code" -ge 400 ]]; then
    err "$label failed (HTTP $http_code)"
    echo "  Response: $resp" >&2
    return 1
  fi
  echo "$resp"
}

# ─────────────────────────────────────────────────────────────────────────────
section "1/4 — Neon PostgreSQL"
# ─────────────────────────────────────────────────────────────────────────────

NEON_RESPONSE=$(api_post "Neon create project" \
  "https://console.neon.tech/api/v2/projects" \
  '{"project":{"name":"hireranker","pg_version":16,"region_id":"aws-us-east-2"}}' \
  -H "Authorization: Bearer $NEON_API_KEY" \
  -H "Content-Type: application/json")

NEON_PROJECT_ID=$(echo "$NEON_RESPONSE" | jq -r '.project.id')

# Neon returns the connection string in connection_uris[].connection_uri
# Extract host/db/user/password from the URI
NEON_URI=$(echo "$NEON_RESPONSE" | jq -r '.connection_uris[0].connection_uri // empty')
if [[ -z "$NEON_URI" || "$NEON_URI" == "null" ]]; then
  # Fallback: build from connection_parameters
  DB_HOST=$(echo "$NEON_RESPONSE" | jq -r '.connection_uris[0].connection_parameters.host')
  DB_NAME=$(echo "$NEON_RESPONSE" | jq -r '.connection_uris[0].connection_parameters.database')
  DB_USER=$(echo "$NEON_RESPONSE" | jq -r '.connection_uris[0].connection_parameters.user')
  DB_PASSWORD=$(echo "$NEON_RESPONSE" | jq -r '.connection_uris[0].connection_parameters.password')
else
  # Parse postgresql://user:pass@host/db
  DB_USER=$(echo "$NEON_URI"     | sed 's|postgresql://||' | cut -d: -f1)
  DB_PASSWORD=$(echo "$NEON_URI" | sed 's|postgresql://[^:]*:||' | cut -d@ -f1)
  DB_HOST=$(echo "$NEON_URI"     | cut -d@ -f2 | cut -d/ -f1 | cut -d: -f1)
  DB_NAME=$(echo "$NEON_URI"     | cut -d/ -f4 | cut -d? -f1)
fi
DB_PORT="5432"

info "Neon project: $NEON_PROJECT_ID"
info "DB: $DB_USER@$DB_HOST/$DB_NAME"

# ─────────────────────────────────────────────────────────────────────────────
section "2/4 — Upstash Redis"
# ─────────────────────────────────────────────────────────────────────────────

UPSTASH_RESPONSE=$(api_post "Upstash create Redis" \
  "https://api.upstash.com/v2/redis/database" \
  '{"name":"hireranker","region":"us-east-1","tls":true}' \
  -H "Authorization: Bearer $UPSTASH_API_KEY" \
  -H "Content-Type: application/json")

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

# Get Render owner ID (required for service creation)
RENDER_OWNER=$(api_get "Render owner" "https://api.render.com/v1/owners?limit=1" \
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
  '. + [{"key":"ALLOWED_HOSTS","value":"hireranker-api.onrender.com"},{"key":"WEB_CONCURRENCY","value":"2"},{"key":"CORS_ALLOWED_ORIGINS","value":"https://hireranker.vercel.app"}]')

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
      "buildCommand": "./build.sh",
      "envSpecificDetails": {"buildCommand": "./build.sh"},
      "healthCheckPath": "/api/health/",
      "numInstances": 1,
      "plan": "starter",
      "startCommand": "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120 --log-level info"
    },
    "type": "web_service",
    "envVars": $env
  }')

API_RESPONSE=$(api_post "Render web service" \
  "https://api.render.com/v1/services" \
  "$API_PAYLOAD" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json")

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
      "buildCommand": "pip install -r requirements.txt",
      "numInstances": 1,
      "plan": "starter",
      "startCommand": "celery -A celery_app worker -l info -Q resumes,evaluations,default --concurrency 1 --max-tasks-per-child 50"
    },
    "type": "background_worker",
    "envVars": $env
  }')

WORKER_RESPONSE=$(api_post "Render background worker" \
  "https://api.render.com/v1/services" \
  "$WORKER_PAYLOAD" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json")

WORKER_SERVICE_ID=$(echo "$WORKER_RESPONSE" | jq -r '.service.id // .id')
info "Render worker: $WORKER_SERVICE_ID"

# ─────────────────────────────────────────────────────────────────────────────
section "4/4 — Vercel (Next.js frontend)"
# ─────────────────────────────────────────────────────────────────────────────

VERCEL_USER=$(api_get "Vercel auth" "https://api.vercel.com/v2/user" \
  -H "Authorization: Bearer $VERCEL_API_KEY")
VERCEL_USERNAME=$(echo "$VERCEL_USER" | jq -r '.user.username')
info "Vercel user: $VERCEL_USERNAME"

VERCEL_PROJECT_PAYLOAD=$(jq -n \
  --arg repo "$GITHUB_REPO_OWNER/$GITHUB_REPO_NAME" \
  --arg apiurl "$API_URL" \
  '{
    "name": "hireranker",
    "framework": "nextjs",
    "gitRepository": {"type": "github", "repo": $repo},
    "rootDirectory": "frontend",
    "buildCommand": "npm run build",
    "outputDirectory": ".next",
    "installCommand": "npm install",
    "environmentVariables": [
      {"key":"NEXT_PUBLIC_API_URL","value":$apiurl,"type":"plain","target":["production","preview","development"]},
      {"key":"NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY","value":"","type":"plain","target":["production","preview","development"]}
    ]
  }')

VERCEL_PROJECT=$(api_post "Vercel project" \
  "https://api.vercel.com/v9/projects" \
  "$VERCEL_PROJECT_PAYLOAD" \
  -H "Authorization: Bearer $VERCEL_API_KEY" \
  -H "Content-Type: application/json")

VERCEL_PROJECT_ID=$(echo "$VERCEL_PROJECT" | jq -r '.id')
VERCEL_URL="https://${VERCEL_USERNAME}-hireranker.vercel.app"
info "Vercel project: $VERCEL_PROJECT_ID"

# Trigger deployment
DEPLOY_PAYLOAD=$(jq -n \
  --arg repo "$GITHUB_REPO_OWNER/$GITHUB_REPO_NAME" \
  --arg branch "$GITHUB_BRANCH" \
  --arg pid "$VERCEL_PROJECT_ID" \
  '{"name":"hireranker","gitSource":{"type":"github","repo":$repo,"ref":$branch},"projectId":$pid,"target":"production"}')

api_post "Vercel deploy" \
  "https://api.vercel.com/v13/deployments" \
  "$DEPLOY_PAYLOAD" \
  -H "Authorization: Bearer $VERCEL_API_KEY" \
  -H "Content-Type: application/json" > /dev/null

info "Vercel deployment triggered  →  $VERCEL_URL"

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
