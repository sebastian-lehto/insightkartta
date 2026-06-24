import { test, expect } from "@playwright/test";

// Regression coverage for CONTEXT.md §5.7 / §10.15: the search dropdown's pin
// icon and the rest of the row must stay separate click targets. This was
// previously a single handler that only navigated, making it impossible to
// preview a region on the dashboard without leaving it.
test.describe("RegionSearch pin vs row split", () => {
  test("clicking the pin icon selects the region on the dashboard without navigating", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator(".dataset-tab").first()).toBeVisible();

    await page.getByLabel("Search for a region").fill("Helsinki");
    await page.getByRole("button", { name: "Show Helsinki on the map" }).click();

    // Still on the dashboard, not the region page.
    await expect(page).toHaveURL("/");
    await expect(page.locator(".insights-panel-region")).toHaveText(/Helsinki/);
  });

  test("clicking the rest of the row navigates to the region's insights page", async ({ page }) => {
    await page.goto("/");

    await page.getByLabel("Search for a region").fill("Helsinki");
    await page.getByTitle("View insights for Helsinki").click();

    await expect(page).toHaveURL(/\/region\//);
    await expect(page.locator(".region-header h1")).toHaveText("Helsinki");
  });
});
