#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../.."

echo "==> Stopping PostgreSQL container..."
docker compose -f docker-compose.db.yml down
echo "==> PostgreSQL container stopped."
