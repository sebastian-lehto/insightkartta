import IndicatorCard from "./IndicatorCard";

export default function IndicatorGrid({
  indicators,
}) {
  return (
    <div className="indicator-grid">
      {Object.entries(indicators).map(
        ([name, data]) => (
          <IndicatorCard
            key={name}
            title={name}
            absoluteChange={data.absolute_change}
            relativeChangePct={
              data.relative_change_pct
            }
          />
        )
      )}
    </div>
  );
}