import { useState, useEffect } from "react";
import { useMap } from "react-leaflet";
import { getColor } from "../utils/mapScale";

function MapLegend({ bins, unit }) {
  const map = useMap();
  const [zoom, setZoom] = useState(() => map.getZoom());

  useEffect(() => {
    const handleZoom = () => setZoom(map.getZoom());
    map.on("zoomend", handleZoom);
    return () => map.off("zoomend", handleZoom);
  }, [map]);

  const u = unit ? ` ${unit}` : "";
  const faded = zoom >= 8;

  const legendItems = [
    { label: `> ${bins[4]}${u}`,             value: bins[4] + 1 },
    { label: `${bins[3]} – ${bins[4]}${u}`,  value: bins[3] + (bins[4] - bins[3]) / 2 },
    { label: `${bins[2]} – ${bins[3]}${u}`,  value: bins[2] + (bins[3] - bins[2]) / 2 },
    { label: `${bins[1]} – ${bins[2]}${u}`,  value: bins[1] + (bins[2] - bins[1]) / 2 },
    { label: `${bins[0]} – ${bins[1]}${u}`,  value: bins[0] + (bins[1] - bins[0]) / 2 },
    { label: `< ${bins[0]}${u}`,             value: bins[0] - 1 },
    { label: "No data",                       value: null },
  ];

  return (
    <div className={`map-legend${faded ? " map-legend--faded" : ""}`}>
      <h4>Legend</h4>
      {legendItems.map((item, idx) => (
        <div key={idx} className="map-legend-row">
          <span
            className="map-legend-swatch"
            style={{ backgroundColor: getColor(item.value, bins) }}
          />
          <span>{item.label}</span>
        </div>
      ))}
    </div>
  );
}

export default MapLegend;
