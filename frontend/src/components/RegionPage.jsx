import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchRegionInsights, fetchRegionPostalCodes, fetchElectionCorrelations } from "../api";

import RegionHeader from "./insights/RegionHeader";
import IndicatorGrid from "./insights/IndicatorGrid";
import PartyChangeChart from "./insights/PartyChangeChart";
import CorrelationTable from "./insights/CorrelationTable";
import PostalCodeComparison from "./PostalCodeComparison";
import { ElectionInsightsSkeleton } from "./LoadingSkeletons";

export default function RegionPage() {
  const { regionCode } = useParams();
  const [insight, setInsight] = useState(null);
  const [error, setError] = useState(null);
  const [correlations, setCorrelations] = useState(null);
  const [correlationsLoading, setCorrelationsLoading] = useState(true);
  const [postalCodes, setPostalCodes] = useState({ datasets: [], postal_codes: [], years: [] });
  const [postalCodesLoading, setPostalCodesLoading] = useState(true);
  const [postalCodesError, setPostalCodesError] = useState(false);
  const [periodIndex, setPeriodIndex] = useState(0);
  const [activeView, setActiveView] = useState("postal");

  useEffect(() => {
    // Resetting loading/error state before the fetch for the new regionCode
    // is the standard "reset, then fetch" data-fetching effect pattern, not
    // the cascading-render anti-pattern this rule otherwise targets.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setInsight(null);
    setError(null);
    setPeriodIndex(0);
    setActiveView("postal");
    fetchRegionInsights(regionCode)
      .then((res) => setInsight(res.data))
      .catch(() => setError("Could not load insights for this region."));
  }, [regionCode]);

  useEffect(() => {
    fetchElectionCorrelations()
      .then((res) => setCorrelations(res.data))
      .catch(() => setCorrelations(null))
      .finally(() => setCorrelationsLoading(false));
  }, []);

  useEffect(() => {
    let cancelled = false;
    // Keep the previous region's rows out of the next region's loading preview.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPostalCodesLoading(true);
    setPostalCodesError(false);
    setPostalCodes({ datasets: [], postal_codes: [], years: [] });
    fetchRegionPostalCodes(regionCode)
      .then((res) => {
        if (!cancelled) {
          setPostalCodes(res.data || { datasets: [], postal_codes: [], years: [] });
          setPostalCodesError(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setPostalCodes({ datasets: [], postal_codes: [], years: [] });
          setPostalCodesError(true);
        }
      })
      .finally(() => {
        if (!cancelled) setPostalCodesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [regionCode]);

  if (error) {
    return (
      <div className="region-page">
        <Link to="/" className="back-link">← Back to map</Link>
        <p style={{ color: "var(--text)", marginTop: "2rem" }}>{error}</p>
      </div>
    );
  }

  const periods = insight?.periods ?? [];
  const currentPeriod = periods[periodIndex] ?? periods[0];
  const regionName = insight?.region?.name ?? regionCode;

  return (
    <div className="region-page">
      <Link to="/" className="back-link">← Back to map</Link>

      <RegionHeader
        region={insight?.region ?? { name: regionName }}
        periods={activeView === "elections" ? periods : []}
        selectedIndex={periodIndex}
        onSelectPeriod={setPeriodIndex}
      />

      <div className="region-view-tabs" role="tablist" aria-label="Region analysis view">
        <button
          type="button"
          role="tab"
          aria-selected={activeView === "postal"}
          className={`region-view-tab${activeView === "postal" ? " region-view-tab--active" : ""}`}
          onClick={() => setActiveView("postal")}
        >
          Postal-code analysis
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeView === "elections"}
          className={`region-view-tab${activeView === "elections" ? " region-view-tab--active" : ""}`}
          onClick={() => setActiveView("elections")}
        >
          Election insights
        </button>
      </div>

      {activeView === "postal" ? (
        <PostalCodeComparison
          regionName={regionName}
          datasets={postalCodes.datasets}
          postalCodes={postalCodes.postal_codes}
          years={postalCodes.years}
          selectedYear={postalCodes.year}
          loading={postalCodesLoading}
          error={postalCodesError}
        />
      ) : (
        insight ? <>
          <IndicatorGrid
            indicators={currentPeriod?.indicators}
            relationships={currentPeriod?.indicator_relationships}
          />
          <PartyChangeChart
            partyChanges={currentPeriod?.party_changes}
            electionSummary={currentPeriod?.election_summary}
          />
          <CorrelationTable
            correlationsData={correlations}
            selectedEndYear={currentPeriod?.election_summary?.latest_year}
            loading={correlationsLoading}
          />
        </> : <ElectionInsightsSkeleton regionName={regionName} />
      )}
    </div>
  );
}