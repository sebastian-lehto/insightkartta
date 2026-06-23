import {
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from "recharts";

const COLOR_GAIN = "#16a34a";
const COLOR_LOSS = "#dc2626";

function PartyTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-title">{d.party_name}</div>
      <div>
        {d.vote_share_change_pct > 0 ? "+" : ""}
        {d.vote_share_change_pct.toFixed(2)} pp
      </div>
    </div>
  );
}

export default function PartyChangeChart({ partyChanges, electionSummary }) {
  if (!partyChanges?.length) return null;

  const period =
    electionSummary?.previous_year && electionSummary?.latest_year
      ? `${electionSummary.previous_year} → ${electionSummary.latest_year}`
      : null;

  const chartData = [...partyChanges]
    .filter((p) => p.vote_share_change_pct != null)
    .sort((a, b) => b.vote_share_change_pct - a.vote_share_change_pct);

  return (
    <section className="insight-section">
      <h2>
        Vote share change (pp){period ? `, ${period}` : ""}
      </h2>

      <ResponsiveContainer width="100%" height={320}>
        <BarChart
          data={chartData}
          margin={{ top: 4, right: 16, left: 0, bottom: 4 }}
        >
          <XAxis
            dataKey="party_code"
            tick={{ fontSize: 13, fill: "var(--text)" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            unit=" pp"
            tick={{ fontSize: 12, fill: "var(--text)" }}
            axisLine={false}
            tickLine={false}
            width={52}
          />
          <ReferenceLine y={0} stroke="var(--border)" />
          <Tooltip content={<PartyTooltip />} cursor={{ fill: "var(--accent-bg)" }} />
          <Bar dataKey="vote_share_change_pct" radius={[3, 3, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={index}
                fill={entry.vote_share_change_pct >= 0 ? COLOR_GAIN : COLOR_LOSS}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}
