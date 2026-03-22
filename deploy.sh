#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# HireRanker — Full deployment script
# Provisions: Neon DB, Upstash Redis, Render (API + Worker), Vercel (Frontend)
#
# Usage:
#   chmod +x deploy.sh
#   export NEON_API_KEY="napi_..."
#   export UPSTASH_API_KEY="..."
#   export RENDER_API_KEY="rnd_..."
#   export VERCEL_API_KEY="vck_..."
#   export ANTHROPIC_API_KEY="sk-ant-..."
#   ./deploy.sh
#
# Requirements: curl, jq (brew install jq / apt install jq)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Validate required env vars ───────────────────────────────────────────────
: "${NEON_API_KEY:?'Set NEON_API_KEY'}"
: "${UPSTASH_API_KEY:?'Set UPSTASH_API_KEY'}"
: "${RENDER_API_KEY:?'Set RENDER_API_KEY'}"
: "${VERCEL_API_KEY:?'Set VERCEL_API_KEY'}"
: "${ANTHROPIC_API_KEY:?'Set ANTHROPIC_API_KEY'}"

# ── GitHub repo (update if different) ────────────────────────────────────────
GITHUB_REPO_OWNER="${GITHUB_REPO_OWNER:-SarswaManish}"
GITHUB_REPO_NAME="${GITHUB_REPO_NAME:-hireranker}"
GITHUB_BRANCH="${GITHUB_BRANCH:-main}"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}[✓]${NC} $*"; }
warn()    { echo -e "${YELLOW}[!]${NC} $*"; }
section() { echo -e "\n${YELLOW}══════════════════════════════════════${NC}"; echo -e "${YELLOW} $*${NC}"; echo -e "${YELLOW}══════════════════════════════════════${NC}"; }

# ─────────────────────────────────────────────────────────────────────────────
section "1/4 — Neon PostgreSQL"
# ─────────────────────────────────────────────────────────────────────────────

NEON_RESPONSE=$(curl -sf -X POST https://console.neon.tech/api/v2/projects \
  -H "Authorization: Bearer $NEON_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "project": {
      "name": "hireranker",
      "pg_version": 16,
      "region_id": "aws-us-east-2"
    }
  }')

NEON_PROJECT_ID=$(echo "$NEON_RESPONSE" | jq -r '.project.id')
DB_HOST=$(echo "$NEON_RESPONSE"         | jq -r '.connection_uris[0].connection_parameters.host')
DB_NAME=$(echo "$NEON_RESPONSE"         | jq -r '.connection_uris[0].connection_parameters.database')
DB_USER=$(echo "$NEON_RESPONSE"         | jq -r '.connection_uris[0].connection_parameters.user')
DB_PASSWORD=$(echo "$NEON_RESPONSE"     | jq -r '.connection_uris[0].connection_parameters.password')
DB_PORT="5432"

info "Neon project created: $NEON_PROJECT_ID"
info "DB: $DB_USER@$DB_HOST/$DB_NAME"

# ─────────────────────────────────────────────────────────────────────────────
section "2/4 — Upstash Redis"
# ─────────────────────────────────────────────────────────────────────────────

UPSTASH_RESPONSE=$(curl -sf -X POST https://api.upstash.com/v2/redis/database \
  -H "Authorization: Bearer $UPSTASH_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hireranker",
    "region": "us-east-1",
    "tls": true
  }')

REDIS_ENDPOINT=$(echo "$UPSTASH_RESPONSE" | jq -r '.endpoint')
REDIS_PORT=$(echo "$UPSTASH_RESPONSE"     | jq -r '.port')
REDIS_PASSWORD=$(echo "$UPSTASH_RESPONSE" | jq -r '.password')

REDIS_URL="rediss://default:${REDIS_PASSWORD}@${REDIS_ENDPOINT}:${REDIS_PORT}"
CELERY_BROKER_URL="${REDIS_URL}/1"
CELERY_RESULT_BACKEND="${REDIS_URL}/2"

info "Upstash Redis: $REDIS_ENDPOINT"

# ─────────────────────────────────────────────────────────────────────────────
section "3/4 — Render (API web service + Celery worker)"
# ─────────────────────────────────────────────────────────────────────────────

warn "GitHub repo: github.com/$GITHUB_REPO_OWNER/$GITHUB_REPO_NAME  branch: $GITHUB_BRANCH"

# Common env vars shared by both services
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

# Web service env (adds ALLOWED_HOSTS, CORS, WEB_CONCURRENCY)
API_ENV=$(echo "$COMMON_ENV" | jq \
  '. + [
    {"key":"ALLOWED_HOSTS","value":"hireranker-api.onrender.com"},
    {"key":"WEB_CONCURRENCY","value":"2"},
    {"key":"CORS_ALLOWED_ORIGINS","value":"https://hireranker.vercel.app"}
  ]')

API_PAYLOAD=$(jq -n \
  --arg repo "https://github.com/$GITHUB_REPO_OWNER/$GITHUB_REPO_NAME" \
  --arg branch "$GITHUB_BRANCH" \
  --argjson env "$API_ENV" \
  '{
    "type": "web_service",
    "name": "hireranker-api",
    "repo": $repo,
    "branch": $branch,
    "rootDir": "backend",
    "buildCommand": "./build.sh",
    "startCommand": "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120 --log-level info",
    "healthCheckPath": "/api/health/",
    "envVars": $env,
    "autoDeploy": true,
    "plan": "starter"
  }')

API_RESPONSE=$(curl -sf -X POST https://api.render.com/v1/services \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$API_PAYLOAD")

API_SERVICE_ID=$(echo "$API_RESPONSE" | jq -r '.service.id // .id')
API_URL="https://hireranker-api.onrender.com"
info "Render API service: $API_SERVICE_ID  →  $API_URL"

WORKER_PAYLOAD=$(jq -n \
  --arg repo "https://github.com/$GITHUB_REPO_OWNER/$GITHUB_REPO_NAME" \
  --arg branch "$GITHUB_BRANCH" \
  --argjson env "$COMMON_ENV" \
  '{
    "type": "background_worker",
    "name": "hireranker-worker",
    "repo": $repo,
    "branch": $branch,
    "rootDir": "backend",
    "buildCommand": "pip install -r requirements.txt",
    "startCommand": "celery -A celery_app worker -l info -Q resumes,evaluations,default --concurrency 1 --max-tasks-per-child 50",
    "envVars": $env,
    "autoDeploy": true,
    "plan": "starter"
  }')

WORKER_RESPONSE=$(curl -sf -X POST https://api.render.com/v1/services \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$WORKER_PAYLOAD")

WORKER_SERVICE_ID=$(echo "$WORKER_RESPONSE" | jq -r '.service.id // .id')
info "Render worker: $WORKER_SERVICE_ID"

# ─────────────────────────────────────────────────────────────────────────────
section "4/4 — Vercel (Next.js frontend)"
# ─────────────────────────────────────────────────────────────────────────────

VERCEL_USER=$(curl -sf https://api.vercel.com/v2/user \
  -H "Authorization: Bearer $VERCEL_API_KEY")
info "Vercel user: $(echo "$VERCEL_USER" | jq -r '.user.username')"

VERCEL_PROJECT=$(curl -sf -X POST "https://api.vercel.com/v9/projects" \
  -H "Authorization: Bearer $VERCEL_API_KEY" \
  -H "Content-Type: application/json" \
  --data-binary "$(jq -n \
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
        {"key":"NEXT_PUBLIC_API_URL","value":$apiurl,"type":"plain","target":["production","preview"]},
        {"key":"NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY","value":"","type":"plain","target":["production","preview"]}
      ]
    }')")

VERCEL_PROJECT_ID=$(echo "$VERCEL_PROJECT" | jq -r '.id')
VERCEL_URL="https://hireranker.vercel.app"
info "Vercel project: $VERCEL_PROJECT_ID  →  $VERCEL_URL"

# Trigger initial deployment
curl -sf -X POST "https://api.vercel.com/v13/deployments" \
  -H "Authorization: Bearer $VERCEL_API_KEY" \
  -H "Content-Type: application/json" \
  --data-binary "$(jq -n \
    --arg name "hireranker" \
    --arg repo "$GITHUB_REPO_OWNER/$GITHUB_REPO_NAME" \
    --arg branch "$GITHUB_BRANCH" \
    --arg pid "$VERCEL_PROJECT_ID" \
    '{
      "name": $name,
      "gitSource": {"type":"github","repo":$repo,"ref":$branch},
      "projectId": $pid,
      "target": "production"
    }')" > /dev/null

info "Vercel deployment triggered"

# ─────────────────────────────────────────────────────────────────────────────
section "Done — Deployment Summary"
# ─────────────────────────────────────────────────────────────────────────────

cat <<SUMMARY

  Backend API:  $API_URL
  Frontend:     $VERCEL_URL
  Neon DB:      $DB_HOST / $DB_NAME
  Redis:        $REDIS_ENDPOINT

  ⚠  First deploy takes ~5 min on Render (free tier).
     Monitor build logs at https://dashboard.render.com

SUMMARY
