#!/usr/bin/env bash

# Change to root directory
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "========================================================"
echo "   Stopping TRACK - EOS Management System Locally"
echo "========================================================"

# 1. Stop Frontend
if [ -f "$ROOT_DIR/.run/frontend.pid" ]; then
    PID=$(cat "$ROOT_DIR/.run/frontend.pid")
    echo "==> Stopping Frontend process (PID: $PID)..."
    kill "$PID" 2>/dev/null || true
    # Also kill any node processes running next dev on port 3000
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    rm -f "$ROOT_DIR/.run/frontend.pid"
else
    # Fallback to kill by port if PID file is missing
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
fi
echo "==> Frontend stopped."

# 2. Stop Backend
if [ -f "$ROOT_DIR/.run/backend.pid" ]; then
    PID=$(cat "$ROOT_DIR/.run/backend.pid")
    echo "==> Stopping Backend process (PID: $PID)..."
    kill "$PID" 2>/dev/null || true
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    rm -f "$ROOT_DIR/.run/backend.pid"
else
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
fi
echo "==> Backend stopped."

# 3. Stop PostgreSQL Docker Container
echo "==> Stopping PostgreSQL Docker container..."
docker compose -f docker-compose.db.yml down
echo "==> PostgreSQL stopped."

echo ""
echo "========================================================"
echo "   All TRACK services have been stopped."
echo "========================================================"
