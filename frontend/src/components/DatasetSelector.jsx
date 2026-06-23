import { useRef, useEffect } from "react";

function DatasetSelector({ datasets, selectedDataset, onChange }) {
  const tabsRef = useRef(null);

  useEffect(() => {
    const el = tabsRef.current;
    if (!el) return;

    // Redirect vertical wheel to horizontal scroll
    const onWheel = (e) => {
      if (e.deltaX !== 0) return;
      e.preventDefault();
      el.scrollLeft += e.deltaY;
    };

    el.addEventListener("wheel", onWheel, { passive: false });

    return () => {
      el.removeEventListener("wheel", onWheel);
    };
  }, []);

  return (
    <div className="dataset-tabs" ref={tabsRef}>
      {datasets.map((dataset) => (
        <button
          key={dataset.name}
          className={
            "dataset-tab" +
            (selectedDataset === dataset.name ? " dataset-tab--active" : "")
          }
          onClick={() => onChange(dataset.name)}
        >
          {dataset.label}
        </button>
      ))}
    </div>
  );
}

export default DatasetSelector;
