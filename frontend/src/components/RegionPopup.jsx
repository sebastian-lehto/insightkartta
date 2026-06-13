import { Link } from "react-router-dom";

export default function RegionPopup({ region }) {
  return (
    <div>
      <h3>{region.name}</h3>
      <Link to={`/municipality/${region.region_code}`}>View insights</Link>
    </div>
  );
}
