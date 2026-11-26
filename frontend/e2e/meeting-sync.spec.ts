import { test, expect, type APIRequestContext, type BrowserContext, type Page } from "@playwright/test";

/**
 * ADR0013: two-browser real-time sync. A facilitator starts a Level 10 Meeting
 * and advances the agenda; a second browser (a different seeded user) must
 * follow within ~1s. The section on the attendee's page changes only via the
 * SSE push, so this guards the real-time path end to end.
 *
 * Prereq: the seeded stack is running (scripts/test_all.sh brings it up) and
 * Chromium is installed (`npx playwright install chromium`).
 */
const API = process.env.E2E_API_URL || "http://localhost:8000/api/v1";
const TEAM = "team_ops"; // u4 and u8 are both Team Members here

async function pageAsUser(context: BrowserContext, userId: string): Promise<Page> {
  // Pin the seeded user deterministically (the app reads track_user_id).
  await context.addInitScript((id) => {
    try {
      window.localStorage.setItem("track_user_id", id);
    } catch {
      /* ignore */
    }
  }, userId);
  return context.newPage();
}

async function clearActiveMeeting(request: APIRequestContext) {
  const res = await request.get(`${API}/teams/${TEAM}/active-meeting`, {
    headers: { "X-User-Id": "u4" },
  });
  const body = await res.json();
  if (body?.data?.id) {
    await request.post(`${API}/meetings/${body.data.id}/end`, { headers: { "X-User-Id": "u4" } });
  }
}

test.beforeEach(async ({ request }) => clearActiveMeeting(request));
test.afterEach(async ({ request }) => clearActiveMeeting(request));

test("facilitator advances the agenda and the attendee follows", async ({ browser }) => {
  const facCtx = await browser.newContext();
  const attCtx = await browser.newContext();
  const facilitator = await pageAsUser(facCtx, "u4");
  const attendee = await pageAsUser(attCtx, "u8");

  // Facilitator starts the meeting and lands on the Scorecard section.
  await facilitator.goto(`/teams/${TEAM}/meeting`);
  await facilitator.getByRole("button", { name: "Start Level 10 Meeting" }).click();
  await expect(facilitator.getByRole("heading", { name: "Scorecard" })).toBeVisible();

  // Attendee joins the active meeting and sees the Scorecard too.
  await attendee.goto(`/teams/${TEAM}/meeting`);
  await expect(attendee.getByRole("heading", { name: "Scorecard" })).toBeVisible();
  await expect(attendee.getByRole("heading", { name: "Issues" })).toHaveCount(0);

  // Facilitator advances to IDS.
  await facilitator.getByRole("button", { name: /IDS/ }).click();

  // The attendee's browser follows via SSE: the Issues (IDS) section appears.
  await expect(attendee.getByRole("heading", { name: "Issues" })).toBeVisible({ timeout: 5_000 });
  await expect(attendee.getByText(/Unsolved/)).toBeVisible();

  await facCtx.close();
  await attCtx.close();
});

test("an observer sees the meeting read-only with no start control", async ({ browser }) => {
  // u7 is an Observer of team_sales.
  const ctx = await browser.newContext();
  const observer = await pageAsUser(ctx, "u7");
  await observer.goto("/teams/team_sales/meeting");
  await expect(observer.getByText("No active meeting")).toBeVisible();
  await expect(observer.getByRole("button", { name: "Start Level 10 Meeting" })).toHaveCount(0);
  await ctx.close();
});
