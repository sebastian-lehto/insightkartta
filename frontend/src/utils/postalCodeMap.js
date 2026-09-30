export function normalizePostalCode(value) {
  const code = String(value ?? "").trim();
  return /^\d+$/.test(code) ? code.padStart(5, "0") : code;
}

export function selectPostalCodeFeatures(geoJson, postalCodes) {
  if (!geoJson?.features || !postalCodes?.length) {
    return { type: "FeatureCollection", features: [] };
  }

  const visibleCodes = new Set(postalCodes.map((row) => normalizePostalCode(row.postal_code)));
  return {
    ...geoJson,
    features: geoJson.features.filter((feature) =>
      visibleCodes.has(normalizePostalCode(feature.properties?.postinumeroalue))
    ),
  };
}

export function getPostalCodeBins(rows, metric) {
  const values = rows
    .map((row) => row[metric])
    .filter((value) => value !== null && value !== undefined && value !== "")
    .map(Number)
    .filter((value) => Number.isFinite(value));

  if (!values.length) {
    return [0, 20, 40, 60, 80];
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) {
    const step = Math.max(Math.abs(min) * 0.01, 1);
    return [min - 2 * step, min - step, min, min + step, min + 2 * step];
  }

  return Array.from({ length: 5 }, (_, index) => min + ((max - min) * (index + 1)) / 6);
}