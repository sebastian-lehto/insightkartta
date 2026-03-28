import logging
from typing import Dict, Any
from pipelines.ingestion.base import BaseAPIClient
from pipelines.storage.local import LocalStorage

logger = logging.getLogger(__name__)


class DataFetcher:
    def __init__(self, client: BaseAPIClient, storage: LocalStorage):
        self.client = client
        self.storage = storage

    def fetch_and_store(
        self,
        dataset_name: str,
        endpoint: str,
        payload: Dict[str, Any],
    ) -> None:
        logger.info(f"Starting ingestion for dataset: {dataset_name}")

        data = self.client.fetch(endpoint, payload)

        path = self.storage.save(dataset_name, data)

        logger.info(f"Dataset '{dataset_name}' stored at: {path}")