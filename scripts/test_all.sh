#!/usr/bin/env bash
# ADR0013: one documented command to run the whole test suite unattended,
# against the seed data and the fixed APP_NOW clock (2026-11-11T15:00:00Z).
#
# Layers:
#   - Rule tests + API integration tests (pytest)
#   - Two-browser real-time E2E (Playwright, Chromium)
#
# Prereq (one-time): cd frontend && npx playwright install chromium
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p .run
API_HEALTH="http://localhost:8000/api/v1/health"

echo "==> [1/4] Database: start, migrate, seed"
./backend/scripts/start_db.sh
./backend/scripts/run_migrations.sh
./backend/scripts/seed_db.sh

echo "==> [2/4] Backend tests (rule + API layers)"
(
  cd backend
  if [ -d .venv ]; then source .venv/bin/activate; fi
  python -m pytest -q
)

echo "==> [3/4] Ensure backend API is running for the E2E"
if ! curl -sf "$API_HEALTH" >/dev/null 2>&1; then
  echo "    starting backend API on :8000 ..."
  (
    cd backend
    if [ -d .venv ]; then source .venv/bin/activate; fi
    nohup uvicorn app.main:app --port 8000 >"$ROOT/.run/backend.e2e.log" 2>&1 &
  )
  for _ in $(seq 1 30); do curl -sf "$API_HEALTH" >/dev/null 2>&1 && break; sleep 1; done
fi

echo "==> [4/4] Playwright E2E (two browsers, facilitator -> attendee sync)"
(
  cd frontend
  npx playwright test
)

echo "==> All tests passed."
