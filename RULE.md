# Project Rules & Development Standards

This document establishes the mandatory engineering rules for building the product. All development, commits, and architectural phases must strictly adhere to these rules.

---

## 1. ADR-Driven Progression Rule
* Every major feature, database change, or architectural milestone must have a corresponding Architectural Decision Record in `adr/ADRXXXX.md`.
* Each ADR must be submitted to the user and **reviewed/approved before execution**.
* Never begin implementing an ADR's tasks before obtaining explicit approval.

---

## 2. Commit Message & Git Workflow Rules
* Commit messages must always be **short, precise, and meaningful**.
* Commit messages must **always include the ADR number** in parentheses at the end.
* **Commit Style & Format**:
  `<type>(<scope>): <precise imperative summary> (<ADR_NUMBER>)`
  * Allowed types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.
  * Allowed scopes: `adr`, `rules`, `foundation`, `backend`, `frontend`, `db`, `rules-report`, `meeting`, `auth`.
* **Layered Separation Policy**:
  * Keep commits cleanly separated by architectural layer rather than bundling mixed concerns:
    1. Documentation / Architectural Decisions: `docs(adr): ... (ADRXXXX)`
    2. Backend Service: `feat(backend): ... (ADRXXXX)`
    3. Frontend Client: `feat(frontend): ... (ADRXXXX)`
  * Squash noisy or fixup commits within a phase before pushing to maintain an uncluttered git log.

---

## 3. Architecture & Code Style Rules
* **Clean Architecture**: Clear separation of concerns across Routing, Services, Domain, Database Models, and UI Presentation.
* **SOLID & KISS Principles**: Keep solutions simple, direct, and readable so junior developers can easily understand and contribute.
* **Response Envelope Standard**:
  All backend endpoints must return the standardized contract:
  ```json
  {
    "code": 200,
    "message": "Descriptive message",
    "data": { ... }
  }
  ```
  On errors, `data` must be `null` and `code` must reflect the HTTP error code.

---

## 4. Security & Environment Protection Rule
* Never commit real secrets, environment variables (`.env`, `.env.local`, `.env.*`), virtual environments (`.venv`), or build artifacts (`.next/`, `node_modules/`, `__pycache__/`).
* All environment configuration templates must be tracked exclusively via committed `.env.example` files.

---

## 5. Independent Executable Scripts Rule
* Frontend, Backend, and Database must remain runnable independently.
* Every service must maintain its own `scripts/` folder with executable bash runners (e.g., `run_fe.sh`, `run_be.sh`, `test_be.sh`, `seed_db.sh`).
* Setup and execution instructions must be documented in `HOW_TO_RUN.md`.
