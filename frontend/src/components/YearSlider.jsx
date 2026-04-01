function YearSlider({ year, minYear, maxYear, onChange }) {
  return (
    <div style={{ marginBottom: "2rem" }}>
      <h2>Year: {year}</h2>
      <input
        type="range"
        min={minYear}
        max={maxYear}
        value={year}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  );
}

export default YearSlider;