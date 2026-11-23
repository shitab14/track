# How to Run Track

This guide covers running the application in development, standalone mode, or unified via Docker.

---

## 1. Quick Start with Runner Scripts

The repository provides executable runner scripts under each service's `scripts/` directory:

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

## 2. Running Individual Test Suites

### Backend Tests
```bash
./backend/scripts/test_be.sh
```

### Frontend Build Verification
```bash
./frontend/scripts/build_fe.sh
```

---

## 3. Standard Response Contract

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

## 4. Upcoming Steps on Roadmap

- **ADR0001**: PostgreSQL database schema, migrations, constraints & relations.
- **ADR0002**: Timezone and simulated clock (`APP_NOW`) integration.
- **ADR0003**: Idempotent database seeder (`seed.json`).
