import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";

function RegionSearch() {
  const [regions, setRegions] = useState([]);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(0);
  const wrapperRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    fetch("/kunnat.geojson")
      .then((r) => r.json())
      .then((geo) => {
        const list = geo.features
          .map((f) => ({
            name: f.properties.Kunta ?? f.properties.name_fi,
            code: f.properties.Koodi,
          }))
          .filter((r) => r.name && r.code)
          .sort((a, b) => a.name.localeCompare(b.name, "fi"));
        setRegions(list);
      });
  }, []);

  const filtered =
    query.trim().length > 0
      ? regions
          .filter((r) => r.name.toLowerCase().includes(query.toLowerCase()))
          .slice(0, 10)
      : [];

  useEffect(() => {
    const onMouseDown = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onMouseDown);
    return () => document.removeEventListener("mousedown", onMouseDown);
  }, []);

  const handleChange = (e) => {
    setQuery(e.target.value);
    setOpen(true);
    setActiveIdx(0);
  };

  const handleKeyDown = (e) => {
    if (!open || filtered.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && filtered[activeIdx]) {
      wrapperRef.current
        ?.querySelector(".region-search-item--active .region-search-link")
        ?.click();
    } else if (e.key === "Escape") {
      setOpen(false);
      inputRef.current?.blur();
    }
  };

  const handleSelect = () => {
    setQuery("");
    setOpen(false);
  };

  return (
    <div className="region-search" ref={wrapperRef}>
      <div className="region-search-field">
        <svg
          className="region-search-icon"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          aria-hidden="true"
        >
          <circle cx="6.5" cy="6.5" r="4.5" />
          <path d="M11 11l2.5 2.5" strokeLinecap="round" />
        </svg>
        <input
          ref={inputRef}
          className="region-search-input"
          type="text"
          placeholder="Find region…"
          value={query}
          onChange={handleChange}
          onFocus={() => query.trim().length > 0 && setOpen(true)}
          onKeyDown={handleKeyDown}
          aria-label="Search for a region"
        />
      </div>
      {open && filtered.length > 0 && (
        <ul className="region-search-dropdown">
          {filtered.map((r, i) => (
            <li
              key={r.code}
              className={`region-search-item${i === activeIdx ? " region-search-item--active" : ""}`}
              onMouseEnter={() => setActiveIdx(i)}
            >
              <Link
                to={`/region/${r.code}`}
                className="region-search-link"
                onClick={handleSelect}
              >
                <span className="region-search-name">{r.name}</span>
                <span className="region-search-code">{r.code}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default RegionSearch;
