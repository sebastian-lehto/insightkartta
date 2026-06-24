import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import RegionSearch from "./RegionSearch";

const GEOJSON_FIXTURE = {
  features: [{ properties: { Kunta: "Helsinki", Koodi: "091" } }],
};

function renderInRouter(onSelectRegion) {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route
          path="/"
          element={
            <>
              <RegionSearch onSelectRegion={onSelectRegion} />
              <div data-testid="dashboard-marker">dashboard</div>
            </>
          }
        />
        <Route path="/region/:code" element={<div data-testid="region-page-marker">region page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

async function openDropdownOnHelsinki(user) {
  const input = await screen.findByLabelText("Search for a region");
  await user.type(input, "Hels");
  return screen.findByText("Helsinki");
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ json: () => Promise.resolve(GEOJSON_FIXTURE) })
  );
});

// Regression tests for CONTEXT.md §5.7 / §10.15: the pin icon and the rest of
// the row are deliberately separate click targets. An earlier version made
// the whole row a single handler that only navigated, which made it
// impossible to preview a region on the map without leaving the dashboard.
describe("RegionSearch", () => {
  it("selects the region on the dashboard via the pin icon, without navigating", async () => {
    const user = userEvent.setup();
    const onSelectRegion = vi.fn();
    renderInRouter(onSelectRegion);

    await openDropdownOnHelsinki(user);
    await user.click(screen.getByLabelText("Show Helsinki on the map"));

    expect(onSelectRegion).toHaveBeenCalledWith("Helsinki");
    expect(screen.getByTestId("dashboard-marker")).toBeInTheDocument();
    expect(screen.queryByTestId("region-page-marker")).not.toBeInTheDocument();
  });

  it("navigates to the region's insights page when the rest of the row is clicked, without selecting it on the map", async () => {
    const user = userEvent.setup();
    const onSelectRegion = vi.fn();
    renderInRouter(onSelectRegion);

    await openDropdownOnHelsinki(user);
    await user.click(screen.getByTitle("View insights for Helsinki"));

    expect(onSelectRegion).not.toHaveBeenCalled();
    expect(screen.getByTestId("region-page-marker")).toBeInTheDocument();
  });

  it("navigates to the region's insights page on Enter, same as clicking the row", async () => {
    const user = userEvent.setup();
    const onSelectRegion = vi.fn();
    renderInRouter(onSelectRegion);

    await openDropdownOnHelsinki(user);
    await user.keyboard("{Enter}");

    expect(onSelectRegion).not.toHaveBeenCalled();
    expect(screen.getByTestId("region-page-marker")).toBeInTheDocument();
  });
});
