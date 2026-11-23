#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "==> Downgrading all migrations to base..."
alembic downgrade base

echo "==> Re-applying migrations to head..."
alembic upgrade head

echo "==> Database schema has been cleanly reset!"
