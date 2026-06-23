const NATIONAL_REGION_NAME = "KOKO MAA";

function formatValue(value, unit) {
  if (value == null || Number.isNaN(value)) return "–";
  if (unit === "%") return `${value.toFixed(1)}%`;
  if (unit === "persons") return `${Math.round(value).toLocaleString("fi-FI")} persons`;
  return `${value}${unit ? ` ${unit}` : ""}`;
}

function formatDiff(diff, unit) {
  const abs = Math.abs(diff);
  if (unit === "%") return `${abs.toFixed(1)} percentage points`;
  if (unit === "persons") return `${Math.round(abs).toLocaleString("fi-FI")} persons`;
  return `${abs}${unit ? ` ${unit}` : ""}`;
}

function directionOf(delta) {
  if (delta > 0) return "up";
  if (delta < 0) return "down";
  return "flat";
}

/**
 * Computes insight entries for whatever region/time series is currently on
 * screen, so the numbers always match what the chart is showing. Each entry
 * carries a `type` (and sometimes a `direction`) so the UI can pick an icon
 * without re-deriving the meaning from the text.
 */
export function computeInsights({ regionData, allData, label, unit, regionName }) {
  const insights = [];
  if (!regionData || regionData.length === 0) return insights;

  const series = [...regionData].sort((a, b) => a.year - b.year);
  const first = series[0];
  const last = series[series.length - 1];
  const isNational = regionName === NATIONAL_REGION_NAME;

  if (series.length >= 2) {
    const delta = last.value - first.value;
    const direction = directionOf(delta);
    const verb = direction === "up" ? "increased" : direction === "down" ? "decreased" : "stayed flat";
    insights.push({
      type: "trend",
      direction,
      text: `${label} ${verb} from ${formatValue(first.value, unit)} in ${first.year} to ${formatValue(last.value, unit)} in ${last.year}.`,
    });

    const peak = series.reduce((a, b) => (b.value > a.value ? b : a));
    const trough = series.reduce((a, b) => (b.value < a.value ? b : a));

    insights.push({
      type: "peak",
      text: `${label} peaked at ${formatValue(peak.value, unit)} in ${peak.year}.`,
    });
    if (trough.year !== peak.year) {
      insights.push({
        type: "low",
        text: `${label} was lowest at ${formatValue(trough.value, unit)} in ${trough.year}.`,
      });
    }
  } else {
    insights.push({
      type: "single",
      text: `${label} was ${formatValue(first.value, unit)} in ${first.year}.`,
    });
  }

  if (!isNational && allData?.length) {
    const nationalForYear = allData.find(
      (d) => d.region_name === NATIONAL_REGION_NAME && d.year === last.year
    );
    if (nationalForYear) {
      if (unit === "%") {
        // Rates are directly comparable to the national rate.
        const diff = last.value - nationalForYear.value;
        if (Math.abs(diff) < 0.001) {
          insights.push({
            type: "compare",
            direction: "flat",
            text: `In ${last.year}, ${regionName} matched the national rate of ${formatValue(nationalForYear.value, unit)}.`,
          });
        } else {
          const comparison = diff > 0 ? "above" : "below";
          insights.push({
            type: "compare",
            direction: directionOf(diff),
            text: `In ${last.year}, ${regionName} was ${formatDiff(diff, unit)} ${comparison} the national rate (${formatValue(nationalForYear.value, unit)}).`,
          });
        }
      } else if (nationalForYear.value) {
        // National figure is a country-wide total, not an average — show the
        // region's own figure alongside its share of that total.
        const share = (last.value / nationalForYear.value) * 100;
        insights.push({
          type: "share",
          text: `In ${last.year}, ${regionName}'s ${formatValue(last.value, unit)} accounted for ${share.toFixed(1)}% of Finland's total ${label.toLowerCase()} (${formatValue(nationalForYear.value, unit)}).`,
        });
      }
    }
  }

  return insights;
}
