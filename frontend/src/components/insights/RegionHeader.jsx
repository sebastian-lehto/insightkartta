export default function RegionHeader({ region }) {
  return (
    <div className="region-header">
      <h1>{region?.name}</h1>
    </div>
  );
}
