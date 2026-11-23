#!/usr/bin/env bash
set -e

# Change to root directory
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "========================================================"
echo "   Starting TRACK - EOS Management System Locally"
echo "========================================================"

# Create pids directory for clean shutdown tracking
mkdir -p "$ROOT_DIR/.run"

# 1. Start PostgreSQL via Docker Compose
echo ""
echo "==> [1/4] Starting PostgreSQL database container..."
docker compose -f docker-compose.db.yml up -d

echo "==> Waiting for PostgreSQL to be healthy..."
until docker compose -f docker-compose.db.yml exec -T db pg_isready -U postgres -d track_db > /dev/null 2>&1; do
    sleep 1
done
echo "==> PostgreSQL is ready on port 5432."

# 2. Run Database Migrations
echo ""
echo "==> [2/4] Applying database migrations..."
if [ -d "$ROOT_DIR/backend/.venv" ]; then
    source "$ROOT_DIR/backend/.venv/bin/activate"
fi

cd "$ROOT_DIR/backend"
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
fi

alembic upgrade head
echo "==> Migrations applied successfully."

# 3. Start Backend (FastAPI) in Background
echo ""
echo "==> [3/4] Starting Backend (FastAPI) on port 8000..."
cd "$ROOT_DIR/backend"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --quiet -r requirements.txt

# Run backend in background and save PID
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "$ROOT_DIR/.run/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$ROOT_DIR/.run/backend.pid"
echo "==> Backend started (PID: $BACKEND_PID, logs: .run/backend.log)"

# 4. Start Frontend (Next.js) in Background
echo ""
echo "==> [4/4] Starting Frontend (Next.js) on port 3000..."
cd "$ROOT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    echo "==> Installing frontend dependencies..."
    npm install --quiet
fi
if [ ! -f ".env.local" ] && [ -f ".env.example" ]; then
    cp .env.example .env.local
fi

nohup npm run dev > "$ROOT_DIR/.run/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$ROOT_DIR/.run/frontend.pid"
echo "==> Frontend started (PID: $FRONTEND_PID, logs: .run/frontend.log)"

echo ""
echo "========================================================"
echo "   TRACK is now running!"
echo "   - Frontend UI:  http://localhost:3000"
echo "   - Backend API:  http://localhost:8000"
echo "   - API Docs:     http://localhost:8000/docs"
echo "   - Database:     localhost:5432 (track_db)"
echo ""
echo "   To stop everything, run: ./scripts/stop_all.sh"
echo "========================================================"
