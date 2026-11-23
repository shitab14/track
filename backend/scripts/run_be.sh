#!/usr/bin/env bash
set -e

# Move to backend directory
cd "$(dirname "$0")/.."

echo "==> Starting Track Backend Service..."

# Check Python environment
if [ ! -d ".venv" ]; then
    echo "==> Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
echo "==> Installing / Updating dependencies..."
pip install --quiet -r requirements.txt

# Load environment defaults if .env does not exist
if [ ! -f ".env" ]; then
    echo "==> Generating default .env from .env.example..."
    cp .env.example .env
fi

echo "==> Running Uvicorn server on http://localhost:8000..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
