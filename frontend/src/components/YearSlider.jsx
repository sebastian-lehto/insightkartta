function YearSlider({ year, minYear, maxYear, onChange }) {
  return (
    <div className="year-slider">
      <div className="year-slider-header">
        <span className="year-slider-label">Year</span>
        <span className="year-slider-value">{year}</span>
      </div>
      <input
        className="year-slider-input"
        type="range"
        min={minYear}
        max={maxYear}
        value={year}
        onChange={(e) => onChange(Number(e.target.value))}
      />
      <div className="year-slider-bounds">
        <span>{minYear}</span>
        <span>{maxYear}</span>
      </div>
    </div>
  );
}

export default YearSlider;
