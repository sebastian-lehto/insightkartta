import logging

from pipelines.ingestion.statfi import StatisticsFinlandClient
from pipelines.ingestion.fetcher import DataFetcher
from pipelines.storage.local import LocalStorage
from pipelines.utils.logging import setup_logging
from pipelines.utils.config_loader import load_config


def main():
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Starting ingestion pipeline")

    config = load_config("pipelines/config/datasets.yaml")

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