export function formatPostalCodeValue(value, unit) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }

  const numericValue = Number(value);

  if (unit === "%") {
    return `${numericValue.toFixed(1)}%`;
  }

  if (unit === "years" || unit === "persons/household") {
    return new Intl.NumberFormat("fi-FI", {
      maximumFractionDigits: 1,
    }).format(numericValue);
  }

  if (unit === "EUR") {
    return `${new Intl.NumberFormat("fi-FI", {
      maximumFractionDigits: 0,
    }).format(numericValue)} €`;
  }

  return new Intl.NumberFormat("fi-FI", {
    maximumFractionDigits: 0,
  }).format(numericValue);
}