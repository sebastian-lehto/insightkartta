from typing import List, Dict, Any
import pandas as pd
from analysis.base import BaseAnalysis


class AnalysisEngine:
    def __init__(self, analyses: List[BaseAnalysis]):
        self.analyses = analyses

    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        results = {}

        for analysis in self.analyses:
            name = analysis.__class__.__name__
            results[name] = analysis.run(df)

        return results