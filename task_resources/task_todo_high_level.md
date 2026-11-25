# High-Level Project Checklist & ADR Roadmap

This checklist tracks step-by-step tasks required to build the product. Each item corresponds to an Architectural Decision Record (ADR) that will be created and executed one by one.

---

- [x] **ADR0000: Project Foundation & Tech Stack Architecture**
  - Define folder structure, workspace organization (Next.js TypeScript frontend, FastAPI backend, PostgreSQL database).
  - Docker Compose configuration setup with networking, volume persistence, and environment variable handling (`APP_NOW`, database URL, CORS).
  - Setup linting, typing, and standard toolchains.

- [x] **ADR0001: Data Modeling & Schema Design in PostgreSQL**
  - Design relational schema for: Companies, Teams, Users, Team Memberships, Measurables, Scores, Rocks, Milestones, Issues, To-Dos, Meetings, Meeting Attendees, and Meeting Ratings.
  - Implement constraints for source tracking (Issue linked to Measurable + week; To-Do linked to Issue).
  - Define migration strategy (e.g. Alembic for FastAPI / PostgreSQL).

- [x] **ADR0002: Time, Timezone & Simulated Clock (`APP_NOW`) Architecture**
  - Establish UTC timestamp storage standard.
  - Centralize `APP_NOW` retrieval mechanism (defaulting to `2026-11-11T15:00:00Z`).
  - Implement Monday-to-Sunday weekly boundary calculation in `America/Chicago` company timezone.
  - Implement quarter calculations and calendar due date evaluation for overdue status.

- [x] **ADR0003: Database Seeding & Idempotent Migration Strategy**
  - Implement database seeder loading from `seed.json`.
  - Ensure entity IDs match exactly (`u1`, `m1`, `t12`, `r1`, `team_lead`, etc.).
  - Ensure re-running `docker compose up` or re-running the seed script is completely idempotent and safe.

- [x] **ADR0004: Domain Business Rules Engine**
  - Implement Measurable status calculation (`at_least`, `at_most`, `between`, `exactly`, handling boundary, closed weeks, and pending current week).
  - Implement To-Do completion rate calculation (target 90%, exact ratio evaluation, round half up).
  - Implement Rock status and progress calculations (handling overdue milestones vs today's date).
  - Implement Issue ordering algorithm (Priority 5 down to 1, oldest first, no priority last).
  - Implement Meeting rating calculation (average to 1 decimal, excluding non-ratings).

- [x] **ADR0005: Rules Report CLI Command (`rules_report.json`)**
  - Build CLI command to calculate and print the required JSON structure for any `APP_NOW`.
  - Format output matching the exact structure defined in `task_resources/README.md`.
  - Validate output against `seed.json` initial state and commit `rules_report.json`.

- [x] **ADR0006: Server-Side Authorization & Role-Based Access Control (RBAC)**
  - Implement user switcher / session simulation for seeded users (`u1` to `u9`).
  - Enforce server-side permissions:
    - Admin: full permissions across all teams.
    - Team Member: read/write within assigned teams.
    - Observer: read-only access within assigned teams.
  - Verify team boundaries (reject access to non-member teams, even by guessed ID).

- [ ] **ADR0007: Core REST API Design & CRUD Endpoints**
  - Design and document REST API endpoints using FastAPI OpenAPI / Swagger.
  - Endpoints for Team switcher and Team summary data (Scorecard, Issues, To-Dos, Rocks).
  - Endpoints to edit scores inline, toggle To-Do completion (done / undo), solve issues with required notes.

- [ ] **ADR0008: Concurrency & Idempotency: "Make it an Issue"**
  - Design unique constraint or atomic transaction mechanism to prevent duplicate Issues for the same Measurable and week.
  - Handle race conditions gracefully when multiple users click "Make it an Issue" simultaneously.

- [ ] **ADR0009: Real-Time Sync & Meeting State Machine Architecture**
  - Design real-time synchronization layer (e.g., WebSockets or Server-Sent Events).
  - Manage Level 10 Meeting state machine: Facilitator controls, Section agenda (Scorecard 5m -> IDS 60m -> Conclude 10m), server-owned timer.
  - Handle attendee presence, live rating submissions, late joins, and browser reconnects.

- [ ] **ADR0010: Meeting Lifecycle & Historical Summary Snapshot Strategy**
  - Capture meeting summary snapshot upon meeting conclusion (Measurables status for last closed week, Issues solved, To-Dos created, ratings).
  - Strategy to keep historical meeting summaries immutable even after subsequent data edits.
  - Serve summary for ended meetings (including seeded `mt1` and `mt2`).

- [ ] **ADR0011: Frontend UI Architecture & Team Page Implementation**
  - Setup Next.js with TypeScript, Tailwind CSS, and shadcn/ui.
  - Build header with seeded user switcher and accessible team selector.
  - Implement Scorecard table (13-week grid with inline editing & "Make it an Issue" triggers).
  - Implement Issues list (unsolved vs solved views, create modal, priority selector, solve modal, add To-Do).
  - Implement To-Dos list (overdue flagging, completion rate widget, done/undo toggle).
  - Implement Rocks section (read-only view with expandable milestones and progress bars).

- [ ] **ADR0012: Frontend Meeting Page & Real-Time Facilitation UI**
  - Implement Level 10 Meeting view reusing Scorecard and IDS sections.
  - Real-time synced timer bar and section navigator (facilitator-only controls).
  - Attendee roster and live rating interface in Conclude step.
  - Meeting end flow displaying the immutable summary report.

- [ ] **ADR0013: Automated Testing Suite & Playwright E2E Multi-User Tests**
  - Unit tests for all business rules in 2.6 with edge and boundary cases.
  - API integration tests verifying RBAC (unauthorized team access refusal, Observer write rejection) and concurrent "Make it an Issue" requests.
  - Multi-browser Playwright E2E test verifying real-time sync between facilitator and attendee.
  - Generate test failure artifact (e.g. Playwright trace).

- [ ] **ADR0014: Production Packaging, Documentation & Submission Artifacts**
  - Prepare `docker compose up` one-command execution.
  - Write root `README.md` (<= 2 pages: setup, testing, assumptions, limitations, AI usage).
  - Write one-page Architectural Decision Record covering Section 2.8.
  - Prepare submission video walkthrough plan.
