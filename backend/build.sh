#!/usr/bin/env bash
# Render build script for hireranker-api
set -o errexit

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Creating migration files..."
python manage.py makemigrations --noinput

echo "==> Running database migrations..."
python manage.py migrate --noinput

echo "==> Build complete."
