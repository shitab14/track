# Decision Record (§2.8)

One page on the five decisions the brief leaves open, with their tradeoffs. Full
rationale is in [`adr/`](adr/); this summarizes and links.

### 1. Data model & how Issues and To-Dos link to their sources — [ADR0001](adr/ADR0001.md), [ADR0010](adr/ADR0010.md)

Entities are relational with database-level integrity. An **Issue** optionally
links to its source score via `source_measurable_id` + `source_week_start`
(both-or-neither, enforced by a `CHECK`); a **To-Do** links to its source Issue
via `source_issue_id`. In-meeting provenance is a separate, explicit link
(`issues.solved_in_meeting_id`, `todos.created_in_meeting_id`) rather than a
timestamp window, so "solved/created during the meeting" is correct even though
the live timer and the business clock differ. **Tradeoff:** two extra nullable
columns and a little write-time wiring, in exchange for clock-independent,
queryable provenance and clean source links.

### 2. API design — [ADR0007](adr/ADR0007.md)

A documented REST API (FastAPI/OpenAPI at `/docs`) with a uniform envelope
`{code, message, data}` and `data: null` on error. Resources are team-scoped
(`/teams/{id}/scorecard|issues|todos|rocks`) with action endpoints for inline
score edits, Make-it-an-Issue, priority, solve, add-To-Do and done/undo.
**Tradeoff:** REST (not GraphQL) keeps the contract explicit and cache-friendly;
the envelope adds a thin wrapper but makes client handling uniform.

### 3. Real-time transport, ownership & recovery — [ADR0009](adr/ADR0009.md)

**Server-Sent Events** push server→client; all actions stay ordinary REST. The
**database meeting row is the single source of truth** (`current_section`,
`section_started_at`); an in-process async broadcaster only *notifies*. On
connect the server sends a full snapshot, so late joins, refreshes and
facilitator reconnects converge on one code path. The timer is server-owned but
rendered client-side from `section_started_at` + `server_now`. **Tradeoff:** SSE
is one-directional and needs no dependency (vs WebSockets' bidirectional channel
we don't need); the in-process bus is single-worker (scale-out = Postgres
`LISTEN/NOTIFY`).

### 4. Duplicate-free "Make it an Issue" under concurrency — [ADR0008](adr/ADR0008.md)

The database is the authority: a **partial unique index** on
`(source_measurable_id, source_week_start) WHERE solved_at IS NULL` permits at
most one unsolved Issue per measurable+week. The endpoint is idempotent —
check-then-insert, and on the losing insert's `IntegrityError` it rolls back,
re-queries and returns the winner. Two simultaneous clicks both receive the same
Issue. **Tradeoff:** relies on the DB constraint rather than app-level locking —
simpler and race-proof, at the cost of catching an expected integrity error.

### 5. Keeping past meeting summaries unchanged after later edits — [ADR0010](adr/ADR0010.md)

The only mutable input to a summary is closed-week scores (editable). So when a
meeting ends we compute the summary once and **freeze it** in
`meetings.summary_snapshot`; it is served thereafter and never recomputed, so a
later score edit cannot rewrite history. Seeded meetings carry no snapshot and
recompute deterministically from their stable historical data (and match the
rules report). **Tradeoff:** one JSON column and a write at conclusion, versus
recomputation that would not be immutable.
