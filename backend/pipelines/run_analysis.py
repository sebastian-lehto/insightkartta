import json
import numpy as np
import pandas as pd
from pathlib import Path

from backend.pipelines.utils.config_loader import load_config
from backend.pipelines.analysis.engine import AnalysisEngine
from backend.pipelines.analysis.generic import GenericAnalysis


PROCESSED_BASE_PATH = Path("backend/data/processed")
ANALYSIS_BASE_PATH = Path("backend/data/analysis")


def load_processed(dataset_name: str) -> pd.DataFrame:
    path = PROCESSED_BASE_PATH / dataset_name / "latest.csv"

    if not path.exists():
        raise FileNotFoundError(f"No processed data found for {dataset_name}")

    return pd.read_csv(path)


class _NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return super().default(obj)


def save_analysis(dataset_name: str, results: dict) -> None:
    ANALYSIS_BASE_PATH.mkdir(parents=True, exist_ok=True)
    path = ANALYSIS_BASE_PATH / f"{dataset_name}.json"
    with open(path, "w") as f:
        json.dump(results, f, indent=2, cls=_NumpyEncoder)
    print(f"💾 Saved analysis to {path}")


def main():
    config = load_config("backend/pipelines/config/datasets.yaml")

    for dataset in config["datasets"]:
        name = dataset["name"]
        label = dataset.get("metadata", {}).get("label", name)

        try:
            print(f"\n🔍 Running analysis for: {name}")

            df = load_processed(name)

            engine = AnalysisEngine([GenericAnalysis(label=label)])
            results = engine.run(df)

            save_analysis(name, results)

            for analysis_name, output in results.items():
                insights = output.get("insights", [])
                print(f"✅ {name} ({analysis_name}): {len(insights)} insight(s)")

        except Exception as e:
            print(f"❌ Failed analysis for {name}: {e}")


if __name__ == "__main__":
    main()
