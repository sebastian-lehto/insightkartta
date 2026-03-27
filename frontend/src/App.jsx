import { useEffect, useState } from "react";
import { fetchUnemployment } from "./api";
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

  useEffect(() => {
    fetchUnemployment().then((res) => {
      setData(res.data.data);
      setAnalysis(res.data.analysis);
    });
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h1>InsightKartta</h1>

      <h2>Insights</h2>
      {analysis &&
        analysis.UnemploymentAnalysis.insights.map((i, idx) => (
          <p key={idx}>{i}</p>
        ))}
      <h2>Unemployment Trend</h2>

      <LineChart width={600} height={300} data={data}>
        <XAxis dataKey="year" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="unemployment_rate" />
      </LineChart>

      <h2>Data (sample)</h2>
      <pre>{JSON.stringify(data.slice(0, 5), null, 2)}</pre>
    </div>
  );
}

export default App;