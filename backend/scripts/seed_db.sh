#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "==> Running database seeder (seed.json)..."
python -m app.db.seed "$@"
echo "==> Seeding finished."
