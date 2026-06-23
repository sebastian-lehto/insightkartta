import { useEffect, useMemo, useState } from "react";
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
  const [analysis, setAnalysis] = useState(null);

  const [selectedRegion, setSelectedRegion] = useState("KOKO MAA");
  const [year, setYear] = useState(null);

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

    const loadDataset = async () => {
      try {
        const res = await fetchDataset(selectedDataset);
        const datasetData = res.data.data ?? [];
        const datasetMeta = res.data.meta ?? {};
        const datasetAnalysis = res.data.analysis ?? null;

        setData(datasetData);
        setMeta(datasetMeta);
        setAnalysis(datasetAnalysis);

        const years = datasetData.map((d) => d.year).filter((y) => y != null);

        if (years.length > 0) {
          setYear(Math.max(...years));
        } else {
          setYear(null);
        }

        const hasWholeFinland = datasetData.some(
          (d) => d.region_name === "KOKO MAA"
        );

        if (hasWholeFinland) {
          setSelectedRegion("KOKO MAA");
        } else if (datasetData.length > 0) {
          setSelectedRegion(datasetData[0].region_name);
        } else {
          setSelectedRegion("");
        }
      } catch (error) {
        console.error(`Failed to load dataset '${selectedDataset}':`, error);
        setData([]);
        setMeta({});
        setAnalysis(null);
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
        <RegionSearch />
      </nav>

      <div className="dashboard-columns">
        <div className="dashboard-left">
          <InsightsPanel analysis={analysis} />

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