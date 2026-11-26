# Track — API Reference

REST API for the Track EOS platform. This document is the human-readable
reference; the machine-readable spec is [`openapi.json`](openapi.json), and the
running server serves interactive docs at **`/docs`** (Swagger) and **`/redoc`**.

- **Base URL:** `http://localhost:8000/api/v1`
- **OpenAPI:** `GET /api/v1/openapi.json`

---

## Conventions

### Response envelope

Every endpoint returns the same envelope:

```json
{ "code": 200, "message": "Descriptive message", "data": { } }
```

On error, `data` is `null` and `code` carries the HTTP status:

```json
{ "code": 403, "message": "Access to team 'team_ops' is denied", "data": null }
```

### Authentication (seeded-user switcher)

There is no login; the caller identifies a seeded user with a header:

```
X-User-Id: u1
```

If omitted it defaults to `u1` (Admin). An unknown id returns **401**. The SSE
stream cannot send headers, so it takes the user as a **query parameter**
(`?user_id=...`) instead.

### Roles & team boundaries (enforced server-side)

| Role | Access |
| --- | --- |
| `admin` | Read/write every team in the company |
| `team_member` | Read/write their own teams |
| `observer` | Read-only in their own teams |

Any access to a team the user does not belong to returns **403** (or **404** for
an unknown team id), even by guessing the id. Writes by an Observer return
**403**.

### Common status codes

`200` OK · `201` Created · `401` unknown user · `403` forbidden (role/team) ·
`404` not found · `409` conflict (e.g. meeting already ended) · `422` validation.

---

## Health

| Method & path | Purpose |
| --- | --- |
| `GET /health` | Liveness + backend/database status and the active `APP_NOW`/timezone. |
| `GET /` (root, no prefix) | Welcome payload with links to the docs. |

---

## Auth & Users

| Method & path | Auth | Purpose |
| --- | --- | --- |
| `GET /auth/users` | any | List the seeded users (`id`, `name`, `role`) for the switcher. |
| `GET /auth/me` | any | The current user's profile (`id`, `name`, `email`, `role`). |
| `GET /auth/teams/{team_id}/verify-read` | team read | Assert read access (debug helper). |
| `POST /auth/teams/{team_id}/verify-write` | team write | Assert write access (debug helper). |

---

## Teams

| Method & path | Auth | Purpose |
| --- | --- | --- |
| `GET /teams` | any | Teams the user can access (Admins: all). Each: `{id, name, user_role}`. |
| `GET /teams/{team_id}/members` | team read | Eligible To-Do owners (the team's Admins + Team Members). |
| `GET /teams/{team_id}/scorecard` | team read | Scorecard (see below). |
| `GET /teams/{team_id}/issues` | team read | `{unsolved: Issue[], solved: Issue[]}`. |
| `GET /teams/{team_id}/todos` | team read | `{completion_rate, todos: Todo[]}` (last closed week's rate). |
| `GET /teams/{team_id}/rocks` | team read | `Rock[]` with computed status, progress and milestones. |

**Scorecard** `data`: `{ weeks: string[13], measurables: [{ id, name, unit,
goal_type, goal_value, goal_min, goal_max, owner:{id,name}, scores: { "YYYY-MM-DD":
{ id, value, status } }, current_week_score } ] }`. `status` is `on_track` /
`off_track` / `pending`. `weeks` are the 13 Mondays ending at the last closed
week; `current_week_score` is the separate current-week cell.

**Rock**: `{ id, title, quarter, owner, computed_status: on_track|off_track|
complete, progress:{done,total,percent}, milestones:[{id,title,due_date,done,
overdue}] }`.

---

## Scorecard actions

| Method & path | Auth | Body | Purpose |
| --- | --- | --- | --- |
| `POST /teams/{team_id}/scores` | team write | `{measurable_id, week_start, value}` | Upsert a score (last-save-wins). `week_start` must be a Monday; future weeks → 422. |
| `POST /scores/{score_id}/make-issue` | team write | — | Promote an off-track score to an Issue, or return the existing unsolved one. Idempotent and safe under concurrency (returns the same Issue). |

`make-issue` responds `200` with message `"Issue created"` or `"Issue already
exists"`.

---

## Issues

| Method & path | Auth | Body | Purpose |
| --- | --- | --- | --- |
| `POST /teams/{team_id}/issues` | team write | `{title, priority?}` | Create an Issue (owner = caller). `201`. |
| `PATCH /issues/{issue_id}/priority` | team write | `{priority}` (1–5 or null) | Set/clear priority. |
| `POST /issues/{issue_id}/solve` | team write | `{resolution_note}` (required) | Solve; `409` if already solved. |

**Issue**: `{ id, title, priority, owner:{id,name}, source:{measurable_id,
week_start}|null, created_at, resolution_note, solved_at }`. Unsolved issues are
returned in **issue order** (priority 5→1, then oldest first, no-priority last).

---

## To-Dos

| Method & path | Auth | Body | Purpose |
| --- | --- | --- | --- |
| `POST /issues/{issue_id}/todos` | team write | `{title, owner_id, due_date?}` | Add a To-Do linked to the Issue; owner must be a team Admin/Member; due in 7 days by default. `201`. |
| `POST /todos/{todo_id}/done` | team write | — | Mark done. |
| `POST /todos/{todo_id}/undo` | team write | — | Mark not done. |

**Todo**: `{ id, title, owner, due_date, done, overdue, source_issue_id,
created_at, done_at }`.

---

## Meetings (Level 10) & real-time

| Method & path | Auth | Purpose |
| --- | --- | --- |
| `POST /teams/{team_id}/meetings` | team write | Start a meeting; caller becomes facilitator. Idempotent — returns the active meeting if one exists (one active per team). |
| `GET /teams/{team_id}/active-meeting` | team read | The team's active meeting state, or `data: null`. |
| `GET /meetings/{meeting_id}` | team read | Current meeting state snapshot. |
| `GET /meetings/{meeting_id}/events?user_id=` | team read | **SSE stream** (see below). |
| `POST /meetings/{meeting_id}/join` | team read | Record the caller as an attendee (idempotent). |
| `POST /meetings/{meeting_id}/advance` | facilitator | Advance the agenda; `403` if not the facilitator, `409` if ended. |
| `POST /meetings/{meeting_id}/end` | facilitator | End the meeting; freezes the summary. |
| `PUT /meetings/{meeting_id}/rating` | attending Admin/Member | `{rating}` 1–10; changeable until end. |
| `GET /meetings/{meeting_id}/summary` | team read | Ended meeting's immutable summary; `409` if not ended. |

**Meeting state** (`data`): `{ id, team_id, facilitator_id, section:
scorecard|ids|conclude|ended, section_started_at, section_budget_seconds,
elapsed_seconds, over_time, server_now, started_at, ended_at, attendees:[{id,
name,joined_at}], ratings:{values:{userId:rating}, count, average} }`. The timer
is server-owned; clients render the countdown from `section_started_at` +
`server_now` and show `over_time` past budget (the server never auto-advances).

**Meeting summary** (`data`): `{ scorecard_week, measurable_status:{id:status},
issues_solved:[id], todos_created:[id], attendee_ids:[id], rating }`.

### SSE stream — `GET /meetings/{meeting_id}/events?user_id=`

`Content-Type: text/event-stream`. On connect the server sends a full snapshot,
then live events; the browser's `EventSource` auto-reconnects. Two named events:

```
event: meeting_state
data: { ...the meeting state object above... }

event: data_changed
data: { "scope": "scorecard" | "issues" | "todos" }
```

`meeting_state` is pushed on every state change (join, advance, rate, end);
`data_changed` tells clients to refetch the reused Scorecard/Issues/To-Dos
sections. A heartbeat comment (`: heartbeat`) keeps the connection alive.

---

## Notes

- `GET /mock/team-summary` is a scaffolding/mock endpoint from the initial setup
  (ADR0000) and is not part of the production contract.
- All timestamps are UTC (ISO-8601). Business rules read a simulated clock
  `APP_NOW` (default `2026-11-11T15:00:00Z`), not the wall clock; the meeting
  timer is the one exception.
