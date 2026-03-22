# HireRanker

AI-powered candidate ranking and evaluation platform for engineering teams.
Upload your job description, import candidates via CSV or resume upload, and
get structured LLM-driven scores, summaries, and shortlists in minutes.

---

## Features

- **Bulk CSV import** — paste a spreadsheet of candidates and have them all
  evaluated in one click
- **Resume parsing** — upload PDF or DOCX resumes; extracted text is fed
  directly to the evaluator
- **LLM evaluation** — each candidate is scored 0-100 against your JD with
  strengths, weaknesses, and a hiring recommendation
- **Multi-project** — manage multiple open roles with separate candidate pools
- **Shortlisting** — mark candidates as shortlisted/rejected and export
- **CSV/JSON/PDF export** — share ranked shortlists with your team
- **Public review page** — optional paid link ($9.99) candidates can use to
  get detailed feedback on their application
- **Async processing** — all LLM calls run via Celery workers so the UI
  stays responsive for bulk imports
- **Team access** — invite colleagues to your organization

---

## Tech Stack

| Layer       | Technology                                       |
|-------------|--------------------------------------------------|
| Backend     | Python 3.11, Django 4.2, Django REST Framework   |
| Task queue  | Celery 5, Redis 7                                |
| Database    | PostgreSQL 15                                    |
| Frontend    | Next.js 14 (App Router), TypeScript, Tailwind    |
| LLM         | OpenAI GPT-4o / GPT-4o-mini (configurable)       |
| Payments    | Stripe Checkout                                  |
| File storage| Local (dev) / AWS S3 or Cloudflare R2 (prod)     |
| Reverse proxy| Nginx 1.25                                      |
| Containers  | Docker, Docker Compose                           |

---

## Quick Start

Get HireRanker running locally in five commands:

```bash
git clone https://github.com/your-org/hireranker.git
cd hireranker
cp .env.example .env           # fill in OPENAI_API_KEY at minimum
make dev-build                  # builds images and starts all services
make migrate                    # runs database migrations
```

Then open http://localhost:3000 in your browser.

The Django admin is at http://localhost:8000/admin/.
Create your first superuser with:

```bash
make create-superuser
```

To load sample data:

```bash
make seed
```

---

## Architecture Overview

```
Browser / API Client
        |
      Nginx (80/443)
        |
   ┌────┴────┐
   │         │
Frontend  Django API
(Next.js)  (Gunicorn)
              │
        ┌─────┼─────┐
        │     │     │
     Postgres Redis  S3/local
              │
        Celery Workers
        (resume parsing,
         LLM evaluation)
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for a full system walkthrough.

---

## Development Guide

### Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose v2)
- An OpenAI API key

### Environment

Copy `.env.example` to `.env` and set at minimum:

```bash
OPENAI_API_KEY=sk-...
```

All other values have sensible defaults for local development (dev passwords,
DEBUG=True, local file storage, etc.).

### Common commands

```bash
make dev              # start all services
make dev-down         # stop
make migrate          # run migrations
make makemigrations   # create new migrations
make test             # run test suite
make test-coverage    # tests + coverage report
make lint             # ruff + eslint
make shell            # Django shell
make logs             # tail all logs
make logs-backend     # tail backend only
```

### Running tests

```bash
make test
# or for a specific app:
docker-compose exec backend python manage.py test apps.evaluations --verbosity=2
```

### Adding a new Django app

```bash
docker-compose exec backend python manage.py startapp myapp apps/myapp
```

### Frontend development

The frontend dev server supports hot module replacement. It runs on
http://localhost:3000 and proxies API calls to the Django backend at
http://localhost:8000.

```bash
docker-compose logs -f frontend   # watch Next.js output
```

---

## Environment Variables Reference

See [.env.example](./.env.example) for the full annotated list.

Key variables:

| Variable                  | Description                                   |
|---------------------------|-----------------------------------------------|
| `SECRET_KEY`              | Django secret key (generate with openssl)     |
| `DATABASE_URL`            | PostgreSQL connection string                  |
| `REDIS_URL`               | Redis connection string                       |
| `OPENAI_API_KEY`          | OpenAI API key                                |
| `OPENAI_EVALUATION_MODEL` | Model used for evaluation (default: gpt-4o)   |
| `STRIPE_SECRET_KEY`       | Stripe secret key                             |
| `STRIPE_WEBHOOK_SECRET`   | Stripe webhook signing secret                 |
| `USE_S3`                  | Set True to use S3/R2 for file storage        |

---

## API Documentation

Full REST API reference: [docs/API_REFERENCE.md](./docs/API_REFERENCE.md)

The Django API is served at `/api/`. Interactive docs (if enabled in dev):
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

---

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for a complete guide to deploying on a
Ubuntu 22.04 VPS with Docker, Nginx, and Let's Encrypt SSL.

---

## Prompt Templates

All LLM prompt templates are documented in [docs/PROMPTS.md](./docs/PROMPTS.md).

---

## Project Structure

```
hireranker/
├── backend/
│   ├── apps/
│   │   ├── accounts/       # User & organization management
│   │   ├── candidates/     # Candidate model, resume parsing
│   │   ├── evaluations/    # LLM evaluation logic
│   │   ├── projects/       # Job opening / project management
│   │   └── reviews/        # Public paid review feature
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── tasks/              # Celery task definitions
│   ├── core/               # Shared utilities, base models
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── app/                # Next.js App Router pages
│   ├── components/         # Reusable UI components
│   ├── hooks/              # Custom React hooks
│   ├── lib/                # API client, utilities
│   ├── store/              # State management
│   └── types/              # TypeScript types
├── nginx/
│   ├── nginx.conf          # Production Nginx config
│   └── nginx.dev.conf      # Development Nginx config
├── data/
│   ├── sample_candidates.csv
│   └── sample_jd.txt
├── docs/
│   ├── API_REFERENCE.md
│   └── PROMPTS.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
├── .env.example
├── README.md
├── DEPLOYMENT.md
└── ARCHITECTURE.md
```

---

## Contributing

1. Fork the repository and create a feature branch.
2. Run `make lint` before opening a PR.
3. Write tests for new functionality (`make test-coverage` should not drop below 80%).
4. Open a PR against `main` with a clear description of what changed and why.

---

## License

MIT License. See `LICENSE` for details.
