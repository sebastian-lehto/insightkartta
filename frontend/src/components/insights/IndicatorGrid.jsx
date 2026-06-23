import IndicatorCard from "./IndicatorCard";

const INDICATOR_ORDER = [
  "unemployment",
  "education_upper_secondary",
  "education_tertiary",
  "population",
];

export default function IndicatorGrid({ indicators = {}, relationships = {} }) {
  const allKeys = [
    ...new Set([
      ...INDICATOR_ORDER.filter(
        (k) => k in indicators || k in relationships
      ),
      ...Object.keys(indicators).filter((k) => !INDICATOR_ORDER.includes(k)),
    ]),
  ];

  if (allKeys.length === 0) return null;

  return (
    <section className="insight-section">
      <h2>Socioeconomic context</h2>
      <div className="indicator-grid">
        {allKeys.map((name) => (
          <IndicatorCard
            key={name}
            name={name}
            indicatorData={indicators[name]}
            relationshipData={relationships[name]}
          />
        ))}
      </div>
    </section>
  );
}
