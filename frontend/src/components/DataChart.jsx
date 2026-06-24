import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

// eslint-disable-next-line react-refresh/only-export-components -- exported for unit testing, see INSTRUCTIONS.md
export const yFormatter = (v) => {
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1000) return `${(v / 1000).toFixed(0)}k`;
  return v;
};

function DataChartTooltip({ active, payload, label, unit }) {
  if (!active || !payload?.length) return null;
  const value = payload[0].value;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-title">{label}</div>
      <div>{value != null ? (unit ? `${value} ${unit}` : String(value)) : "—"}</div>
    </div>
  );
}

function DataChart({ data, title, unit }) {
  return (
    <div className="data-chart">
      <h2>
        {title} {unit ? `(${unit})` : ""}
      </h2>

      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" fill="transparent" />
          <XAxis
            dataKey="year"
            tick={{ fontSize: 12, fill: "var(--text)" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tickFormatter={yFormatter}
            tick={{ fontSize: 12, fill: "var(--text)" }}
            axisLine={false}
            tickLine={false}
            width={48}
          />
          <Tooltip content={<DataChartTooltip unit={unit} />} />
          <Line
            type="monotone"
            dataKey="value"
            stroke="var(--accent)"
            strokeWidth={2}
            dot={{ r: 3, fill: "var(--accent)", strokeWidth: 0 }}
            activeDot={{ r: 5, fill: "var(--accent)", strokeWidth: 0 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default DataChart;
