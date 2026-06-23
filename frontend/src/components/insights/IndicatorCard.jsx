const INDICATOR_LABELS = {
  unemployment: "Unemployment",
  education_upper_secondary: "Upper secondary edu.",
  education_tertiary: "Tertiary edu.",
  population: "Population",
};

const RELATIVE_LABELS = {
  above_average: "↑ above national avg",
  below_average: "↓ below national avg",
  similar: "≈ near national avg",
};

function formatChange(value, dataset) {
  if (value == null) return "—";
  const sign = value > 0 ? "+" : "";
  if (dataset === "population") {
    return `${sign}${Math.round(value).toLocaleString("fi-FI")}`;
  }
  return `${sign}${value.toFixed(1)} pp`;
}

export default function IndicatorCard({ name, indicatorData, relationshipData }) {
  const label = INDICATOR_LABELS[name] ?? name;
  const noData = !indicatorData && (!relationshipData || relationshipData.data_status === "no_data");

  const absoluteChange = indicatorData?.absolute_change ?? relationshipData?.regional_absolute_change;
  const nationalChange = relationshipData?.national_absolute_change;
  const relative = relationshipData?.relative_to_national;
  const relativeLabel = RELATIVE_LABELS[relative];

  const startYear = indicatorData?.indicator_start_year;
  const endYear = indicatorData?.indicator_end_year;
  const period = startYear && endYear ? `${startYear}–${endYear} data` : null;

  return (
    <div className={`indicator-card${noData ? " indicator-card--no-data" : ""}`}>
      <div className="indicator-card-label">{label}</div>
      {period && <div className="indicator-card-period">{period}</div>}

      <div className="indicator-card-divider" />

      {noData ? (
        <div className="indicator-card-no-data">No data for this period</div>
      ) : (
        <>
          <div className="indicator-card-change">
            {formatChange(absoluteChange, name)}
          </div>

          {relativeLabel && nationalChange != null && (
            <div className="indicator-card-vs-national">
              {relativeLabel}
              <span className="indicator-card-national-value">
                {" "}(national: {formatChange(nationalChange, name)})
              </span>
            </div>
          )}
        </>
      )}
    </div>
  );
}
