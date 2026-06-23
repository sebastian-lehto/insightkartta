import { useRef, useEffect } from "react";

function DatasetSelector({ datasets, selectedDataset, onChange }) {
  const tabsRef = useRef(null);

  useEffect(() => {
    const el = tabsRef.current;
    if (!el) return;

    let startX = 0;
    let scrollLeft = 0;
    let dragging = false;

    const onPointerDown = (e) => {
      if (e.button !== 0) return;
      startX = e.clientX;
      scrollLeft = el.scrollLeft;
      dragging = false;
      el.setPointerCapture(e.pointerId);
      el.style.cursor = "grabbing";
    };

    const onPointerMove = (e) => {
      if (!el.hasPointerCapture(e.pointerId)) return;
      const dx = e.clientX - startX;
      if (Math.abs(dx) > 4) dragging = true;
      if (dragging) el.scrollLeft = scrollLeft - dx;
    };

    const onPointerUp = (e) => {
      el.releasePointerCapture(e.pointerId);
      el.style.cursor = "";
    };

    // Capture-phase click suppression after a drag
    const onCapturingClick = (e) => {
      if (dragging) {
        dragging = false;
        e.stopPropagation();
        e.preventDefault();
      }
    };

    // Redirect vertical wheel to horizontal scroll
    const onWheel = (e) => {
      if (e.deltaX !== 0) return;
      e.preventDefault();
      el.scrollLeft += e.deltaY;
    };

    el.addEventListener("pointerdown", onPointerDown);
    el.addEventListener("pointermove", onPointerMove);
    el.addEventListener("pointerup", onPointerUp);
    el.addEventListener("click", onCapturingClick, true);
    el.addEventListener("wheel", onWheel, { passive: false });

    return () => {
      el.removeEventListener("pointerdown", onPointerDown);
      el.removeEventListener("pointermove", onPointerMove);
      el.removeEventListener("pointerup", onPointerUp);
      el.removeEventListener("click", onCapturingClick, true);
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
