#!/usr/bin/env bash
# Start the FULL containerized stack (PostgreSQL + backend + frontend) via Docker
# Compose. The backend container applies migrations and the idempotent seed on
# start. Use --no-build to skip rebuilding images.
set -e
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

BUILD="--build"
for arg in "$@"; do
  case "$arg" in
    --no-build) BUILD="" ;;
    -h|--help)
      echo "Usage: ./scripts/docker_up.sh [--no-build]"
      exit 0
      ;;
  esac
done

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: The Docker daemon is not running. Start Docker Desktop and retry."
  exit 1
fi

echo "==> Starting the full stack (docker compose up -d ${BUILD})..."
docker compose up -d ${BUILD}

echo "==> Waiting for the API to become healthy..."
for _ in $(seq 1 60); do
  if curl -sf http://localhost:8000/api/v1/health >/dev/null 2>&1; then
    echo "==> API is healthy."
    break
  fi
  sleep 2
done

echo ""
echo "========================================================"
echo "   TRACK (containers) is now running!"
echo "   - Frontend UI:  http://localhost:3000"
echo "   - Backend API:  http://localhost:8000"
echo "   - API Docs:     http://localhost:8000/docs"
echo ""
echo "   Stop with: ./scripts/docker_down.sh   (add --clean to wipe data)"
echo "========================================================"
