function RegionSelector({ regions, selectedRegion, onChange }) {
  return (
    <>
      <label>Select Region: </label>
      <select
        value={selectedRegion}
        onChange={(e) => onChange(e.target.value)}
      >
        {regions.map((region) => (
          <option key={region} value={region}>
            {region}
          </option>
        ))}
      </select>
    </>
  );
}

export default RegionSelector;