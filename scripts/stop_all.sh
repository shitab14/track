#!/usr/bin/env bash

# Change to root directory
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "========================================================"
echo "   Stopping TRACK - EOS Management System Locally"
echo "========================================================"

# --docker / -d: stop the FULL containerized stack (pass --clean to wipe data).
# --all  / -a: in addition to the app, also stop the native (Homebrew) Postgres
#              service. Off by default because that Postgres is a shared system
#              service other projects may rely on.
STOP_DB=0
for arg in "$@"; do
  case "$arg" in
    --docker|-d)
      exec "$ROOT_DIR/scripts/docker_down.sh" "$@"
      ;;
    --all|-a)
      STOP_DB=1
      ;;
  esac
done

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

# 3. Stop Docker containers (the DB-only container and/or the full stack,
#    whichever is running).
echo "==> Stopping Docker containers..."
docker compose -f docker-compose.db.yml down 2>/dev/null || true
docker compose down 2>/dev/null || true
echo "==> Docker containers stopped."

# 4. Stop the native (Homebrew) PostgreSQL service — only with --all/-a.
#    stop_all.sh normally leaves this running: it is a long-lived macOS
#    LaunchAgent that auto-starts on login and may be used by other projects,
#    and start_all.sh falls back to it when Docker is not running.
if [ "$STOP_DB" -eq 1 ]; then
    echo "==> Stopping native PostgreSQL service (requested via --all)..."
    if command -v brew >/dev/null 2>&1; then
        brew services stop postgresql@16 2>/dev/null \
            || brew services stop postgresql 2>/dev/null \
            || echo "    (no Homebrew postgresql service to stop)"
    else
        echo "    (Homebrew not found; skipping native Postgres stop)"
    fi
    if lsof -ti:5432 >/dev/null 2>&1; then
        echo "    NOTE: something is still listening on :5432 (non-brew Postgres"
        echo "          or Docker). Not force-killing it."
    else
        echo "==> Native PostgreSQL stopped."
    fi
fi

echo ""
echo "========================================================"
echo "   All TRACK services have been stopped."
echo "========================================================"
