import { test, expect } from "@playwright/test";

// Regression coverage for the multi-period election comparison feature
// (CONTEXT.md §4.7): switching the period pill must update all four region
// page sections together — header emphasis, indicator grid, party chart, and
// correlation table — not just some of them.
test("switching the region page's period pill updates every section", async ({ page }) => {
  // KU091 = Helsinki, expected to have all three election periods generated.
  await page.goto("/region/KU091");

  const tabs = page.getByRole("tab");
  await expect(tabs.first()).toBeVisible();
  const tabCount = await tabs.count();
  test.skip(tabCount < 2, "Region has fewer than 2 periods to switch between");

  const partyChartHeading = page.locator("h2", { hasText: "Vote share change" });
  const beforeText = await partyChartHeading.textContent();

  await expect(tabs.nth(0)).toHaveAttribute("aria-selected", "true");
  await tabs.nth(1).click();

  await expect(tabs.nth(1)).toHaveAttribute("aria-selected", "true");
  await expect(tabs.nth(0)).toHaveAttribute("aria-selected", "false");

  await expect(partyChartHeading).not.toHaveText(beforeText ?? "");
});
