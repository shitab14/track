# How to Run Track

This guide covers running the application in development, standalone mode, or unified via Docker.

---

## 1. One-Command Master Control (Recommended)

To run the **entire stack locally** (PostgreSQL Database + Database Migrations + Backend API + Frontend UI) with a single command:

### Start Entire System
```bash
./scripts/start_all.sh
```
* Spins up PostgreSQL 16 container via Docker and waits until healthy.
* Automatically applies Alembic database migrations.
* Starts the FastAPI backend at `http://localhost:8000` (background process, logs in `.run/backend.log`).
* Starts the Next.js frontend at `http://localhost:3000` (background process, logs in `.run/frontend.log`).

### Stop Entire System
```bash
./scripts/stop_all.sh
```
* Gracefully terminates the Frontend, Backend, and stops the PostgreSQL Docker container.

---

## 2. Independent Service Runners

You don't need PostgreSQL installed locally! A pre-configured Docker Compose service is ready to run.

### Start PostgreSQL
```bash
./backend/scripts/start_db.sh
```
* Spins up PostgreSQL 16 container (`track_postgres`) on port `5432`.
* Database: `track_db` | User: `postgres` | Password: `postgres`.
* Automatically waits until the database is healthy and ready to accept connections.
* Data is safely persisted in a Docker volume (`track_pgdata`).

### Apply Database Migrations (Schema Creation)
```bash
./backend/scripts/run_migrations.sh
```
* Applies Alembic migrations to create all tables, check constraints, foreign keys, and concurrency indexes.

### Reset Database (Clean Schema Rebuild)
```bash
./backend/scripts/reset_db.sh
```
* Wipes all tables and re-applies migrations cleanly from scratch.

### Stop PostgreSQL
```bash
./backend/scripts/stop_db.sh
```

---

## 2. Quick Start with Service Runner Scripts

### Run Backend (FastAPI)
```bash
./backend/scripts/run_be.sh
```
* Sets up virtual environment `.venv` if not already created.
* Installs requirements from `backend/requirements.txt`.
* Copies `.env.example` to `.env` if missing.
* Runs Uvicorn on `http://localhost:8000`.
* Interactive API docs: `http://localhost:8000/docs`.
* **Browser Test Endpoints (GET)**:
  - `http://localhost:8000/`: Welcome root endpoint.
  - `http://localhost:8000/api/v1/health`: Detailed health status reporting both `backend` and `database` connectivity.
  - `http://localhost:8000/api/v1/mock/team-summary`: Rich mock team summary showing the standard envelope with sample measurables and issues.
* **Frontend Status Monitoring**:
  - The frontend UI (`http://localhost:3000`) displays live, real-time status indicators in the bottom-right corner for both **Backend** and **DB** (online/offline).

### Run Frontend (Next.js)
```bash
./frontend/scripts/run_fe.sh
```
* Installs dependencies if `node_modules` does not exist.
* Copies `.env.example` to `.env.local` if missing.
* Starts Next.js development server on `http://localhost:3000`.

---

## 3. Running Test Suites

### Backend Tests (Health & Model Unit Tests)
```bash
./backend/scripts/test_be.sh
```

### Frontend Build Verification
```bash
./frontend/scripts/build_fe.sh
```

---

## 4. Standard Response Contract

All backend endpoints strictly follow the uniform envelope:
```json
{
  "code": 200,
  "message": "Success",
  "data": { ... }
}
```
In case of any HTTP or database error, the response returns the error status with `"data": null`:
```json
{
  "code": 404,
  "message": "Resource not found",
  "data": null
}
```

---

## 5. Testing (ADR0013)

Run the **entire test suite** — rule tests, API integration tests, and the
two-browser real-time E2E — with one command, against the seed data and the
fixed `APP_NOW` clock:

```bash
./scripts/test_all.sh
```

It starts/seeds PostgreSQL, runs `pytest` (rule + API layers), ensures the
backend API is up, and runs the Playwright E2E.

**One-time prerequisite** for the E2E (installs the Chromium browser):

```bash
cd frontend && npx playwright install chromium
```

### Test layers

- **Rule tests** (`backend/tests/test_rules.py`): every business rule in §2.6
  with boundary cases.
- **API tests** (`backend/tests/test_rbac.py`, `test_concurrency.py`): a Team
  Member reading another team is refused, an Observer write is refused, and
  concurrent *Make it an Issue* requests return a single Issue (a real
  PostgreSQL thread race).
- **End-to-end** (`frontend/e2e/meeting-sync.spec.ts`): two browsers in one
  meeting — the facilitator advances the agenda and the second browser follows
  via SSE.

Backend tests alone: `./backend/scripts/test_be.sh`. E2E alone (stack running):
`cd frontend && npm run test:e2e`.

### Fixture & clock strategy

- Unit/rule and pure service tests run on an isolated, freshly **seeded
  in-memory SQLite** database (fully deterministic).
- Integration tests run against the **seeded PostgreSQL** via the API and clean
  up any rows they create, so repeated runs are stable.
- The business clock is always **`APP_NOW` (`2026-11-11T15:00:00Z`)**; no rule
  reads the wall clock.

### Failure artifact (Playwright trace)

```bash
cd frontend
npm run test:e2e:trace                 # runs a deliberate failing spec with tracing
npx playwright show-trace test-results/**/trace.zip
```

The normal suite captures a trace automatically on any failure
(`trace: retain-on-failure`).
