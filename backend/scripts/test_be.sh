#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "==> Running Backend Tests..."
pytest -v tests/
