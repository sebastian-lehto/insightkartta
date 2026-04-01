export const getColor = (value) => {
  if (value == null) return "#ccc";
  if (value > 15) return "#800026";
  if (value > 10) return "#BD0026";
  if (value > 8) return "#E31A1C";
  if (value > 6) return "#FC4E2A";
  if (value > 4) return "#FD8D3C";
  return "#FEB24C";
};