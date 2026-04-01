import { MapContainer, TileLayer, GeoJSON } from "react-leaflet";
import { useMemo, useEffect, useState } from "react";

import MapLegend from "./MapLegend";



function MapView({ data, year, onRegionSelect, unit }) {
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

  // Color scale
  const getColor = (value) => {
    if (value == null) return "#ccc";
    if (value > 15) return "#800026";
    if (value > 10) return "#BD0026";
    if (value > 8) return "#E31A1C";
    if (value > 6) return "#FC4E2A";
    if (value > 4) return "#FD8D3C";
    return "#FEB24C";
  };

  const style = (feature) => {
    const regionName = feature.properties.Kunta;
    const value = dataMap[regionName];

    return {
      fillColor: getColor(value),
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
      <MapLegend />
    </MapContainer>
  );
}

export default MapView;