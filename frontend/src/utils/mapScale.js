export function getBins(meta, data) {
  const configuredBins = meta?.visualization?.map?.bins;
  if (configuredBins && configuredBins.length > 0) {
    return configuredBins;
  }

  const values = data
    .map((d) => d.value)
    .filter((v) => typeof v === "number" && !Number.isNaN(v));

  if (values.length === 0) return [0, 20, 40, 60, 80];

  const min = Math.min(...values);
  const max = Math.max(...values);

  if (min === max) return [min];

  const step = (max - min) / 5;
  return [
    min + step,
    min + step * 2,
    min + step * 3,
    min + step * 4,
  ];
}

export function getColor(value, bins) {
  if (value == null) return "#ccc";
  if (bins.length === 1) return "#FEB24C";
  if (value > bins[3]) return "#800026";
  if (value > bins[2]) return "#BD0026";
  if (value > bins[1]) return "#E31A1C";
  if (value > bins[0]) return "#FC4E2A";
  return "#FEB24C";
}