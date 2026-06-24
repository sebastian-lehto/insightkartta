import { useEffect, useState } from "react";

// RegionSearch and MapView both need the municipality boundaries, and used to
// each fetch+parse the 700KB file independently. Caching the in-flight/
// resolved promise at module scope means every mount shares one fetch, which
// also closes the race where MapView's own copy was still loading when a
// search-pin click tried to focus a region on the map.
let cached = null;

function loadKunnatGeoJson() {
  if (!cached) {
    cached = fetch("/kunnat.geojson").then((res) => res.json());
  }
  return cached;
}

export function useKunnatGeoJson() {
  const [geoJson, setGeoJson] = useState(null);

  useEffect(() => {
    let cancelled = false;
    loadKunnatGeoJson().then((data) => {
      if (!cancelled) setGeoJson(data);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return geoJson;
}
