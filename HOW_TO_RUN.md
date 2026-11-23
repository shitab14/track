# How to Run Track

This guide covers running the application in development, standalone mode, or unified via Docker.

---

## 1. Quick Start: Database (PostgreSQL via Docker)

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
  - `http://localhost:8000/api/v1/health`: System health status and clock info.
  - `http://localhost:8000/api/v1/mock/team-summary`: Rich mock team summary showing the standard envelope with sample measurables and issues.

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

## 5. Upcoming Steps on Roadmap

- **ADR0002**: Timezone and simulated clock (`APP_NOW`) integration.
- **ADR0003**: Idempotent database seeder (`seed.json`).
- **ADR0004**: Business Rules Engine.
