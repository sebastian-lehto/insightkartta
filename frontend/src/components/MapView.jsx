import { MapContainer, TileLayer, GeoJSON } from "react-leaflet";
import { useMemo, useEffect, useState } from "react";

import MapLegend from "./MapLegend";
import { getBins, getColor } from "../utils/mapScale";


function MapView({ data, year, onRegionSelect, unit, meta }) {
  // Load GeoJSON
  const [geoData, setGeoData] = useState(null);
  useEffect(() => {
    fetch("/kunnat.geojson")
    .then(res => res.json())
    .then(data => setGeoData(data));
  }, []);

  // Filter data for selected year
  const yearData = useMemo(() => {
    return data.filter(d => d.year === year && d.region !== "SSS");
  }, [data, year]);

  // Convert to lookup: region → unemployment
  const dataMap = useMemo(() => {
    const map = {};
    yearData.forEach(d => {
      map[d.region_name] = d.value;
    });
    return map;
  }, [yearData]);

  // Get bins for color scale
  const bins = useMemo(() => getBins(meta, yearData), [meta, yearData]);

  // Color scale
  const getColor = (value, bins) => {
    if (value == null) return "#ccc";
    if (value > bins[4]) return "#800026";
    if (value > bins[3]) return "#BD0026";
    if (value > bins[2]) return "#E31A1C";
    if (value > bins[1]) return "#FC4E2A";
    if (value > bins[0]) return "#FD8D3C";
    return "#FEB24C";
  };

  const style = (feature) => {
    const regionName = feature.properties.Kunta;
    const value = dataMap[regionName];

    return {
      fillColor: getColor(value, bins),
      weight: 1,
      color: "white",
      fillOpacity: 0.7,
    };
  };

  const onEachFeature = (feature, layer) => {
    
    const regionName = feature.properties.Kunta ?? feature.properties.name_fi;
    const value = dataMap[regionName];

    layer.bindTooltip(
      `${regionName}: ${value != null ? value : "No data"}${value != null && unit ? ` ${unit}` : ""}`
    );
    
    layer.on({
      click: () => {
        onRegionSelect(regionName);
      },
    });
  };

  const isDataReady = yearData.length > 0;
  
  return (
    <MapContainer
      center={[64.5, 26]}
      zoom={5}
      style={{ height: "500px", width: "100%" }}
    >
      <TileLayer
        attribution="&copy; OpenStreetMap"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {geoData && isDataReady && (
        <GeoJSON
          key={year}
          data={geoData}
          style={style}
          onEachFeature={onEachFeature}
        />
      )}
      <MapLegend bins={bins} unit={unit} />
    </MapContainer>
  );
}

export default MapView;