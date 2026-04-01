import logging

from backend.pipelines.ingestion.statfi import StatisticsFinlandClient
from backend.pipelines.ingestion.fetcher import DataFetcher
from backend.pipelines.storage.local import LocalStorage
from backend.pipelines.utils.logging import setup_logging
from backend.pipelines.utils.config_loader import load_config


def main():
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Starting ingestion pipeline")

    config = load_config("backend/pipelines/config/datasets.yaml")

    client = StatisticsFinlandClient()
    storage = LocalStorage()
    fetcher = DataFetcher(client, storage)

    for dataset in config["datasets"]:
        if dataset["source"] != "statfi":
            logger.warning(f"Unsupported source: {dataset['source']}")
            continue

        try:
            fetcher.fetch_and_store(
                dataset_name=dataset["name"],
                endpoint=dataset["endpoint"],
                payload=dataset["payload"],
            )
        except Exception as e:
            logger.error(f"Failed to process dataset {dataset['name']}: {e}")
            continue

    logger.info("Ingestion pipeline completed")


if __name__ == "__main__":
    main()