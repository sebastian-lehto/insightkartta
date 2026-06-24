export default function RegionHeader({
  region,
  periods = [],
  selectedIndex = 0,
  onSelectPeriod,
}) {
  return (
    <div className="region-header">
      <h1>{region?.name}</h1>

      {periods.length > 0 && (
        <div className="region-period-switcher">
          <span className="region-period-eyebrow">Viewing election period</span>
          <div className="region-period-tabs" role="tablist" aria-label="Election period">
            {periods.map((p, i) => {
              const { previous_year, latest_year } = p.election_summary ?? {};
              const isActive = i === selectedIndex;
              return (
                <button
                  key={`${previous_year}-${latest_year}`}
                  type="button"
                  role="tab"
                  aria-selected={isActive}
                  className={`region-period-tab${isActive ? " region-period-tab--active" : ""}`}
                  onClick={() => onSelectPeriod?.(i)}
                >
                  {previous_year} → {latest_year}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
