import { useMemo, useState } from "react";
import PostalCodeMap from "./PostalCodeMap";
import { formatPostalCodeValue } from "../utils/formatPostalCodeValue";
import { normalizePostalCode } from "../utils/postalCodeMap";

function PostalComparisonSkeleton({ regionName }) {
  return (
    <section className="postal-code-comparison postal-code-comparison--loading" aria-busy="true" aria-label="Loading postal-code analysis">
      <div className="postal-code-comparison-header">
        <div>
          <span className="postal-code-comparison-eyebrow">Postal-code analysis</span>
          <h2>{regionName}</h2>
        </div>
        <div className="postal-skeleton-control">
          <span className="postal-skeleton postal-skeleton-label" />
          <span className="postal-skeleton postal-skeleton-select" />
        </div>
      </div>

      <div className="postal-insight-cards" aria-hidden="true">
        {[0, 1, 2].map((item) => (
          <div className="postal-insight-card postal-insight-card--skeleton" key={item}>
            <span className="postal-skeleton postal-skeleton-short" />
            <span className="postal-skeleton postal-skeleton-value" />
            <span className="postal-skeleton postal-skeleton-caption" />
          </div>
        ))}
      </div>

      <div className="postal-year-control postal-year-control--skeleton" aria-hidden="true">
        <div className="postal-year-label-row">
          <span className="postal-skeleton postal-skeleton-label" />
          <span className="postal-skeleton postal-skeleton-year" />
        </div>
        <span className="postal-skeleton postal-skeleton-slider" />
        <div className="postal-year-bounds">
          <span className="postal-skeleton postal-skeleton-bound" />
          <span className="postal-skeleton postal-skeleton-bound" />
        </div>
      </div>

      <div className="postal-code-comparison-content">
        <div className="postal-code-map-column">
          <h3 className="postal-code-map-title">Postal-area map</h3>
          <div className="postal-map-skeleton" aria-hidden="true">
            <span className="postal-map-skeleton-region postal-map-skeleton-region--one" />
            <span className="postal-map-skeleton-region postal-map-skeleton-region--two" />
            <span className="postal-map-skeleton-region postal-map-skeleton-region--three" />
            <span className="postal-map-skeleton-legend postal-skeleton" />
          </div>
        </div>
        <div className="postal-table-skeleton" aria-hidden="true">
          <div className="postal-table-skeleton-toolbar">
            <span className="postal-skeleton postal-skeleton-label" />
            <span className="postal-skeleton postal-skeleton-select" />
          </div>
          <div className="postal-table-skeleton-heading">
            <span className="postal-skeleton" />
            <span className="postal-skeleton" />
            <span className="postal-skeleton" />
          </div>
          {Array.from({ length: 8 }, (_, index) => (
            <div className="postal-table-skeleton-row" key={index}>
              <span className="postal-skeleton" />
              <span className="postal-skeleton" />
              <span className="postal-skeleton" />
            </div>
          ))}
        </div>
      </div>
      <span className="visually-hidden" role="status">Loading postal-code analysis for {regionName}</span>
    </section>
  );
}

export default function PostalCodeComparison({ regionName, datasets, postalCodes, loading = false, error = false }) {
  const [mapMetric, setMapMetric] = useState("");
  const [sortMetric, setSortMetric] = useState("");
  const [sortDirection, setSortDirection] = useState("desc");
  const [activePostalCode, setActivePostalCode] = useState(null);
  const [viewYear, setViewYear] = useState(null);

  const years = useMemo(() => {
    const available = new Set();
    postalCodes.forEach((row) => Object.keys(row.history ?? {}).forEach((year) => available.add(Number(year))));
    return [...available].sort((a, b) => a - b);
  }, [postalCodes]);
  const activeYear = years.includes(viewYear) ? viewYear : years.at(-1);

  const yearRows = useMemo(() => postalCodes.map((row) => ({
    ...row,
    ...(row.history?.[String(activeYear)] ?? {}),
  })), [activeYear, postalCodes]);

  const activeMetric = datasets.some((dataset) => dataset.name === mapMetric)
    ? mapMetric
    : datasets[0]?.name ?? "";
  const activeDataset = datasets.find((dataset) => dataset.name === activeMetric);
  const activeSortMetric = datasets.some((dataset) => dataset.name === sortMetric)
    ? sortMetric
    : datasets[0]?.name ?? "";

  const sortedRows = useMemo(() => {
    if (!yearRows.length) {
      return [];
    }

    const sorted = [...yearRows].sort((a, b) => {
      const left = Number(a[activeSortMetric] ?? 0);
      const right = Number(b[activeSortMetric] ?? 0);
      return sortDirection === "desc" ? right - left : left - right;
    });

    return sorted;
  }, [activeSortMetric, sortDirection, yearRows]);

  if (loading) {
    return <PostalComparisonSkeleton regionName={regionName} />;
  }

  if (error) {
    return (
      <section className="postal-code-comparison postal-code-empty-state" role="alert">
        <span className="postal-code-comparison-eyebrow">Postal-code analysis</span>
        <h2>{regionName}</h2>
        <p>Postal-code data is temporarily unavailable. Please try again later.</p>
      </section>
    );
  }

  if (!datasets.length || !postalCodes.length || !years.length) {
    return (
      <section className="postal-code-comparison postal-code-empty-state" role="status">
        <span className="postal-code-comparison-eyebrow">Postal-code analysis</span>
        <h2>{regionName}</h2>
        <p>No postal-code data is available for this region yet.</p>
      </section>
    );
  }

  const summaryCards = datasets
    .filter((dataset) => dataset.summary)
    .map((dataset) => {
      const values = yearRows
        .map((row) => row[dataset.name])
        .filter((value) => value !== null && value !== undefined && value !== "")
        .map(Number)
        .filter(Number.isFinite);
      let value = null;
      if (dataset.summary === "total" && values.length) {
        value = values.reduce((sum, current) => sum + current, 0);
      } else if (dataset.summary === "median" && values.length) {
        const ordered = [...values].sort((a, b) => a - b);
        const middle = Math.floor(ordered.length / 2);
        value = ordered.length % 2 ? ordered[middle] : (ordered[middle - 1] + ordered[middle]) / 2;
      }
      return { ...dataset, value };
    });

  return (
    <section className="postal-code-comparison">
      <div className="postal-code-comparison-header">
        <div>
          <span className="postal-code-comparison-eyebrow">Postal-code analysis</span>
          <h2>{regionName}</h2>
        </div>

        <div className="postal-code-comparison-controls">
          <label htmlFor="postal-map-metric" className="postal-code-sort-label">Map metric</label>
          <select
            id="postal-map-metric"
            className="postal-code-sort-select"
            value={activeMetric}
            onChange={(event) => setMapMetric(event.target.value)}
          >
            {datasets.map((dataset) => (
              <option key={dataset.name} value={dataset.name}>
                {dataset.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {summaryCards.length > 0 && (
        <div className="postal-insight-cards">
          {summaryCards.map((card) => (
            <article className="postal-insight-card" key={card.name}>
              <span>{card.label}</span>
              <strong>{formatPostalCodeValue(card.value, card.unit)}</strong>
              <small>{activeYear}</small>
            </article>
          ))}
          <article className="postal-insight-card postal-insight-card--count">
            <span>Postal areas</span>
            <strong>{yearRows.length}</strong>
            <small>in {regionName}</small>
          </article>
        </div>
      )}

      <div className="postal-year-control">
        <div className="postal-year-label-row">
          <label htmlFor="postal-year-slider">Year</label>
          <output htmlFor="postal-year-slider">{activeYear}</output>
        </div>
        <input
          id="postal-year-slider"
          type="range"
          min="0"
          max={years.length - 1}
          step="1"
          value={Math.max(0, years.indexOf(activeYear))}
          onChange={(event) => setViewYear(years[Number(event.target.value)])}
          aria-valuetext={String(activeYear)}
        />
        <div className="postal-year-bounds"><span>{years[0]}</span><span>{years.at(-1)}</span></div>
      </div>

      <div className="postal-code-comparison-content">
        <div className="postal-code-map-column">
          <h3 className="postal-code-map-title">Postal-area map</h3>
          <PostalCodeMap
            regionName={regionName}
            dataset={activeDataset}
            metric={activeMetric}
            postalCodes={yearRows}
            activePostalCode={activePostalCode}
            onPostalCodeHover={setActivePostalCode}
          />
        </div>

        <div className="postal-code-comparison-table-wrap">
          <div className="postal-table-controls">
            <label htmlFor="postal-table-sort">Sort table</label>
            <select
              id="postal-table-sort"
              className="postal-code-sort-select"
              value={activeSortMetric}
              onChange={(event) => setSortMetric(event.target.value)}
            >
              {datasets.map((dataset) => <option key={dataset.name} value={dataset.name}>{dataset.label}</option>)}
            </select>
            <button
              type="button"
              className="postal-code-sort-button"
              onClick={() => setSortDirection((prev) => (prev === "desc" ? "asc" : "desc"))}
            >
              {sortDirection === "desc" ? "High to low" : "Low to high"}
            </button>
          </div>
          <table className="postal-code-comparison-table">
            <thead>
              <tr>
                <th>Postal code</th>
                {datasets.map((dataset) => (
                  <th key={dataset.name}>{dataset.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((row) => (
                <tr
                  key={row.postal_code}
                  className={
                    normalizePostalCode(activePostalCode) === normalizePostalCode(row.postal_code)
                      ? "is-active"
                      : ""
                  }
                  onMouseEnter={() => setActivePostalCode(row.postal_code)}
                  onMouseLeave={() => setActivePostalCode(null)}
                >
                  <td>{row.postal_code}</td>
                  {datasets.map((dataset) => (
                    <td key={`${row.postal_code}-${dataset.name}`}>
                      {formatPostalCodeValue(row[dataset.name], dataset.unit)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
