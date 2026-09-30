import argparse
import logging

from backend.pipelines.ingestion.paavo import PaavoClient
from backend.pipelines.ingestion.statfi import StatisticsFinlandClient
from backend.pipelines.ingestion.fetcher import DataFetcher
from backend.pipelines.storage.local import LocalStorage
from backend.pipelines.utils.logging import setup_logging
from backend.pipelines.utils.config_loader import load_config


def main(dataset_names=None):
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Starting ingestion pipeline")

    config = load_config("backend/pipelines/config/datasets.yaml")
    datasets = config.get("datasets", []) + config.get("postal_code_datasets", [])
    if dataset_names:
        configured_names = {dataset["name"] for dataset in datasets}
        unknown_names = set(dataset_names) - configured_names
        if unknown_names:
            raise ValueError(f"Unknown dataset(s): {', '.join(sorted(unknown_names))}")
        datasets = [dataset for dataset in datasets if dataset["name"] in dataset_names]

    storage = LocalStorage()

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
            continue

    logger.info("Ingestion pipeline completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch configured datasets.")
    parser.add_argument(
        "--dataset",
        action="append",
        dest="dataset_names",
        help="Dataset to fetch; may be provided multiple times.",
    )
    main(parser.parse_args().dataset_names)