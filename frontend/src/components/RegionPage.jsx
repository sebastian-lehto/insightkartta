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

  useEffect(() => {
    setInsight(null);
    setError(null);
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

  return (
    <div className="region-page">
      <Link to="/" className="back-link">← Back to map</Link>

      <RegionHeader
        region={insight.region}
        electionSummary={insight.election_summary}
      />

      <IndicatorGrid
        indicators={insight.indicators}
        relationships={insight.indicator_relationships}
      />

      <PartyChangeChart
        partyChanges={insight.party_changes}
        electionSummary={insight.election_summary}
      />

      <CorrelationTable correlationsData={correlations} />
    </div>
  );
}