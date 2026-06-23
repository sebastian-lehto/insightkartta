const INDICATOR_LABELS = {
  unemployment: "Unemployment",
  education_upper_secondary: "Upper secondary edu.",
  education_tertiary: "Tertiary edu.",
  population: "Population",
};

const CLASSIFICATION_META = {
  none:              { label: "no correlation",      className: "corr-none" },
  weak_positive:     { label: "weak +",              className: "corr-weak-pos" },
  weak_negative:     { label: "weak −",              className: "corr-weak-neg" },
  moderate_positive: { label: "moderate +",          className: "corr-mod-pos" },
  moderate_negative: { label: "moderate −",          className: "corr-mod-neg" },
  strong_positive:   { label: "strong +",            className: "corr-strong-pos" },
  strong_negative:   { label: "strong −",            className: "corr-strong-neg" },
};

export default function CorrelationTable({ correlationsData }) {
  if (!correlationsData) return null;

  const years = Object.keys(correlationsData).sort().reverse();
  if (years.length === 0) return null;

  const latestYear = years[0];
  const entry = correlationsData[latestYear];
  const { election_period, correlations } = entry;

  const indicatorKeys = Object.keys(correlations);
  if (indicatorKeys.length === 0) return null;

  const allParties = [
    ...new Set(
      indicatorKeys.flatMap((ind) => Object.keys(correlations[ind]))
    ),
  ].sort();

  return (
    <section className="insight-section">
      <h2>
        National indicator–vote correlations,{" "}
        {election_period.start} → {election_period.end}
      </h2>
      <p className="corr-description">
        Pearson correlation across {getN(correlations)} municipalities between
        each indicator's change and each party's vote share shift. Weak or absent
        correlations are a valid finding.
      </p>

      <div className="corr-table-wrapper">
        <table className="corr-table">
          <thead>
            <tr>
              <th className="corr-th corr-th-indicator">Indicator</th>
              {allParties.map((code) => {
                const name = getPartyName(correlations, indicatorKeys, code);
                return (
                  <th key={code} className="corr-th" title={name}>
                    {code}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {indicatorKeys.map((ind) => (
              <tr key={ind}>
                <td className="corr-td-indicator">
                  {INDICATOR_LABELS[ind] ?? ind}
                </td>
                {allParties.map((code) => {
                  const cell = correlations[ind]?.[code];
                  if (!cell) {
                    return <td key={code} className="corr-td corr-none">—</td>;
                  }
                  const meta = CLASSIFICATION_META[cell.classification] ?? {
                    label: cell.classification,
                    className: "corr-none",
                  };
                  return (
                    <td
                      key={code}
                      className={`corr-td ${meta.className}`}
                      title={`r = ${cell.pearson_r} (n=${cell.n})`}
                    >
                      {meta.label}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="corr-note">
        Hover a cell for the Pearson r value and municipality count.
      </p>
    </section>
  );
}

function getN(correlations) {
  const firstInd = Object.values(correlations)[0];
  if (!firstInd) return "–";
  const firstParty = Object.values(firstInd)[0];
  return firstParty?.n ?? "–";
}

function getPartyName(correlations, indicatorKeys, partyCode) {
  for (const ind of indicatorKeys) {
    const cell = correlations[ind]?.[partyCode];
    if (cell?.party_name) return cell.party_name;
  }
  return partyCode;
}
