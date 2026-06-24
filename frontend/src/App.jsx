import { useEffect, useMemo, useRef, useState } from "react";
import { Routes, Route } from "react-router-dom";
import { fetchDataset, fetchDatasets } from "./api";

import DatasetSelector from "./components/DatasetSelector";
import DataChart from "./components/DataChart";
import YearSlider from "./components/YearSlider";
import MapView from "./components/MapView";
import InsightsPanel from "./components/InsightsPanel";
import RegionPage from "./components/RegionPage";
import RegionSearch from "./components/RegionSearch";

function App() {
  const [datasets, setDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState("");
  const [data, setData] = useState([]);
  const [meta, setMeta] = useState({});

  const [selectedRegion, setSelectedRegion] = useState("KOKO MAA");
  const [focusRegion, setFocusRegion] = useState(null);
  const [year, setYear] = useState(null);
  const isInitialDatasetLoadRef = useRef(true);

  useEffect(() => {
    const loadDatasets = async () => {
      try {
        const res = await fetchDatasets();
        const availableDatasets = res.data;

        setDatasets(availableDatasets);

        if (availableDatasets.length > 0) {
          setSelectedDataset(availableDatasets[0].name);
        }
      } catch (error) {
        console.error("Failed to load datasets:", error);
      }
    };

    loadDatasets();
  }, []);

  useEffect(() => {
    if (!selectedDataset) return;

    // Only the very first dataset load should ever default the region; later
    // switches always reset to the dataset's default view.
    const isInitialLoad = isInitialDatasetLoadRef.current;
    isInitialDatasetLoadRef.current = false;

    const loadDataset = async () => {
      try {
        const res = await fetchDataset(selectedDataset);
        const datasetData = res.data.data ?? [];
        const datasetMeta = res.data.meta ?? {};

        setData(datasetData);
        setMeta(datasetMeta);

        const years = datasetData.map((d) => d.year).filter((y) => y != null);

        if (years.length > 0) {
          setYear(Math.max(...years));
        } else {
          setYear(null);
        }

        const hasWholeFinland = datasetData.some(
          (d) => d.region_name === "KOKO MAA"
        );
        const defaultRegion = hasWholeFinland
          ? "KOKO MAA"
          : datasetData.length > 0
          ? datasetData[0].region_name
          : "";

        if (isInitialLoad) {
          // The user may have already picked a region (e.g. via the search
          // pin) while this first load was still in flight — don't clobber
          // that selection once the request finally resolves.
          setSelectedRegion((prev) =>
            datasetData.some((d) => d.region_name === prev) ? prev : defaultRegion
          );
        } else {
          setSelectedRegion(defaultRegion);
        }
      } catch (error) {
        console.error(`Failed to load dataset '${selectedDataset}':`, error);
        setData([]);
        setMeta({});
        setYear(null);
        setSelectedRegion("");
      }
    };

    loadDataset();
  }, [selectedDataset]);

  const regions = useMemo(() => {
    return [...new Set(data.map((d) => d.region_name).filter(Boolean))];
  }, [data]);

const chartData = useMemo(() => {
    return data
      .filter((d) => d.region_name === selectedRegion)
      .sort((a, b) => a.year - b.year);
  }, [data, selectedRegion]);

  const yearBounds = useMemo(() => {
    if (data.length === 0) {
      return { minYear: 0, maxYear: 0 };
    }

    const years = data.map((d) => d.year).filter((y) => y != null);

    if (years.length === 0) {
      return { minYear: 0, maxYear: 0 };
    }

    return {
      minYear: Math.min(...years),
      maxYear: Math.max(...years),
    };
  }, [data]);

  const handleSelectRegionFromSearch = (name) => {
    setSelectedRegion(name);
    setFocusRegion({ name, token: Date.now() });
  };

  const chartTitle =
    selectedRegion === "KOKO MAA"
      ? `${meta.label ?? selectedDataset} - Finland`
      : `${meta.label ?? selectedDataset} - ${selectedRegion}`;

  const isReady = data.length > 0 && year !== null;

  const dashboard = (
    <div className="dashboard">
      <nav className="top-bar">
        <span className="top-bar-brand">InsightKartta</span>
        <DatasetSelector
          datasets={datasets}
          selectedDataset={selectedDataset}
          onChange={setSelectedDataset}
        />
        <RegionSearch onSelectRegion={handleSelectRegionFromSearch} />
      </nav>

      <div className="dashboard-columns">
        <div className="dashboard-left">
          <InsightsPanel
            regionData={chartData}
            allData={data}
            label={meta.label ?? selectedDataset}
            unit={meta.unit}
            regionName={selectedRegion}
          />

          <DataChart
            data={chartData}
            title={chartTitle}
            unit={meta.unit}
          />
        </div>

        <div className="dashboard-right">
          {isReady && (
            <>
              <YearSlider
                year={year}
                minYear={yearBounds.minYear}
                maxYear={yearBounds.maxYear}
                onChange={setYear}
              />
              <div className="map-fill">
                <MapView
                  data={data}
                  year={year}
                  onRegionSelect={setSelectedRegion}
                  unit={meta.unit}
                  meta={meta}
                  focusRegion={focusRegion}
                />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <Routes>
      <Route path="/" element={dashboard} />
      <Route path="/region/:regionCode" element={<RegionPage />} />
    </Routes>
  );
}

export default App;