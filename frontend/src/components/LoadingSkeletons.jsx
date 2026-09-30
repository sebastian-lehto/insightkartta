function SkeletonBlock({ className = "", style }) {
  return <span className={`ui-skeleton ${className}`} style={style} aria-hidden="true" />;
}

export function DashboardSkeleton({ message }) {
  return (
    <div className="dashboard-loading" aria-busy="true" aria-label="Loading dashboard">
      {message && <p className="dashboard-loading-message">{message}</p>}
      <div className="dashboard-columns dashboard-columns--skeleton">
        <div className="dashboard-left">
          <section className="insights-panel dashboard-insights-skeleton">
            <SkeletonBlock className="skeleton-heading" />
            <SkeletonBlock className="skeleton-copy" />
            <SkeletonBlock className="skeleton-copy skeleton-copy--short" />
          </section>
          <section className="dashboard-chart-skeleton">
            <SkeletonBlock className="skeleton-heading" />
            <div className="dashboard-chart-skeleton-plot" aria-hidden="true">
              {[40, 64, 50, 82, 58, 72, 46, 68, 90, 62, 76, 54].map((height, index) => (
                <SkeletonBlock className="dashboard-chart-skeleton-bar" key={index} style={{ height: `${height}%` }} />
              ))}
            </div>
            <div className="dashboard-chart-skeleton-axis">
              <SkeletonBlock />
              <SkeletonBlock />
              <SkeletonBlock />
              <SkeletonBlock />
            </div>
          </section>
        </div>
        <div className="dashboard-right">
          <section className="dashboard-slider-skeleton">
            <SkeletonBlock className="skeleton-heading" />
            <SkeletonBlock className="skeleton-slider-track" />
            <div><SkeletonBlock /><SkeletonBlock /></div>
          </section>
          <div className="dashboard-map-skeleton" aria-hidden="true">
            <span className="dashboard-map-shape dashboard-map-shape--one" />
            <span className="dashboard-map-shape dashboard-map-shape--two" />
            <span className="dashboard-map-shape dashboard-map-shape--three" />
            <SkeletonBlock className="dashboard-map-legend" />
          </div>
        </div>
      </div>
      <span className="visually-hidden" role="status">Loading dashboard content</span>
    </div>
  );
}

export function ElectionInsightsSkeleton({ regionName }) {
  return (
    <div className="election-insights-skeleton" aria-busy="true" aria-label={`Loading election insights for ${regionName}`}>
      <section className="insight-section">
        <SkeletonBlock className="skeleton-heading skeleton-heading--wide" />
        <div className="election-cards-skeleton" aria-hidden="true">
          {[0, 1, 2, 3].map((item) => (
            <div className="election-card-skeleton" key={item}>
              <SkeletonBlock className="skeleton-copy skeleton-copy--short" />
              <SkeletonBlock className="election-card-value" />
              <SkeletonBlock className="skeleton-copy" />
            </div>
          ))}
        </div>
      </section>
      <section className="insight-section">
        <SkeletonBlock className="skeleton-heading" />
        <div className="election-chart-skeleton" aria-hidden="true">
          <div className="election-chart-zero-line" />
          {[46, 69, 38, 78, 56, 86, 32, 62, 48, 74, 40, 57].map((height, index) => (
            <SkeletonBlock className={`election-chart-bar election-chart-bar--${index % 3}`} style={{ height: `${height}%` }} key={index} />
          ))}
        </div>
      </section>
      <section className="insight-section">
        <SkeletonBlock className="skeleton-heading skeleton-heading--wide" />
        <div className="correlation-skeleton" aria-hidden="true">
          {Array.from({ length: 6 }, (_, row) => (
            <div className="correlation-skeleton-row" key={row}>
              {Array.from({ length: 6 }, (_, column) => (
                <SkeletonBlock className={column === 0 ? "correlation-skeleton-cell correlation-skeleton-cell--label" : "correlation-skeleton-cell"} key={column} />
              ))}
            </div>
          ))}
        </div>
      </section>
      <span className="visually-hidden" role="status">Loading election insights for {regionName}</span>
    </div>
  );
}

export function CorrelationTableSkeleton() {
  return (
    <section className="insight-section correlation-loading-skeleton" aria-busy="true" aria-label="Loading election correlations">
      <SkeletonBlock className="skeleton-heading skeleton-heading--wide" />
      <div className="correlation-skeleton" aria-hidden="true">
        {Array.from({ length: 5 }, (_, row) => (
          <div className="correlation-skeleton-row" key={row}>
            {Array.from({ length: 6 }, (_, column) => <SkeletonBlock className="correlation-skeleton-cell" key={column} />)}
          </div>
        ))}
      </div>
    </section>
  );
}
