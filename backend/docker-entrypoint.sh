#!/usr/bin/env bash
# Backend container start (ADR0014): apply migrations, seed idempotently, serve.
set -e

echo "==> Applying database migrations (alembic upgrade head)..."
alembic upgrade head

echo "==> Seeding database from seed.json (idempotent)..."
python -m app.db.seed

echo "==> Starting API on :8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
