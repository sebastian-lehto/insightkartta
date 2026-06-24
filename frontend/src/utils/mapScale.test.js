import { describe, expect, it } from "vitest";
import { getBins, getColor } from "./mapScale";

describe("getBins", () => {
  it("uses the configured bins when present, ignoring the data", () => {
    const meta = { visualization: { map: { bins: [10, 20, 30, 40, 50] } } };
    expect(getBins(meta, [{ value: 999 }])).toEqual([10, 20, 30, 40, 50]);
  });

  it("falls back to a default range when there is no data and no configured bins", () => {
    expect(getBins({}, [])).toEqual([0, 20, 40, 60, 80]);
  });

  it("collapses to a single bin when every value is identical", () => {
    const data = [{ value: 5 }, { value: 5 }, { value: 5 }];
    expect(getBins({}, data)).toEqual([5]);
  });

  it("derives 5 evenly spaced thresholds from the data range", () => {
    const data = [{ value: 0 }, { value: 60 }];
    const bins = getBins({}, data);
    expect(bins).toHaveLength(5);
    expect(bins[0]).toBeCloseTo(10);
    expect(bins[4]).toBeCloseTo(50);
  });
});

describe("getColor", () => {
  const bins = [4, 6, 8, 10, 15];

  it("returns the no-data color for a null value", () => {
    expect(getColor(null, bins)).toBe("#ccc");
  });

  it("returns the documented fallback color when fewer than 2 bins are provided", () => {
    expect(getColor(50, [5])).toBe("#FEB24C");
    expect(getColor(50, [])).toBe("#FEB24C");
  });

  it("picks the band matching the value against ascending thresholds", () => {
    expect(getColor(2, bins)).toBe("#FEB24C"); // below first threshold
    expect(getColor(5, bins)).toBe("#FD8D3C"); // > bins[0]
    expect(getColor(20, bins)).toBe("#800026"); // > bins[4]
  });
});
