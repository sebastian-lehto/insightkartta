import argparse
import json
from pathlib import Path
from datetime import datetime

from backend.pipelines.utils.config_loader import load_config
from backend.pipelines.transformation.transform_runner import run_transformation
from backend.pipelines.storage.processed import ProcessedStorage
from backend.pipelines.utils.dataset_selection import select_datasets


RAW_BASE_PATH = Path("backend/data/raw")
PROCESSED_BASE_PATH = Path("backend/data/processed")


def get_latest_file(dataset_path: Path):
    files = sorted(dataset_path.glob("*.json"))
    if not files:
        return None
    return files[-1]


def main(dataset_names=None, group=None, fail_on_error=False):
    config = load_config("backend/pipelines/config/datasets.yaml")
    storage = ProcessedStorage()
    datasets = select_datasets(config, dataset_names=dataset_names, group=group)
    failures = []

    for dataset in datasets:
        name = dataset["name"]

        raw_path = RAW_BASE_PATH / name
        processed_path = PROCESSED_BASE_PATH / name

        try:
            latest_file = get_latest_file(raw_path)

            if latest_file is None:
                print(f"⚠️ No raw files found for {name}, skipping...")
                if fail_on_error:
                    failures.append(name)
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
            failures.append(name)

    if fail_on_error and failures:
        raise RuntimeError(f"Transformation failed for dataset(s): {', '.join(failures)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transform ingested datasets.")
    parser.add_argument(
        "--dataset",
        action="append",
        dest="dataset_names",
        help="Dataset to transform; may be provided multiple times.",
    )
    parser.add_argument("--group", help="Only process datasets in this config group.")
    parser.add_argument("--fail-on-error", action="store_true", help="Exit non-zero if any selected dataset fails.")
    args = parser.parse_args()
    main(args.dataset_names, group=args.group, fail_on_error=args.fail_on_error)