#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../.."

echo "==> Starting PostgreSQL container via Docker Compose..."
docker compose -f docker-compose.db.yml up -d

echo "==> Waiting for PostgreSQL to be ready..."
until docker compose -f docker-compose.db.yml exec -T db pg_isready -U postgres -d track_db > /dev/null 2>&1; do
    sleep 1
done

echo "==> PostgreSQL is ready on port 5432 (database: track_db)!"
