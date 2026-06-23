import { getColor } from "../utils/mapScale";

function MapLegend({ bins, unit }) {
  const u = unit || "";
  const legendItems = [
    { label: `> ${bins[4]}${u}`,              value: bins[4] + 1 },
    { label: `${bins[3]} – ${bins[4]}${u}`,   value: bins[3] + (bins[4] - bins[3]) / 2 },
    { label: `${bins[2]} – ${bins[3]}${u}`,   value: bins[2] + (bins[3] - bins[2]) / 2 },
    { label: `${bins[1]} – ${bins[2]}${u}`,   value: bins[1] + (bins[2] - bins[1]) / 2 },
    { label: `${bins[0]} – ${bins[1]}${u}`,   value: bins[0] + (bins[1] - bins[0]) / 2 },
    { label: `< ${bins[0]}${u}`,              value: bins[0] - 1 },
    { label: "No data",                        value: null },
  ];

  return (
    <div style={styles.container}>
      <h4 style={{ margin: "0 0 8px 0" }}>Legend</h4>
      {legendItems.map((item, idx) => (
        <div key={idx} style={styles.row}>
          <span
            style={{
              ...styles.colorBox,
              backgroundColor: getColor(item.value, bins),
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