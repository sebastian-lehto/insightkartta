export default function IndicatorCard({
  title,
  absoluteChange,
  relativeChangePct,
}) {
  const positive = absoluteChange > 0;

  return (
    <div className="indicator-card">
      <h3>{title}</h3>

      <div
        style={{
          color: positive ? "green" : "red",
          fontWeight: "bold",
        }}
      >
        {absoluteChange > 0 ? "+" : ""}
        {absoluteChange.toFixed(1)}
      </div>

      <div>
        {relativeChangePct > 0 ? "+" : ""}
        {relativeChangePct?.toFixed(1)}%
      </div>
    </div>
  );
}