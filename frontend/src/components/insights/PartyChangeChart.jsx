import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

export default function PartyChangeChart({
  partyChanges,
}) {
  const chartData = [...partyChanges]
    .sort((a, b) => b.vote_change - a.vote_change);

  return (
    <div>
      <h2>Vote Change Since Previous Election</h2>

      <ResponsiveContainer
        width="100%"
        height={400}
      >
        <BarChart data={chartData}>
          <XAxis dataKey="party" />
          <YAxis />
          <Tooltip />

          <Bar
            dataKey="vote_change"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}