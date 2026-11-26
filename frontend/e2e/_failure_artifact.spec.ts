import { test, expect } from "@playwright/test";

/**
 * Deliberate failure used ONLY to generate a Playwright trace as the required
 * failure artifact (Part 3). It is excluded from the normal suite by the
 * config's testIgnore. Produce the artifact with:
 *
 *   cd frontend
 *   npx playwright test e2e/_failure_artifact.spec.ts --trace on
 *   npx playwright show-trace test-results/**\/trace.zip
 */
test("intentional failure to capture a trace", async ({ page }) => {
  await page.goto("/teams/team_ops/meeting");
  await expect(
    page.getByText("THIS ELEMENT DOES NOT EXIST — intentional failure for the trace artifact")
  ).toBeVisible({ timeout: 3_000 });
});
