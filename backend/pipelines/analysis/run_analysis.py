import pandas as pd
from pathlib import Path

from backend.pipelines.analysis.engine import AnalysisEngine
from backend.pipelines.analysis.unemployment.analysis import UnemploymentAnalysis


def load_processed(dataset_name: str) -> pd.DataFrame:
    path = Path(f"backend/data/processed/{dataset_name}/data.parquet")
    return pd.read_parquet(path)


def main():
    df = load_processed("unemployment_basic")

    engine = AnalysisEngine([
        UnemploymentAnalysis(),
    ])

    results = engine.run(df)

    print(results)


if __name__ == "__main__":
    main()