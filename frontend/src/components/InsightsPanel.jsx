function InsightsPanel({ analysis }) {
  if (!analysis) return null;

  const insights = Object.values(analysis).flatMap(
    (result) => result.insights ?? []
  );

  if (insights.length === 0) return null;

  return (
    <div className="insights-panel">
      <div className="insights-panel-label">National trend</div>
      {insights.map((text, i) => (
        <p key={i} className="insights-panel-text">{text}</p>
      ))}
    </div>
  );
}

export default InsightsPanel;