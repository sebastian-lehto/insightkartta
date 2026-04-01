import pandas as pd
from pathlib import Path

from backend.pipelines.utils.config_loader import load_config
from backend.pipelines.analysis.engine import AnalysisEngine

# Import analyses (expand as needed)
from backend.pipelines.analysis.unemployment.analysis import UnemploymentAnalysis


PROCESSED_BASE_PATH = Path("backend/data/processed")


def load_processed(dataset_name: str) -> pd.DataFrame:
    path = PROCESSED_BASE_PATH / dataset_name / "latest.csv"

    if not path.exists():
        raise FileNotFoundError(f"No processed data found for {dataset_name}")

    return pd.read_csv(path)


def get_analyses_for_dataset(dataset_name: str):
    """
    Map dataset → analyses.
    Later this can be made fully dynamic.
    """
    if dataset_name == "unemployment":
        return [UnemploymentAnalysis()]

    # Future datasets:
    # if dataset_name == "education":
    #     return [EducationAnalysis()]

    return []


def main():
    config = load_config("backend/pipelines/config/datasets.yaml")

    for dataset in config["datasets"]:
        name = dataset["name"]

        try:
            print(f"\n🔍 Running analysis for: {name}")

            df = load_processed(name)

            analyses = get_analyses_for_dataset(name)

            if not analyses:
                print(f"⚠️ No analyses defined for {name}, skipping...")
                continue

            engine = AnalysisEngine(analyses)

            results = engine.run(df)

            print(f"✅ Results for {name}:")
            print(results)

        except Exception as e:
            print(f"❌ Failed analysis for {name}: {e}")


if __name__ == "__main__":
    main()