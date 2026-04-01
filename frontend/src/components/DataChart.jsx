import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

function DataChart({ data, title, unit }) {
  return (
    <div style={{ marginBottom: "2rem" }}>
      <h2>
        {title} {unit ? `(${unit})` : ""}
      </h2>

      <LineChart width={800} height={320} data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="year" />
        <YAxis />
        <Tooltip
          formatter={(value) =>
            unit ? [`${value} ${unit}`, title] : [value, title]
          }
        />
        <Line type="monotone" dataKey="value" />
      </LineChart>
    </div>
  );
}

export default DataChart;