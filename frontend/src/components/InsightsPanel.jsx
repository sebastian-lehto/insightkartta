function InsightsPanel({ analysis }) {
  if (!analysis) return null;

  const analysisEntries = Object.entries(analysis);

  if (analysisEntries.length === 0) return null;

  return (
    <div style={{ marginBottom: "2rem" }}>
      <h2>Insights</h2>

      {analysisEntries.map(([analysisName, analysisResult]) => (
        <div key={analysisName} style={{ marginBottom: "1rem" }}>
          {analysisResult.insights?.map((insight, index) => (
            <p key={`${analysisName}-${index}`}>{insight}</p>
          ))}
        </div>
      ))}
    </div>
  );
}

export default InsightsPanel;