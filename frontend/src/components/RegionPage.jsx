import { useEffect, useState } from "react";
import { useParams } from 'react-router-dom';
import axios from "axios";

import RegionHeader from "../components/insights/RegionHeader";
import IndicatorGrid from "../components/insights/IndicatorGrid";
import PartyChangeChart from "../components/insights/PartyChangeChart";

export default function RegionPage() {
  const { regionCode } = useParams();

  const [insight, setInsight] = useState(null);

  useEffect(() => {
    axios
      .get(`http://127.0.0.1:8000/regions/${regionCode}/insights`)
      .then((response) => setInsight(response.data));
  }, [regionCode]);

  if (!insight) {
    return <div>Loading...</div>;
  }

  return (
    <div className="region-page">
      <RegionHeader region={insight.region} />

      <IndicatorGrid indicators={insight.indicators} />

      <PartyChangeChart
        partyChanges={insight.party_changes}
      />
    </div>
  );
}