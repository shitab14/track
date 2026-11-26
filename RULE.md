# Project Rules & Development Standards

This document establishes the mandatory engineering rules for building the product. All development, commits, and architectural phases must strictly adhere to these rules.

---

## 1. ADR-Driven Progression & Two-Stage Review Rule
* Every major feature, database change, or architectural milestone must have a corresponding Architectural Decision Record in `adr/ADRXXXX.md`.
* **Stage 1 (Design Review)**: Each ADR document must be submitted to the user and **reviewed/approved before any implementation begins**. Never begin execution without explicit design approval.
* **Stage 2 (Execution Review)**: After the approved tasks are implemented and tested, the execution output, diffs, and verification results must be **reviewed and approved by the human reviewer before finalizing/proceeding**.
* **Human in the Loop**: A human reviewer must review and approve every commit and transition.

---

## 2. Commit Message & Git Workflow Rules
* **Human Approval Before Every Commit (MANDATORY)**: Never create a commit before an explicit human approval of the staged changes. Stage the work, present the diff/summary for review, and wait for the reviewer's go-ahead; only then run `git commit`. This applies to every branch and is strictly required for the protected default branch (`main`). Do not commit automatically as part of executing an approved task — approval of the work is not approval to commit it.
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

## 3. Dependency & Library Management Rule (Zero Bloat)
* **No Unnecessary Libraries**: External packages or libraries must NOT be introduced if the task can be cleanly solved using the standard library or existing dependencies.
* Always prioritize native language capabilities (e.g., standard library math, date/time, built-in data structures) to keep the project lightweight, secure, and easily understandable.

---

## 4. Architecture & Code Style Rules
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

## 5. Security & Environment Protection Rule
* Never commit real secrets, environment variables (`.env`, `.env.local`, `.env.*`), virtual environments (`.venv`), or build artifacts (`.next/`, `node_modules/`, `__pycache__/`).
* All environment configuration templates must be tracked exclusively via committed `.env.example` files.

---

## 6. Independent Executable Scripts Rule
* Frontend, Backend, and Database must remain runnable independently.
* Every service must maintain its own `scripts/` folder with executable bash runners (e.g., `run_fe.sh`, `run_be.sh`, `test_be.sh`, `seed_db.sh`).
* Setup and execution instructions must be documented in `HOW_TO_RUN.md`.
