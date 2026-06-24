import { test, expect } from "@playwright/test";

// Regression coverage for CONTEXT.md §5.7: selecting a region via the search
// pin opens its map popup exactly like a real map click would (MapView's
// `focusRegion` effect mirrors the click handler), and switching datasets
// afterward must close it via `PopupCloser` instead of leaving a stale
// region popup on screen next to insights that have already reset to
// national.
test("selecting a region via the search pin opens its popup, and switching datasets closes it", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".dataset-tab").first()).toBeVisible();

  await page.getByLabel("Search for a region").fill("Helsinki");
  await page.getByRole("button", { name: "Show Helsinki on the map" }).click();

  const popup = page.locator(".leaflet-popup");
  await expect(popup).toBeVisible();
  await expect(popup.locator(".map-popup-name")).toHaveText("Helsinki");

  const tabs = page.locator(".dataset-tab");
  const activeTabText = await page.locator(".dataset-tab--active").textContent();
  const otherTab = tabs.filter({ hasNotText: activeTabText ?? "" }).first();
  await otherTab.click();

  await expect(popup).toBeHidden();
});
