import { describe, expect, it } from "vitest";
import {
  getPostalCodeBins,
  normalizePostalCode,
  selectPostalCodeFeatures,
} from "./postalCodeMap";

describe("postalCodeMap helpers", () => {
  it("normalizes numeric postal codes while preserving non-numeric codes", () => {
    expect(normalizePostalCode(100)).toBe("00100");
    expect(normalizePostalCode("00120")).toBe("00120");
    expect(normalizePostalCode("SSSSS")).toBe("SSSSS");
  });

  it("keeps only postal areas represented by the selected region data", () => {
    const geoJson = {
      type: "FeatureCollection",
      features: [
        { type: "Feature", properties: { postinumeroalue: "00100" } },
        { type: "Feature", properties: { postinumeroalue: "00120" } },
      ],
    };

    const selected = selectPostalCodeFeatures(geoJson, [{ postal_code: 100 }]);

    expect(selected.features).toHaveLength(1);
    expect(selected.features[0].properties.postinumeroalue).toBe("00100");
  });

  it("creates five thresholds from the selected metric range", () => {
    const bins = getPostalCodeBins([
      { population: 0 },
      { population: 60 },
    ], "population");

    expect(bins).toHaveLength(5);
    expect(bins[0]).toBeCloseTo(10);
    expect(bins[4]).toBeCloseTo(50);
  });

  it("ignores missing values and centers a constant metric range", () => {
    const bins = getPostalCodeBins([
      { population: null },
      { population: 100 },
      { population: 100 },
    ], "population");

    expect(bins).toEqual([98, 99, 100, 101, 102]);
  });
});