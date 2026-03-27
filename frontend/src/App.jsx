import { useEffect, useState } from "react";
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
  const [year, setYear] = useState(2000);
  const years = data.map(d => d.year);
  const minYear = Math.min(...years);
  const maxYear = Math.max(...years);

  // Fetch data once
  useEffect(() => {
    fetchUnemployment().then((res) => {
      const dataset = res.data.data;
      setData(dataset);
      setAnalysis(res.data.analysis);

      // Set default region immediately
      const regions = [...new Set(dataset.map(d => d.region))];
      setSelectedRegion(regions[0]);
    });
  }, []);

  // Get unique regions
  const regions = [...new Set(data.map(d => d.region))];

  // Filter data by selected region
  const filteredData = data
    .filter(d => d.region === selectedRegion)
    .sort((a, b) => a.year - b.year);

  return (
    <div style={{ padding: 20 }}>
      <h1>InsightKartta</h1>

      <h2>Insights</h2>
      {analysis &&
        analysis.UnemploymentAnalysis.insights.map((i, idx) => (
          <p key={idx}>{i}</p>
        ))}

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

      <h2>Year: {year}</h2>
      <input
        type="range"
        min={minYear}
        max={maxYear}
        value={year}
        onChange={(e) => setYear(Number(e.target.value))}
      />

      <h2>Regional Map</h2>
      <MapView data={data} year={year} />

      <h2>Data (sample)</h2>
      <pre>{JSON.stringify(data.slice(0, 5), null, 2)}</pre>
    </div>
  );
}

export default App;