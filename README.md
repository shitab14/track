# Track — EOS Weekly Meeting Platform

A leadership team's weekly loop in one place: track **Measurables** (Scorecard),
quarterly **Rocks**, **To-Dos** and **Issues**, and run the **Level 10 Meeting**
live across browsers. Modeled on Ninety's EOS edition.

**Stack:** Next.js (TypeScript, Tailwind, shadcn/ui, React Query) · FastAPI ·
PostgreSQL 16 (Alembic). Real-time via Server-Sent Events.

---

## Quick start — one command

```bash
docker compose up
```

Starts PostgreSQL, the API (migrations + idempotent seed run automatically) and
the web app:

- Web app → **http://localhost:3000**
- API docs (OpenAPI) → **http://localhost:8000/docs**

The seed is safe to re-run, so `docker compose up` again never duplicates data.
`docker compose down` keeps the data volume; add `-v` to reset it.

Pick a seeded user from the header switcher (the login stand-in) and choose a
team. Admins and Team Members can edit; Observers are read-only. For local
(non-Docker) runs and per-service scripts, see **[HOW_TO_RUN.md](HOW_TO_RUN.md)**.
To deploy on a server, see **[HOW_TO_DEPLOY.md](HOW_TO_DEPLOY.md)**.

---

## Tests — one command

```bash
cd frontend && npx playwright install chromium   # one-time, for the E2E
./scripts/test_all.sh
```

Runs, on the seed data and the fixed `APP_NOW` clock:

- **Rule tests** — every §2.6 rule with boundary cases.
- **API tests** — cross-team read refused, Observer write refused, concurrent
  *Make it an Issue* returns one Issue (real PostgreSQL race).
- **E2E** — two browsers in one meeting: the facilitator advances the agenda and
  the second browser follows via SSE.

Fixture/clock strategy and the failure-artifact (Playwright trace) steps are in
**[HOW_TO_RUN.md](HOW_TO_RUN.md#5-testing-adr0013)**.

## Rules report

```bash
./backend/scripts/rules_report.sh > rules_report.json      # default APP_NOW
./backend/scripts/rules_report.sh --app-now 2026-12-01T15:00:00Z
```

Prints every computed value in §2.6 as JSON for a freshly seeded database at any
clock. The committed [`rules_report.json`](rules_report.json) is the output for
the seed's default now.

---

## Assumptions (judgement calls)

- **Two clocks.** Business rules (weeks, overdue, statuses) always read the frozen
  `APP_NOW` (`2026-11-11T15:00:00Z`). The live meeting **timer** uses the real
  wall clock (elapsed seconds can't come from a frozen instant). A meeting
  summary's "last closed week" is taken as of `APP_NOW` at conclusion.
- **Scorecard columns.** Shows the 13 weeks ending at the last closed week, plus a
  separate editable **current-week** column (pending until scored).
- **To-Do completion** widget reports the **last closed** week's rate (§2.5).
- **"During the meeting"** (issues solved / to-dos created) is an explicit
  attribution link set at action time — clock-independent; seeded meetings fall
  back to the timestamp window.
- **Summary immutability** is enforced by freezing a snapshot at conclusion;
  seeded meetings have no snapshot and recompute from stable historical data.
- **Authorization** is enforced on the server (RBAC + team boundaries); the UI
  only hides controls for Observers. The user switcher is the sanctioned login
  stand-in. The SSE stream authenticates via a query parameter because
  `EventSource` cannot set headers.

## Known limitations

- The SSE broadcaster is **in-process** — correct for the single worker that
  `docker compose` runs; multi-worker scale-out would use Postgres
  `LISTEN/NOTIFY` (the one line that changes).
- Scores and Issue priority are **last-save-wins** (no lost-update protection —
  a Part 3 bonus). No audit trail.
- The frontend is client-rendered (no SSR); fine for this authenticated tool.
- The walkthrough video and the Playwright trace are produced by documented
  manual steps.

## AI usage

Built with **Claude (Claude Code)** throughout, under an ADR-driven, two-stage
human-reviewed workflow (see [`RULE.md`](RULE.md)): each `adr/ADRXXXX.md` was
designed and approved before implementation, then the code, migrations and tests
were reviewed before moving on. Claude produced the schema and migrations, the
rules engine, the REST API and RBAC, the real-time meeting backend, the Next.js
UI, the test suite and this documentation; a human reviewed and approved every
ADR and commit. The decision record is **[DECISIONS.md](DECISIONS.md)**; the full
rationale lives in [`adr/`](adr/).
