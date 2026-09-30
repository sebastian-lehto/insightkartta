import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path

from backend.pipelines.utils.config_loader import load_config
from backend.pipelines.analysis.engine import AnalysisEngine
from backend.pipelines.analysis.generic import GenericAnalysis
from backend.pipelines.utils.dataset_selection import select_datasets


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


def main(dataset_names=None, group=None, fail_on_error=False):
    config = load_config("backend/pipelines/config/datasets.yaml")
    datasets = select_datasets(config, dataset_names=dataset_names, group=group)
    failures = []

    for dataset in datasets:
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
            failures.append(name)

    if fail_on_error and failures:
        raise RuntimeError(f"Analysis failed for dataset(s): {', '.join(failures)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze processed datasets.")
    parser.add_argument(
        "--dataset",
        action="append",
        dest="dataset_names",
        help="Dataset to analyze; may be provided multiple times.",
    )
    parser.add_argument("--group", help="Only process datasets in this config group.")
    parser.add_argument("--fail-on-error", action="store_true", help="Exit non-zero if any selected dataset fails.")
    args = parser.parse_args()
    main(args.dataset_names, group=args.group, fail_on_error=args.fail_on_error)
