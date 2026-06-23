import pandas as pd
from typing import Dict, Any

from backend.pipelines.analysis.base import BaseAnalysis
from backend.pipelines.analysis.metrics import compute_trend, find_peak_year, compute_average
from backend.pipelines.analysis.insights import trend_insight, peak_insight

NATIONAL_REGION_CODE = "SSS"


class GenericAnalysis(BaseAnalysis):
    def __init__(self, label: str = "Value"):
        self.label = label

    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        national = df[df["region_code"] == NATIONAL_REGION_CODE]

        if national.empty:
            national = df

        national = national.sort_values("year")

        trend = compute_trend(national, "value")
        avg = compute_average(national, "value")
        peak_year, peak_value = find_peak_year(national, "value", "year")

        return {
            "metrics": {
                "trend": trend,
                "average": avg,
                "peak_year": peak_year,
                "peak_value": peak_value,
            },
            "insights": [
                trend_insight(trend, self.label),
                peak_insight(peak_year, peak_value, self.label),
            ],
        }
