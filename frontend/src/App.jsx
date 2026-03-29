import { useEffect, useMemo, useState } from "react";
import { fetchUnemployment } from "./api";
import MapView from "./components/MapView";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

function App() {
  const [data, setData] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [selectedRegion, setSelectedRegion] = useState("");
  const [year, setYear] = useState(null);

  // Fetch data
  useEffect(() => {
    fetchUnemployment().then((res) => {
      const dataset = res.data.data;

      setData(dataset);
      setAnalysis(res.data.analysis);

      const regions = [...new Set(dataset.map(d => d.region_name))];
      setSelectedRegion(regions[0]);

      const years = dataset.map(d => d.year);
      setYear(Math.min(...years)); // initialize properly
    });
  }, []);

  // Derived: regions
  const regions = useMemo(() => {
    return [...new Set(data.map(d => d.region_name))];
  }, [data]);

  // Derived: year range
  const { minYear, maxYear } = useMemo(() => {
    if (data.length === 0) return { minYear: 0, maxYear: 0 };

    const years = data.map(d => d.year);
    return {
      minYear: Math.min(...years),
      maxYear: Math.max(...years),
    };
  }, [data]);

  // Derived: filtered data for chart
  const filteredData = useMemo(() => {
    return data
      .filter(d => d.region_name === selectedRegion)
      .sort((a, b) => a.year - b.year);
  }, [data, selectedRegion]);

  const isReady = data.length > 0 && year !== null;

  return (
    <div style={{ padding: 20 }}>
      <h1>InsightKartta</h1>

      {/* Insights */}
      <h2>Insights</h2>
      {analysis &&
        analysis.UnemploymentAnalysis.insights.map((i, idx) => (
          <p key={idx}>{i}</p>
        ))}

      {/* Chart */}
      <h2>Unemployment Trend</h2>

      <label>Select Region: </label>
      <select
        value={selectedRegion}
        onChange={(e) => setSelectedRegion(e.target.value)}
      >
        {regions.map((region) => (
          <option key={region} value={region}>
            {region}
          </option>
        ))}
      </select>

      <LineChart width={600} height={300} data={filteredData}>
        <XAxis dataKey="year" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="unemployment_rate" />
      </LineChart>

      {/* Slider */}
      <h2>Year: {year}</h2>
      {isReady && (
        <input
          type="range"
          min={minYear}
          max={maxYear}
          value={year}
          onChange={(e) => setYear(Number(e.target.value))}
        />
      )}

      {/* Map */}
      <h2>Regional Map</h2>
      {isReady && <MapView data={data} year={year} />}

      {/* Debug */}
      <h2>Data (sample)</h2>
      <pre>{JSON.stringify(data.slice(0, 5), null, 2)}</pre>
    </div>
  );
}

export default App;