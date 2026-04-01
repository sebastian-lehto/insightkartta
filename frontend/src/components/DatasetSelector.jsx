function DatasetSelector({ datasets, selectedDataset, onChange }) {
  return (
    <div style={{ marginBottom: "1rem" }}>
      <label htmlFor="dataset-select">Select dataset: </label>
      <select
        id="dataset-select"
        value={selectedDataset}
        onChange={(e) => onChange(e.target.value)}
      >
        {datasets.map((dataset) => (
          <option key={dataset.name} value={dataset.name}>
            {dataset.label}
          </option>
        ))}
      </select>
    </div>
  );
}

export default DatasetSelector;