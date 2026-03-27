import pandas as pd
from typing import Dict, Any

from analysis.base import BaseAnalysis
from analysis.metrics import compute_trend, find_peak_year, compute_average
from analysis.insights import trend_insight, peak_insight


class UnemploymentAnalysis(BaseAnalysis):
    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        df = df.sort_values("year")

        metric = "unemployment_rate"

        trend = compute_trend(df, metric)
        avg = compute_average(df, metric)
        peak_year, peak_value = find_peak_year(df, metric, "year")

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