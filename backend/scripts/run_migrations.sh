#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "==> Running Alembic migrations to apply latest schema..."
alembic upgrade head
echo "==> Migrations applied successfully."
