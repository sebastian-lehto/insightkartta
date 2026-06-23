import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchRegionInsights, fetchElectionCorrelations } from "../api";

import RegionHeader from "./insights/RegionHeader";
import IndicatorGrid from "./insights/IndicatorGrid";
import PartyChangeChart from "./insights/PartyChangeChart";
import CorrelationTable from "./insights/CorrelationTable";

export default function RegionPage() {
  const { regionCode } = useParams();
  const [insight, setInsight] = useState(null);
  const [error, setError] = useState(null);
  const [correlations, setCorrelations] = useState(null);
  const [periodIndex, setPeriodIndex] = useState(0);

  useEffect(() => {
    setInsight(null);
    setError(null);
    setPeriodIndex(0);
    fetchRegionInsights(regionCode)
      .then((res) => setInsight(res.data))
      .catch(() => setError("Could not load insights for this region."));
  }, [regionCode]);

  useEffect(() => {
    fetchElectionCorrelations()
      .then((res) => setCorrelations(res.data))
      .catch(() => setCorrelations(null));
  }, []);

  if (error) {
    return (
      <div className="region-page">
        <Link to="/" className="back-link">← Back to map</Link>
        <p style={{ color: "var(--text)", marginTop: "2rem" }}>{error}</p>
      </div>
    );
  }

  if (!insight) {
    return (
      <div className="region-page">
        <Link to="/" className="back-link">← Back to map</Link>
        <p style={{ color: "var(--text)", marginTop: "2rem" }}>Loading…</p>
      </div>
    );
  }

  const periods = insight.periods ?? [];
  const currentPeriod = periods[periodIndex] ?? periods[0];

  return (
    <div className="region-page">
      <Link to="/" className="back-link">← Back to map</Link>

      <RegionHeader
        region={insight.region}
        periods={periods}
        selectedIndex={periodIndex}
        onSelectPeriod={setPeriodIndex}
      />

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
      />
    </div>
  );
}