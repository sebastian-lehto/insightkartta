import pandas as pd
from pathlib import Path

from backend.pipelines.analysis.engine import AnalysisEngine
from backend.pipelines.analysis.unemployment.analysis import UnemploymentAnalysis
from backend.app.utils.serialization import clean_dict

def load_data():
    path = Path("backend/data/processed/unemployment_basic/data.parquet")
    return pd.read_parquet(path)


def get_unemployment_analysis():
    df = load_data()

    engine = AnalysisEngine([
        UnemploymentAnalysis(),
    ])

    results = engine.run(df)

    return clean_dict({
        "data": df.to_dict(orient="records"),
        "analysis": results,
    })