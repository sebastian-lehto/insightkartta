import { computeInsights } from "../utils/insights";

const NATIONAL_REGION_NAME = "KOKO MAA";

function ArrowUpIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M4 12L12 4" strokeLinecap="round" />
      <path d="M6 4h6v6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ArrowDownIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M4 4L12 12" strokeLinecap="round" />
      <path d="M12 6v6H6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ArrowFlatIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M3 8h10" strokeLinecap="round" />
      <path d="M9 4l4 4-4 4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function PeakIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M2 13l4.2-8 2.3 3.6L10.5 5 14 13" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function LowIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M2 4.5l4.2 7.5 2.3-3.2L10.5 11 14 4.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ShareIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6">
      <circle cx="8" cy="8" r="6" />
      <path d="M8 2v6l4.2 4.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function DotIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="currentColor">
      <circle cx="8" cy="8" r="3" />
    </svg>
  );
}

const DIRECTIONAL_ICONS = { up: ArrowUpIcon, down: ArrowDownIcon, flat: ArrowFlatIcon };

function getIcon(insight) {
  if (insight.type === "trend" || insight.type === "compare") {
    return DIRECTIONAL_ICONS[insight.direction] ?? ArrowFlatIcon;
  }
  if (insight.type === "peak") return PeakIcon;
  if (insight.type === "low") return LowIcon;
  if (insight.type === "share") return ShareIcon;
  return DotIcon;
}

function InsightsPanel({ regionData, allData, label, unit, regionName }) {
  if (!regionData || regionData.length === 0) return null;

  const insights = computeInsights({ regionData, allData, label, unit, regionName });

  if (insights.length === 0) return null;

  const displayRegion = regionName === NATIONAL_REGION_NAME ? "Finland" : regionName;

  return (
    <div className="insights-panel">
      <div className="insights-panel-header">
        <span className="insights-panel-eyebrow">Insights for</span>
        <h3 className="insights-panel-region">{displayRegion}</h3>
        {label && <span className="insights-panel-dataset">{label}</span>}
      </div>

      <ul className="insights-panel-list">
        {insights.map((insight, i) => {
          const Icon = getIcon(insight);
          return (
            <li key={i} className={`insights-panel-row insights-panel-row--${insight.type}`}>
              <span className={`insights-panel-icon insights-panel-icon--${insight.direction ?? insight.type}`}>
                <Icon />
              </span>
              <p className="insights-panel-text">{insight.text}</p>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default InsightsPanel;
