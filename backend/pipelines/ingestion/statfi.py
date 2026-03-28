import requests
import logging
from typing import Any, Dict
from .base import BaseAPIClient

logger = logging.getLogger(__name__)


class StatisticsFinlandClient(BaseAPIClient):
    BASE_URL = "https://pxdata.stat.fi/PxWeb/api/v1/en/StatFin"

    def fetch(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/{endpoint}"

        logger.info(f"Requesting data from {url}")

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

        logger.info("Data fetched successfully")

        return response.json()