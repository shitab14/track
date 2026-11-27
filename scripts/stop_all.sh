#!/usr/bin/env bash

# Change to root directory
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "========================================================"
echo "   Stopping TRACK - EOS Management System Locally"
echo "========================================================"

# By default stop_all.sh stops the frontend, backend, Docker containers, and the
# native (Homebrew) Postgres service (start_all.sh starts that in hybrid mode, so
# stopping it keeps start/stop symmetric and frees :5432).
#
# --docker / -d: stop the FULL containerized stack instead (pass --clean to wipe
#                data).
# --all    / -a: after the normal teardown, also QUIT Docker Desktop (symmetric
#                with docker_up.sh, which launches it). Off by default because
#                Docker Desktop may be used by other projects.
QUIT_DOCKER_APP=0
for arg in "$@"; do
  case "$arg" in
    --docker|-d)
      exec "$ROOT_DIR/scripts/docker_down.sh" "$@"
      ;;
    --all|-a)
      QUIT_DOCKER_APP=1
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

# 4. Stop the native (Homebrew) PostgreSQL service. start_all.sh starts this in
#    hybrid mode (when Docker is not running), so stop_all.sh stops it to keep
#    start/stop symmetric and leave :5432 free. Note: the service is a LaunchAgent
#    with KeepAlive=true, so `brew services stop` is the correct way to stop it
#    (killing the process alone would let launchd relaunch it).
echo "==> Stopping native PostgreSQL service..."
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

# 5. With --all/-a, also quit Docker Desktop (symmetric with docker_up.sh
#    launching it). The GUI app reports to AppleScript as "Docker Desktop" on
#    current versions and "Docker" on older ones, so try both.
if [ "$QUIT_DOCKER_APP" -eq 1 ] && [ "$(uname -s)" = "Darwin" ]; then
    quit_docker=0
    for app in "Docker Desktop" "Docker"; do
        if osascript -e "application \"$app\" is running" 2>/dev/null | grep -qi true; then
            echo "==> Quitting $app..."
            osascript -e "quit app \"$app\"" 2>/dev/null || true
            quit_docker=1
            break
        fi
    done
    if [ "$quit_docker" -eq 1 ]; then
        echo "==> Docker Desktop quit."
    else
        echo "==> Docker Desktop not running; nothing to quit."
    fi
fi

echo ""
echo "========================================================"
echo "   All TRACK services have been stopped."
echo "========================================================"
