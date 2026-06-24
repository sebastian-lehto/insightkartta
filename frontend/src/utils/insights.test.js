import { describe, expect, it } from "vitest";
import { computeInsights } from "./insights";

describe("computeInsights", () => {
  it("returns no insights when there is no region data", () => {
    expect(computeInsights({ regionData: [], allData: [], label: "X", unit: "%", regionName: "Y" })).toEqual([]);
  });

  it("describes a single data point without a trend", () => {
    const insights = computeInsights({
      regionData: [{ year: 2024, value: 12.3 }],
      allData: [],
      label: "Unemployment Rate",
      unit: "%",
      regionName: "Helsinki",
    });

    expect(insights).toHaveLength(1);
    expect(insights[0].type).toBe("single");
    expect(insights[0].text).toContain("12.3%");
  });

  it("emits trend, peak and low insights for a multi-year series", () => {
    const regionData = [
      { year: 2021, value: 9.0 },
      { year: 2023, value: 11.5 },
      { year: 2025, value: 10.0 },
    ];

    const insights = computeInsights({
      regionData,
      allData: [],
      label: "Unemployment Rate",
      unit: "%",
      regionName: "Helsinki",
    });

    const types = insights.map((i) => i.type);
    expect(types).toEqual(["trend", "peak", "low"]);
    expect(insights[0].direction).toBe("up"); // 9.0 -> 10.0
    expect(insights[1].text).toContain("11.5%");
    expect(insights[2].text).toContain("9.0%");
  });

  // Regression test for CONTEXT.md §4.9 / §10.14: a "%"-unit dataset must
  // compare against the national rate as a percentage-point difference, an
  // absolute-count dataset (e.g. persons) must compare as a share of the
  // national total instead — subtracting a region's population from a
  // national *sum* produces a meaningless number ("Helsinki was 4,958,489
  // persons below the national average").
  it("compares percentage-unit datasets as a percentage-point difference from the national rate", () => {
    const regionData = [{ year: 2025, value: 12.0 }];
    const allData = [
      { region_name: "KOKO MAA", year: 2025, value: 10.0 },
      { region_name: "Helsinki", year: 2025, value: 12.0 },
    ];

    const insights = computeInsights({
      regionData,
      allData,
      label: "Unemployment Rate",
      unit: "%",
      regionName: "Helsinki",
    });

    const compare = insights.find((i) => i.type === "compare");
    expect(compare.direction).toBe("up");
    expect(compare.text).toContain("above the national rate");
    expect(compare.text).toContain("percentage points");
  });

  it("compares absolute-count datasets as a share of the national total, not a subtraction", () => {
    const regionData = [{ year: 2025, value: 650_000 }];
    const allData = [
      { region_name: "KOKO MAA", year: 2025, value: 5_600_000 },
      { region_name: "Helsinki", year: 2025, value: 650_000 },
    ];

    const insights = computeInsights({
      regionData,
      allData,
      label: "Population",
      unit: "persons",
      regionName: "Helsinki",
    });

    const share = insights.find((i) => i.type === "share");
    expect(share).toBeDefined();
    expect(share.text).not.toMatch(/below the national average/);
    expect(share.text).toContain("% of Finland's total");
    // Both the region's own figure and the national total should be present
    // (formatted with fi-FI's space thousands-separator, not a comma).
    expect(share.text).toMatch(/650\s000/);
    expect(share.text).toMatch(/5\s600\s000/);
  });

  it("does not compute a national comparison when the region itself is national", () => {
    const regionData = [{ year: 2025, value: 5_600_000 }];
    const allData = [{ region_name: "KOKO MAA", year: 2025, value: 5_600_000 }];

    const insights = computeInsights({
      regionData,
      allData,
      label: "Population",
      unit: "persons",
      regionName: "KOKO MAA",
    });

    expect(insights.find((i) => i.type === "compare" || i.type === "share")).toBeUndefined();
  });

  it("reports a flat comparison when the region exactly matches the national rate", () => {
    const regionData = [{ year: 2025, value: 10.0 }];
    const allData = [
      { region_name: "KOKO MAA", year: 2025, value: 10.0 },
      { region_name: "Helsinki", year: 2025, value: 10.0 },
    ];

    const insights = computeInsights({
      regionData,
      allData,
      label: "Unemployment Rate",
      unit: "%",
      regionName: "Helsinki",
    });

    const compare = insights.find((i) => i.type === "compare");
    expect(compare.direction).toBe("flat");
    expect(compare.text).toContain("matched the national rate");
  });
});
