import { useRef, useEffect } from "react";

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
  const wrapperRef = useRef(null);

  useEffect(() => {
    const el = wrapperRef.current;
    if (!el) return;

    const onWheel = (e) => {
      if (e.deltaY === 0) return;
      e.preventDefault();
      el.scrollLeft += e.deltaY;
    };

    let isDragging = false;
    let startX = 0;
    let startScrollLeft = 0;

    const onMouseDown = (e) => {
      isDragging = true;
      startX = e.pageX;
      startScrollLeft = el.scrollLeft;
      el.classList.add("corr-table-wrapper--dragging");
    };
    const onMouseMove = (e) => {
      if (!isDragging) return;
      e.preventDefault();
      el.scrollLeft = startScrollLeft - (e.pageX - startX);
    };
    const stopDragging = () => {
      isDragging = false;
      el.classList.remove("corr-table-wrapper--dragging");
    };

    el.addEventListener("wheel", onWheel, { passive: false });
    el.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", stopDragging);

    return () => {
      el.removeEventListener("wheel", onWheel);
      el.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", stopDragging);
    };
  }, []);

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

      <div className="corr-table-wrapper" ref={wrapperRef}>
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
