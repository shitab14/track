#!/usr/bin/env bash
set -e

# Change to root directory
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "========================================================"
echo "   Starting TRACK - EOS Management System Locally"
echo "========================================================"

# --docker / -d: run the FULL containerized stack (db + backend + frontend)
# instead of the hybrid run below (Docker DB + native backend/frontend).
for arg in "$@"; do
  case "$arg" in
    --docker|-d)
      echo "==> Docker mode: delegating to scripts/docker_up.sh"
      exec "$ROOT_DIR/scripts/docker_up.sh"
      ;;
  esac
done

mkdir -p "$ROOT_DIR/.run"

# 1. Start Database (Auto-detect Docker vs Local PostgreSQL)
echo ""
echo "==> [1/4] Ensuring PostgreSQL database is running..."

if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "==> Docker detected! Starting PostgreSQL container via Docker Compose..."
    docker compose -f docker-compose.db.yml up -d
    echo "==> Waiting for Docker PostgreSQL to be ready..."
    until docker compose -f docker-compose.db.yml exec -T db pg_isready -U postgres -d track_db > /dev/null 2>&1; do
        sleep 1
    done
    echo "==> Docker PostgreSQL is ready on port 5432."
elif command -v pg_isready &> /dev/null && pg_isready -q; then
    echo "==> Local PostgreSQL service is running and healthy on port 5432."
elif [ -x "/opt/homebrew/opt/postgresql@16/bin/pg_isready" ] && /opt/homebrew/opt/postgresql@16/bin/pg_isready -q; then
    echo "==> Local Homebrew PostgreSQL 16 is running on port 5432."
else
    echo "==> PostgreSQL is not running. Attempting to start via Homebrew service..."
    brew services start postgresql@16 2>/dev/null || brew services start postgresql 2>/dev/null || true
    sleep 2
    if ! command -v docker &> /dev/null && ! command -v pg_isready &> /dev/null && [ ! -x "/opt/homebrew/opt/postgresql@16/bin/pg_isready" ]; then
        echo "ERROR: Neither Docker nor PostgreSQL service could be detected."
        echo "Please run: ./scripts/installations/install_all.sh"
        exit 1
    fi
fi

# 2. Run Database Migrations
echo ""
echo "==> [2/4] Applying database migrations..."
if [ ! -d "$ROOT_DIR/backend/.venv" ]; then
    python3 -m venv "$ROOT_DIR/backend/.venv"
fi
source "$ROOT_DIR/backend/.venv/bin/activate"

cd "$ROOT_DIR/backend"
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
fi

pip install --quiet -r requirements.txt
alembic upgrade head
echo "==> Migrations applied successfully."

# 3. Seed Database
echo ""
echo "==> [3/5] Seeding database with initial data (seed.json)..."
python -m app.db.seed
echo "==> Database seeded successfully."

# 4. Start Backend (FastAPI) in Background
echo ""
echo "==> [4/5] Starting Backend (FastAPI) on port 8000..."
cd "$ROOT_DIR/backend"
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
