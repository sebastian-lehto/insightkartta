import { MapContainer, TileLayer, GeoJSON, useMap, useMapEvents } from "react-leaflet";
import { useMemo, useEffect, useRef } from "react";

import MapLegend from "./MapLegend";
import { getBins, getColor } from "../utils/mapScale";
import { useKunnatGeoJson } from "../hooks/useKunnatGeoJson";

const SELECTED_STYLE = { weight: 3, color: "#fff", fillOpacity: 1 };
const HOVER_STYLE    = { weight: 2.5, color: "#fff", fillOpacity: 1 };

// Closes any open popup whenever the dataset changes, so stale region overlays
// don't linger on the map after a data refresh or selection change.
function PopupCloser({ watch }) {
  const map = useMap();

  useEffect(() => {
    if (map && typeof map.closePopup === "function") {
      map.closePopup();
    }
  }, [watch, map]);

  return null;
}

function MapPointerCleanup({ clearHoverState, activeHoverLayerRef }) {
  useMapEvents({
    mouseleave() {
      clearHoverState(activeHoverLayerRef.current);
    },
    mouseout() {
      clearHoverState(activeHoverLayerRef.current);
    },
  });

  return null;
}

function MapView({ data, year, onRegionSelect, unit, meta, focusRegion }) {
  const selectedLayerRef = useRef(null); // { layer, baseStyle }
  const layersByNameRef = useRef({}); // regionName -> { layer, baseStyle }
  const activeTooltipLayerRef = useRef(null);
  const activeHoverLayerRef = useRef(null);
  const appliedFocusTokenRef = useRef(null); // focusRegion.token already applied

  const geoData = useKunnatGeoJson();

  const clearHoverState = (layer) => {
    if (!layer) return;

    const entry = Object.values(layersByNameRef.current).find((item) => item.layer === layer);
    const restoreStyle = entry?.baseStyle ?? {
      weight: 1,
      color: "rgba(255,255,255,0.6)",
      fillOpacity: 0.78,
    };

    if (selectedLayerRef.current?.layer === layer) {
      layer.setStyle(SELECTED_STYLE);
    } else {
      layer.setStyle(restoreStyle);
    }

    layer.closeTooltip?.();

    if (activeHoverLayerRef.current === layer) {
      activeHoverLayerRef.current = null;
    }

    if (activeTooltipLayerRef.current === layer) {
      activeTooltipLayerRef.current = null;
    }
  };

  // Clear selection when GeoJSON remounts
  useEffect(() => {
    selectedLayerRef.current = null;
    layersByNameRef.current = {};
    activeTooltipLayerRef.current = null;
    activeHoverLayerRef.current = null;
  }, [year]);

  // Selecting a region elsewhere (e.g. the search bar's map-pin button)
  // should behave like clicking it directly on the map. Also re-runs when
  // the map's own data arrives (`data`/`year`/`geoData` — MapView fetches
  // its own GeoJSON asynchronously after mounting), so a focus request made
  // before the GeoJSON layer existed yet (and therefore found nothing in
  // layersByNameRef) gets retried instead of silently doing nothing.
  //
  // appliedFocusTokenRef guards against the retry firing again on a later,
  // unrelated data/geoData change (e.g. switching datasets): without it,
  // re-applying setStyle/openPopup for an already-applied focusRegion would
  // fight PopupCloser's "close the popup when data changes" behavior.
  useEffect(() => {
    if (!focusRegion?.name) return;
    if (appliedFocusTokenRef.current === focusRegion.token) return;

    const entry = layersByNameRef.current[focusRegion.name];
    if (!entry) return;

    const { layer, baseStyle } = entry;

    if (selectedLayerRef.current && selectedLayerRef.current.layer !== layer) {
      selectedLayerRef.current.layer.setStyle(selectedLayerRef.current.baseStyle);
    }

    selectedLayerRef.current = { layer, baseStyle };
    layer.setStyle(SELECTED_STYLE);
    layer.openPopup();
    appliedFocusTokenRef.current = focusRegion.token;
  }, [focusRegion, data, year, geoData]);

  const yearData = useMemo(() => {
    return data.filter((d) => d.year === year && d.region !== "SSS");
  }, [data, year]);

  const dataMap = useMemo(() => {
    const map = {};
    yearData.forEach((d) => {
      map[d.region_name] = d.value;
    });
    return map;
  }, [yearData]);

  const bins = useMemo(() => getBins(meta, yearData), [meta, yearData]);

  const style = (feature) => {
    const value = dataMap[feature.properties.Kunta];
    return {
      fillColor: getColor(value, bins),
      weight: 1,
      color: "rgba(255,255,255,0.6)",
      fillOpacity: 0.78,
    };
  };

  const indicatorLabel = meta?.label ?? "";

  const onEachFeature = (feature, layer) => {
    const regionName = feature.properties.Kunta ?? feature.properties.name_fi;
    const regionCode = feature.properties.Koodi;
    const value = dataMap[regionName];
    const baseStyle = style(feature);
    layersByNameRef.current[regionName] = { layer, baseStyle };

    const valueDisplay =
      value != null ? `${value}${unit ? ` ${unit}` : ""}` : "No data";

    layer.bindTooltip(
      `<div class="map-tooltip-inner">
        <div class="map-tooltip-name">${regionName}</div>
        <div class="map-tooltip-value">${valueDisplay}</div>
      </div>`,
      {
        className: "map-tooltip",
        sticky: false,
        direction: "top",
        offset: [0, -6],
      }
    );

    layer.bindPopup(
      `<div class="map-popup">
        <div class="map-popup-name">${regionName}</div>
        <div class="map-popup-stats">
          <div class="map-popup-value">${valueDisplay}</div>
          ${indicatorLabel ? `<div class="map-popup-label">${indicatorLabel}</div>` : ""}
        </div>
        <a class="map-popup-link" href="/region/${regionCode}">View region insights →</a>
      </div>`,
      { maxWidth: 260, offset: [0, -20], autoPanPadding: [10, 60] }
    );

    layer.on({
      mouseover(e) {
        const currentTarget = e.target;

        if (activeHoverLayerRef.current && activeHoverLayerRef.current !== currentTarget) {
          clearHoverState(activeHoverLayerRef.current);
        }

        if (activeTooltipLayerRef.current && activeTooltipLayerRef.current !== currentTarget) {
          activeTooltipLayerRef.current.closeTooltip?.();
          activeTooltipLayerRef.current = null;
        }

        currentTarget.setStyle(HOVER_STYLE);
        currentTarget.bringToFront();
        activeHoverLayerRef.current = currentTarget;
        activeTooltipLayerRef.current = currentTarget;
        currentTarget.openTooltip();
      },
      mouseout(e) {
        const currentTarget = e.target;

        if (selectedLayerRef.current?.layer === currentTarget) {
          currentTarget.setStyle(SELECTED_STYLE);
          return;
        }

        clearHoverState(currentTarget);
      },
      mouseleave(e) {
        clearHoverState(e.target);
      },
      click(e) {
        e.target?.closeTooltip?.();
        if (activeTooltipLayerRef.current === e.target) {
          activeTooltipLayerRef.current = null;
        }

        if (selectedLayerRef.current && selectedLayerRef.current.layer !== layer) {
          selectedLayerRef.current.layer.setStyle(selectedLayerRef.current.baseStyle);
        }

        selectedLayerRef.current = { layer, baseStyle };
        layer.setStyle(SELECTED_STYLE);

        onRegionSelect(regionName);
      },
    });
  };

  const isDataReady = yearData.length > 0;

  return (
    <MapContainer
      center={[64.5, 26]}
      zoom={5}
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        attribution="&copy; OpenStreetMap"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapPointerCleanup
        clearHoverState={clearHoverState}
        activeHoverLayerRef={activeHoverLayerRef}
      />
      <PopupCloser watch={data} />
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
