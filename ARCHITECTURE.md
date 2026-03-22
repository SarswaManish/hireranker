# HireRanker Architecture

## System Overview

```
                          ┌──────────────────────────────────────────┐
                          │              Browser / API Client         │
                          └───────────────────┬──────────────────────┘
                                              │ HTTPS (443)
                          ┌───────────────────▼──────────────────────┐
                          │                  Nginx                    │
                          │         (reverse proxy + SSL termination)  │
                          │    rate limiting │ gzip │ static serving  │
                          └──────┬───────────────────────┬───────────┘
                                 │ /api/* /admin/*        │ /* (frontend)
                  ┌──────────────▼──────────┐  ┌─────────▼──────────┐
                  │     Django / Gunicorn    │  │  Next.js (Node.js)  │
                  │       (backend:8000)     │  │   (frontend:3000)   │
                  └──────────┬──────────────┘  └────────────────────┘
                             │
           ┌─────────────────┼─────────────────────┐
           │                 │                       │
  ┌────────▼───────┐  ┌──────▼──────┐  ┌───────────▼────────┐
  │  PostgreSQL 15  │  │   Redis 7   │  │  S3 / Local Storage │
  │   (postgres:   │  │  (redis:    │  │  (resume files,     │
  │    5432)       │  │   6379)     │  │   static assets)    │
  └────────────────┘  └──────┬──────┘  └────────────────────┘
                             │ Broker + Result Backend
           ┌─────────────────┼──────────────────────┐
           │                 │                        │
  ┌────────▼──────┐  ┌───────▼────────┐  ┌──────────▼───────┐
  │ Celery Worker  │  │ Celery Worker  │  │  Celery Beat      │
  │ (resumes +     │  │ (evaluations + │  │  (periodic tasks  │
  │  default Q)    │  │  default Q)    │  │   scheduler)      │
  └───────┬────────┘  └───────┬────────┘  └──────────────────┘
          │                   │
          └─────────┬─────────┘
                    │
         ┌──────────▼──────────┐
         │    OpenAI API        │
         │  (GPT-4o / 4o-mini) │
         └─────────────────────┘
```

---

## Component Descriptions

### Nginx (Reverse Proxy)

- Terminates SSL using Let's Encrypt certificates.
- Routes `/api/*` and `/admin/*` to the Django backend.
- Routes all other traffic to the Next.js frontend.
- Serves Django's collected static files (`/static/`) and uploaded media
  (`/media/`) directly from volumes — bypassing Python for static content.
- Applies rate limiting zones:
  - `/api/review/` — 10 req/hour per IP (public endpoint, prevents abuse)
  - `/api/auth/` — 10 req/minute per IP (brute-force protection)
  - All other `/api/` — 60 req/minute per IP
- Enforces `client_max_body_size 50m` for resume uploads.
- Adds security headers: HSTS, X-Frame-Options, CSP, etc.

### Django Backend

Organized into Django apps under `backend/apps/`:

| App           | Responsibility                                              |
|---------------|-------------------------------------------------------------|
| `accounts`    | User registration, login, JWT auth, org membership          |
| `projects`    | Job opening CRUD, JD storage, project stats                 |
| `candidates`  | Candidate model, CSV import, resume upload, field normalize |
| `evaluations` | LLM evaluation orchestration, score storage, comparison     |
| `reviews`     | Public review page, Stripe Checkout integration             |

The `core/` package contains:
- `base_models.py` — abstract UUID + timestamp base model
- `llm_client.py` — OpenAI client wrapper with retry logic and token counting
- `storage.py` — unified file storage abstraction (local vs. S3)
- `permissions.py` — DRF custom permission classes

### Celery Workers

Two worker processes run by default in production (configurable via Docker
Compose `deploy.replicas`). Three task queues:

| Queue         | Tasks                                                        |
|---------------|--------------------------------------------------------------|
| `default`     | General tasks: email sending, export generation              |
| `resumes`     | PDF/DOCX parsing, bulk zip extraction, skills normalization  |
| `evaluations` | LLM evaluation calls, re-evaluation, candidate comparison    |

All workers share the same codebase and Dockerfile; the queue is determined
by the `--queues` flag passed at startup.

### Celery Beat

Runs scheduled tasks using `django_celery_beat` with a database scheduler:
- Nightly cleanup of expired Stripe checkout sessions
- Weekly aggregate statistics computation per project
- Daily health-check ping to Sentry

### PostgreSQL

Single primary database. Key tables:

| Table                  | Description                                       |
|------------------------|---------------------------------------------------|
| `accounts_user`        | User accounts                                     |
| `accounts_organization`| Tenant/org (multi-tenant via FK, not schema)      |
| `projects_project`     | Job openings                                      |
| `candidates_candidate` | Candidate profiles                                |
| `evaluations_evaluation`| LLM evaluation results per candidate             |
| `reviews_publicreview` | Paid public review records                        |
| `django_celery_beat_*` | Celery Beat periodic task schedules               |

All models extend a `BaseModel` with `id` (UUID4), `created_at`, `updated_at`.

### Redis

Serves two roles:
1. **Celery broker** — task queue backend (`/0`)
2. **Django cache** — API response caching, rate limit counters (`/1`)

Configured with `maxmemory 512mb` and `allkeys-lru` eviction policy in
production so it never runs out of memory under sustained load.

### Next.js Frontend

Built with the App Router (Next.js 14). Key routes:

| Route                          | Description                                  |
|-------------------------------|----------------------------------------------|
| `/`                           | Marketing landing page                       |
| `/login`, `/register`         | Auth pages                                   |
| `/dashboard`                  | Project list                                 |
| `/projects/[id]`              | Project detail + candidate table             |
| `/projects/[id]/import`       | CSV / resume import wizard                   |
| `/projects/[id]/candidates/[id]` | Candidate detail + evaluation              |
| `/review/[slug]`              | Public review landing page                   |
| `/review/[slug]/success`      | Post-payment review result page              |

State management uses Zustand for client state and React Query (TanStack Query)
for server state / caching.

---

## Data Flow

### 1. CSV Import Flow

```
User uploads CSV
      │
  [POST /api/projects/{id}/candidates/import/csv/]
      │
  Django validates file, reads rows, creates stub Candidate records
      │
  Returns task_id (202 Accepted)
      │
  Celery task: `process_csv_import`
    ├── For each row: normalize skills via LLM (Template 6)
    ├── Save parsed candidate to DB
    └── Enqueue individual evaluation tasks
      │
  Celery task: `evaluate_candidate` (per candidate)
    ├── Build prompt from JD + candidate profile
    ├── Call OpenAI API (Template 1)
    ├── Parse JSON response
    └── Save Evaluation record to DB
      │
  Frontend polls GET /api/tasks/{task_id}/status/ every 2s
  until status=SUCCESS
```

### 2. Resume Upload Flow

```
User uploads PDF/DOCX
      │
  [POST /api/projects/{id}/candidates/import/resume/]
      │
  Django saves file to storage (local/S3), creates Candidate stub
      │
  Celery task: `parse_resume`
    ├── Extract raw text (pdfminer for PDF, python-docx for DOCX)
    ├── Call LLM to extract structured fields (Template 2)
    └── Update Candidate record with parsed data
      │
  Celery task: `evaluate_candidate`
    └── (same as CSV import flow above)
```

### 3. Public Review Flow (Paid)

```
Candidate visits /review/{slug}
      │
  [GET /api/review/{slug}/] — loads JD summary
      │
  Candidate fills form and submits
      │
  [POST /api/review/{slug}/checkout/] — creates Stripe Checkout session
      │
  Candidate redirected to Stripe hosted checkout page
      │
  Stripe charges $9.99, sends webhook event
      │
  [POST /api/webhooks/stripe/] — Django receives signed webhook
    ├── Validates Stripe signature
    ├── Creates PublicReview record
    └── Enqueues `generate_public_review` Celery task
      │
  Celery task: `generate_public_review`
    ├── Calls LLM with detailed review prompt (Template 5)
    └── Saves result to PublicReview record
      │
  Candidate's success_url includes review_token
  [GET /api/review/{slug}/result/{token}/] — returns review JSON
```

---

## LLM Evaluation Pipeline

```
evaluate_candidate(candidate_id, project_id)
           │
  Load Candidate + Project from DB
           │
  Build context dict:
    - job_description (from Project)
    - name, email, location (from Candidate)
    - college, degree, graduation_year, cgpa
    - skills (normalized list)
    - github, linkedin, notes
    - resume_text (if available, truncated to 8000 chars)
           │
  Render system prompt + user message from Template 1
           │
  Call OpenAI (with retry: 3 attempts, exponential backoff)
           │
  Parse JSON response
    - Validate score is integer 0-100
    - Validate required fields present
    - Fallback to partial save on parse error
           │
  Save Evaluation:
    score, summary, strengths, weaknesses,
    skill_match, experience_score, education_score,
    recommendation, model_used, prompt_version,
    raw_response (for audit), tokens_used
           │
  Update Candidate.status = "evaluated"
           │
  Trigger WebSocket push (if connected) to refresh UI
```

---

## Scoring Framework

The final `score` (0-100) is determined entirely by the LLM based on the
rubric in the system prompt. The model also returns component scores:

| Component            | Weight (informational) | Description                    |
|----------------------|------------------------|--------------------------------|
| `skill_match`        | ~40%                   | % of required skills matched   |
| `experience_score`   | ~35%                   | Depth and relevance of XP      |
| `education_score`    | ~15%                   | Degree, school, GPA relevance  |
| Soft factors         | ~10%                   | Portfolio, notes, domain fit   |

These are informational — the LLM produces the holistic `score` directly, not
as a weighted sum. The component fields are used for display and filtering.

**Recommendation tiers:**
- `STRONG_YES` (90-100) — advance immediately
- `YES` (75-89) — recommend for phone screen
- `MAYBE` (60-74) — worth considering; review manually
- `NO` (<60) — does not meet minimum requirements

---

## Security Design

### Authentication
- JWT access tokens (60 min TTL) + refresh tokens (7 days TTL)
- Refresh token rotation + blacklisting on logout
- bcrypt password hashing (Django default)

### Multi-tenancy
- All resources (projects, candidates) are scoped to an `Organization`
- DRF permission class `IsOrganizationMember` enforces row-level isolation
- No cross-organization data leakage by construction (all queries filtered)

### File Uploads
- File type validated by magic bytes (python-magic), not just extension
- Max file size enforced at Nginx (50 MB) and Django application layer (10 MB)
- Uploaded files stored outside the web root; served via `/media/` path
- S3-stored files use private ACL; presigned URLs for downloads

### Rate Limiting
- Nginx-level: per-IP rate limits on sensitive endpoints
- Django-level: `django-ratelimit` on the review checkout endpoint
- Stripe webhook endpoint verified by signature (`STRIPE_WEBHOOK_SECRET`)

### Production Hardening
- Non-root Docker users (`appuser`, `nextjs`)
- `server_tokens off` in Nginx (hides version)
- Django `DEBUG=False` in production
- `SECURE_SSL_REDIRECT`, `HSTS`, `SECURE_BROWSER_XSS_FILTER` enabled
- Sentry for exception tracking
- No credentials in environment variables committed to git

---

## Future Scaling Considerations

### Horizontal Scaling

The application is stateless at the Django and Celery layer. To scale:

1. **Backend**: Run multiple Gunicorn containers behind Nginx upstream. Add
   more `backend` replicas in Docker Compose or Kubernetes.
2. **Celery workers**: Increase `deploy.replicas` in `docker-compose.prod.yml`.
   Separate worker pools per queue for independent scaling.
3. **Database**: Add read replicas for analytics queries. Consider PgBouncer
   for connection pooling under high concurrency.
4. **Redis**: Use Redis Cluster or AWS ElastiCache for HA.
5. **File Storage**: Already abstracted — switch `USE_S3=True` to move uploads
   off the server disk.

### LLM Cost Optimization

- Cache evaluation results; re-evaluate only when the JD or candidate profile
  changes.
- Use `gpt-4o-mini` for extraction/normalization tasks (Templates 2, 3, 6)
  and `gpt-4o` only for evaluation and comparison (Templates 1, 4, 5).
- Implement a token budget per evaluation to avoid runaway costs on large
  resumes.
- Consider a local model (Ollama + Llama 3) for development to eliminate API
  costs during testing.

### Kubernetes Migration

The Docker Compose setup maps directly to Kubernetes:
- Services → Deployments + Services
- Volumes → PersistentVolumeClaims
- Secrets → Kubernetes Secrets (sealed or Vault-backed)
- `celery_beat` → CronJob or a single-replica Deployment with leader election
