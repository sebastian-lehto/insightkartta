export default function RegionHeader({ region, electionSummary }) {
  const period =
    electionSummary?.previous_year && electionSummary?.latest_year
      ? `${electionSummary.previous_year} → ${electionSummary.latest_year}`
      : null;

  return (
    <div className="region-header">
      <h1>{region?.name}</h1>
      {period && (
        <p className="region-header-subtitle">
          Municipal election comparison: {period}
        </p>
      )}
    </div>
  );
}
