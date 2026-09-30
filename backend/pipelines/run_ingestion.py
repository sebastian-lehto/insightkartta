import argparse
import logging

from backend.pipelines.ingestion.paavo import PaavoClient
from backend.pipelines.ingestion.statfi import StatisticsFinlandClient
from backend.pipelines.ingestion.fetcher import DataFetcher
from backend.pipelines.storage.local import LocalStorage
from backend.pipelines.utils.logging import setup_logging
from backend.pipelines.utils.config_loader import load_config
from backend.pipelines.utils.dataset_selection import select_datasets


def main(dataset_names=None, group=None, fail_on_error=False):
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Starting ingestion pipeline")

    config = load_config("backend/pipelines/config/datasets.yaml")
    datasets = select_datasets(config, dataset_names=dataset_names, group=group)

    storage = LocalStorage()

    failures = []
    for dataset in datasets:
        source = dataset["source"]

        if source == "statfi":
            client = StatisticsFinlandClient()
        elif source == "paavo":
            client = PaavoClient()
        else:
            logger.warning(f"Unsupported source for pipeline: {source} ({dataset['name']})")
            continue

        fetcher = DataFetcher(client, storage)

        try:
            fetcher.fetch_and_store(
                dataset_name=dataset["name"],
                endpoint=dataset["endpoint"],
                payload=dataset.get("payload", {}),
            )
        except Exception as e:
            logger.error(f"Failed to process dataset {dataset['name']}: {e}")
            failures.append(dataset["name"])
            continue

    logger.info("Ingestion pipeline completed")
    if fail_on_error and failures:
        raise RuntimeError(f"Ingestion failed for dataset(s): {', '.join(failures)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch configured datasets.")
    parser.add_argument(
        "--dataset",
        action="append",
        dest="dataset_names",
        help="Dataset to fetch; may be provided multiple times.",
    )
    parser.add_argument("--group", help="Only process datasets in this config group.")
    parser.add_argument("--fail-on-error", action="store_true", help="Exit non-zero if any selected dataset fails.")
    args = parser.parse_args()
    main(args.dataset_names, group=args.group, fail_on_error=args.fail_on_error)