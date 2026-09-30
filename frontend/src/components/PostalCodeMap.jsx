import { useEffect, useMemo } from "react";
import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";
import L from "leaflet";

import { usePostalCodesGeoJson } from "../hooks/usePostalCodesGeoJson";
import { formatPostalCodeValue } from "../utils/formatPostalCodeValue";
import { getColor } from "../utils/mapScale";
import {
  getPostalCodeBins,
  normalizePostalCode,
  selectPostalCodeFeatures,
} from "../utils/postalCodeMap";

function FitPostalAreas({ geoJson }) {
  const map = useMap();

  useEffect(() => {
    if (!geoJson?.features?.length) return;

    const bounds = L.geoJSON(geoJson).getBounds();
    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [18, 18], maxZoom: 12 });
    }
  }, [geoJson, map]);

  return null;
}

function PostalMapLegend({ bins, label, unit }) {
  const labels = [
    { label: `≤ ${formatPostalCodeValue(bins[0], unit)}`, value: bins[0] },
    { label: `${formatPostalCodeValue(bins[0], unit)}–${formatPostalCodeValue(bins[1], unit)}`, value: (bins[0] + bins[1]) / 2 },
    { label: `${formatPostalCodeValue(bins[1], unit)}–${formatPostalCodeValue(bins[2], unit)}`, value: (bins[1] + bins[2]) / 2 },
    { label: `${formatPostalCodeValue(bins[2], unit)}–${formatPostalCodeValue(bins[3], unit)}`, value: (bins[2] + bins[3]) / 2 },
    { label: `${formatPostalCodeValue(bins[3], unit)}–${formatPostalCodeValue(bins[4], unit)}`, value: (bins[3] + bins[4]) / 2 },
    { label: `> ${formatPostalCodeValue(bins[4], unit)}`, value: bins[4] + 1 },
    { label: "No data", value: null },
  ];

  return (
    <div className="postal-map-legend" aria-label="Map legend">
      <div className="postal-map-legend-title">{label}{unit ? ` · ${unit}` : ""}</div>
      {labels.map((item, index) => (
        <div className="postal-map-legend-item" key={index}>
          <span
            className="postal-map-legend-swatch"
            style={{ backgroundColor: getColor(item.value, bins) }}
          />
          <span>{item.label}</span>
        </div>
      ))}
    </div>
  );
}

function createPopup(row, dataset, value) {
  const popup = document.createElement("div");
  const title = document.createElement("strong");
  title.textContent = row.postal_code_name
    ? `${row.postal_code} ${row.postal_code_name}`
    : row.postal_code;
  const metric = document.createElement("div");
  metric.textContent = `${dataset.label}: ${formatPostalCodeValue(value, dataset.unit)}`;
  popup.append(title, metric);
  return popup;
}

export default function PostalCodeMap({
  regionName,
  dataset,
  metric,
  postalCodes,
  activePostalCode,
  onPostalCodeHover,
}) {
  const { geoJson, error } = usePostalCodesGeoJson();
  const rowsByCode = useMemo(
    () => new Map(postalCodes.map((row) => [normalizePostalCode(row.postal_code), row])),
    [postalCodes]
  );
  const regionGeoJson = useMemo(
    () => selectPostalCodeFeatures(geoJson, postalCodes),
    [geoJson, postalCodes]
  );
  const bins = useMemo(
    () => dataset?.bins?.length === 5 ? dataset.bins : getPostalCodeBins(postalCodes, metric),
    [dataset, metric, postalCodes]
  );

  if (error) {
    return <div className="postal-map-status" role="status">Postal-code boundaries could not be loaded.</div>;
  }

  if (!geoJson) {
    return (
      <div className="postal-map-skeleton" role="status" aria-label="Loading postal-code boundaries">
        <span className="postal-map-skeleton-region postal-map-skeleton-region--one" />
        <span className="postal-map-skeleton-region postal-map-skeleton-region--two" />
        <span className="postal-map-skeleton-region postal-map-skeleton-region--three" />
        <span className="postal-map-skeleton-legend postal-skeleton" />
        <span className="visually-hidden">Loading postal-code boundaries</span>
      </div>
    );
  }

  if (!regionGeoJson.features.length) {
    return <div className="postal-map-status" role="status">No postal-code boundaries found for {regionName}.</div>;
  }

  const style = (feature) => {
    const code = normalizePostalCode(feature.properties?.postinumeroalue);
    const row = rowsByCode.get(code);
    const rawValue = row?.[metric];
    const value = rawValue == null || !Number.isFinite(Number(rawValue)) ? null : Number(rawValue);
    const isActive = code === normalizePostalCode(activePostalCode);

    return {
      fillColor: getColor(value, bins),
      color: isActive ? "#172554" : "#ffffff",
      weight: isActive ? 2.5 : 1,
      fillOpacity: value == null ? 0.35 : 0.78,
    };
  };

  const onEachFeature = (feature, layer) => {
    const code = normalizePostalCode(feature.properties?.postinumeroalue);
    const row = rowsByCode.get(code);
    if (!row) return;

    const value = row[metric];
    const tooltip = document.createElement("span");
    tooltip.textContent = `${code} · ${formatPostalCodeValue(value, dataset.unit)}`;
    layer.bindTooltip(tooltip, {
      className: "postal-map-tooltip",
      sticky: true,
      direction: "top",
    });
    layer.bindPopup(createPopup(row, dataset, value), { maxWidth: 280 });
    layer.on({
      mouseover() {
        onPostalCodeHover(code);
        layer.setStyle({ ...style(feature), weight: 2.5, color: "#172554" });
      },
      mouseout() {
        onPostalCodeHover(null);
        layer.setStyle(style(feature));
      },
    });
  };

  return (
    <div className="postal-code-map">
      <MapContainer
        center={[64.5, 26]}
        zoom={5}
        scrollWheelZoom={false}
        className="postal-code-leaflet-map"
      >
        <TileLayer
          attribution="&copy; OpenStreetMap"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitPostalAreas geoJson={regionGeoJson} />
        <GeoJSON
          key={`${regionName}-${metric}`}
          data={regionGeoJson}
          style={style}
          onEachFeature={onEachFeature}
        />
        <PostalMapLegend bins={bins} label={dataset.label} unit={dataset.unit} />
      </MapContainer>
    </div>
  );
}