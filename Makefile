.PHONY: help dev dev-build dev-down dev-clean prod-build prod-up prod-down \
        migrate makemigrations seed shell test test-coverage lint fmt \
        logs logs-backend logs-celery install-dev create-superuser \
        collectstatic prod-migrate prod-createsuperuser prod-logs

# Default target
help:
	@echo ""
	@echo "HireRanker Development Commands"
	@echo "================================"
	@echo ""
	@echo "  Development:"
	@echo "    make dev              Start development environment (attached)"
	@echo "    make dev-build        Build and start development environment"
	@echo "    make dev-down         Stop development environment"
	@echo "    make dev-clean        Stop and remove all volumes (WARNING: deletes data)"
	@echo ""
	@echo "  Database:"
	@echo "    make migrate          Run database migrations"
	@echo "    make makemigrations   Create new migrations"
	@echo "    make seed             Seed database with sample data"
	@echo ""
	@echo "  Testing:"
	@echo "    make test             Run all tests"
	@echo "    make test-coverage    Run tests with coverage report"
	@echo ""
	@echo "  Code Quality:"
	@echo "    make lint             Run linters (ruff, eslint)"
	@echo "    make fmt              Auto-format code (ruff, prettier)"
	@echo ""
	@echo "  Utilities:"
	@echo "    make shell            Open Django shell"
	@echo "    make logs             Tail all logs"
	@echo "    make logs-backend     Tail backend logs only"
	@echo "    make logs-celery      Tail celery worker logs only"
	@echo "    make create-superuser Create Django superuser"
	@echo "    make collectstatic    Collect static files"
	@echo "    make install-dev      Install deps locally (outside Docker)"
	@echo ""
	@echo "  Production:"
	@echo "    make prod-build       Build production images"
	@echo "    make prod-up          Start production environment (detached)"
	@echo "    make prod-down        Stop production environment"
	@echo "    make prod-logs        Tail production logs"
	@echo "    make prod-migrate     Run migrations in production"
	@echo "    make prod-createsuperuser  Create superuser in production"
	@echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Development
# ─────────────────────────────────────────────────────────────────────────────

dev:
	docker-compose up

dev-build:
	docker-compose up --build

dev-down:
	docker-compose down

dev-clean:
	@echo "WARNING: This will delete all volumes including the database!"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	docker-compose down -v

# ─────────────────────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────────────────────

migrate:
	docker-compose exec backend python manage.py migrate

makemigrations:
	docker-compose exec backend python manage.py makemigrations

seed:
	docker-compose exec backend python manage.py seed_data

# ─────────────────────────────────────────────────────────────────────────────
# Testing
# ─────────────────────────────────────────────────────────────────────────────

test:
	docker-compose exec backend python manage.py test apps --verbosity=2

test-coverage:
	docker-compose exec backend coverage run manage.py test apps
	docker-compose exec backend coverage report --show-missing
	docker-compose exec backend coverage html
	@echo "HTML coverage report written to backend/htmlcov/index.html"

# ─────────────────────────────────────────────────────────────────────────────
# Code Quality
# ─────────────────────────────────────────────────────────────────────────────

lint:
	@echo "--- Python (ruff) ---"
	docker-compose exec backend ruff check .
	@echo "--- Frontend (eslint) ---"
	docker-compose exec frontend npm run lint

fmt:
	@echo "--- Python (ruff format) ---"
	docker-compose exec backend ruff format .
	@echo "--- Frontend (prettier) ---"
	docker-compose exec frontend npm run format

# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────

shell:
	docker-compose exec backend python manage.py shell

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-celery:
	docker-compose logs -f celery_worker

create-superuser:
	docker-compose exec backend python manage.py createsuperuser

collectstatic:
	docker-compose exec backend python manage.py collectstatic --noinput

install-dev:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# ─────────────────────────────────────────────────────────────────────────────
# Production
# ─────────────────────────────────────────────────────────────────────────────

prod-build:
	docker-compose -f docker-compose.prod.yml build

prod-up:
	docker-compose -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.prod.yml down

prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f

prod-migrate:
	docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

prod-createsuperuser:
	docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
