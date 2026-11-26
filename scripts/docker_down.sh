#!/usr/bin/env bash
# Stop the FULL containerized stack (docker compose down).
#   --clean / -v  also removes the PostgreSQL data volume (fresh DB next start).
set -e
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

VOLUMES=""
for arg in "$@"; do
  case "$arg" in
    --clean|-v) VOLUMES="-v" ;;
    -h|--help)
      echo "Usage: ./scripts/docker_down.sh [--clean]"
      exit 0
      ;;
  esac
done

echo "==> Stopping the full stack (docker compose down ${VOLUMES})..."
docker compose down ${VOLUMES}

if [ -n "${VOLUMES}" ]; then
  echo "==> Containers stopped and the database volume removed."
else
  echo "==> Containers stopped (database volume preserved)."
fi
