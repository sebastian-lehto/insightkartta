import pandas as pd
from typing import Dict, Any

from backend.pipelines.analysis.base import BaseAnalysis
from backend.pipelines.analysis.metrics import compute_trend, find_peak_year, compute_average
from backend.pipelines.analysis.insights import trend_insight, peak_insight


class UnemploymentAnalysis(BaseAnalysis):
    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        df = df.sort_values("year")

        trend = compute_trend(df, "value")
        avg = compute_average(df, "value")
        peak_year, peak_value = find_peak_year(df, "value", "year")

        return {
            "metrics": {
                "trend": trend,
                "average": avg,
                "peak_year": peak_year,
                "peak_value": peak_value,
            },
            "insights": [
                trend_insight(trend, "Unemployment rate"),
                peak_insight(peak_year, peak_value, "Unemployment rate"),
            ],
        }