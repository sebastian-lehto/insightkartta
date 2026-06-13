import json
from pathlib import Path
from datetime import datetime

from backend.pipelines.utils.config_loader import load_config
from backend.pipelines.transformation.transform_runner import run_transformation
from backend.pipelines.storage.processed import ProcessedStorage


RAW_BASE_PATH = Path("backend/data/raw")
PROCESSED_BASE_PATH = Path("backend/data/processed")


def get_latest_file(dataset_path: Path):
    files = sorted(dataset_path.glob("*.json"))
    if not files:
        return None
    return files[-1]


def main():
    config = load_config("backend/pipelines/config/datasets.yaml")
    storage = ProcessedStorage()

    for dataset in config["datasets"]:
        name = dataset["name"]

        raw_path = RAW_BASE_PATH / name
        processed_path = PROCESSED_BASE_PATH / name

        try:
            latest_file = get_latest_file(raw_path)

            if latest_file is None:
                print(f"⚠️ No raw files found for {name}, skipping...")
                continue

            print(f"Processing {name} from {latest_file.name}")

            with open(latest_file) as f:
                raw_data = json.load(f)

            df = run_transformation(raw_data, dataset)

            versioned_file, latest_file_path = storage.save(name, df)

            print(f"✅ Processed: {name}")
            print(f"   versioned: {versioned_file}")
            print(f"   latest:    {latest_file_path}")

        except Exception as e:
            print(f"❌ Failed {name}: {e}")


if __name__ == "__main__":
    main()