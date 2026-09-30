import { useEffect, useState } from "react";

let cachedRequest = null;

function loadPostalCodesGeoJson() {
  if (!cachedRequest) {
    cachedRequest = fetch("/finland-postal-codes.geojson")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Postal GeoJSON request failed: ${response.status}`);
        }
        return response.json();
      })
      .catch((error) => {
        cachedRequest = null;
        throw error;
      });
  }
  return cachedRequest;
}

export function usePostalCodesGeoJson() {
  const [geoJson, setGeoJson] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    loadPostalCodesGeoJson()
      .then((data) => {
        if (!cancelled) setGeoJson(data);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return { geoJson, error };
}