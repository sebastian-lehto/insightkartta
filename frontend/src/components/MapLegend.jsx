import { getColor } from "../utils/colorScale";

function MapLegend({ bins, unit }) {
  const legendItems = [
    { label: `> ${bins[4]}${unit || '%'}`, value: 16 },
    { label: `${bins[3]} – ${bins[4]}${unit || '%'}`, value: 12 },
    { label: `${bins[2]} – ${bins[3]}${unit || '%'}`, value: 9 },
    { label: `${bins[1]} – ${bins[2]}${unit || '%'}`, value: 7 },
    { label: `${bins[0]} – ${bins[1]}${unit || '%'}`, value: 5 },
    { label: `< ${bins[0]}${unit || '%'}`, value: 2 },
    { label: "No data", value: null },
  ];

  return (
    <div style={styles.container}>
      <h4 style={{ margin: "0 0 8px 0" }}>Legend</h4>
      {legendItems.map((item, idx) => (
        <div key={idx} style={styles.row}>
          <span
            style={{
              ...styles.colorBox,
              backgroundColor: getColor(item.value),
            }}
          />
          <span>{item.label}</span>
        </div>
      ))}
    </div>
  );
}

const styles = {
  container: {
    position: "absolute",
    bottom: "20px",
    right: "20px",
    background: "white",
    padding: "10px 12px",
    borderRadius: "8px",
    boxShadow: "0 0 6px rgba(0,0,0,0.2)",
    fontSize: "14px",
    zIndex: 1000,
  },
  row: {
    display: "flex",
    alignItems: "center",
    marginBottom: "4px",
  },
  colorBox: {
    width: "18px",
    height: "18px",
    marginRight: "8px",
    borderRadius: "3px",
  },
};

export default MapLegend;