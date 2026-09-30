import logging
import os
from typing import Any, Dict
from urllib.parse import urljoin

import requests

from .base import BaseAPIClient

logger = logging.getLogger(__name__)


class PaavoClient(BaseAPIClient):
    """Client for PXWeb tables in Statistics Finland's Paavo catalogue."""

    DEFAULT_BASE_URL = "https://pxdata.stat.fi/PxWeb/api/v1/fi/"
    _variable_cache: dict[str, dict[str, list[str]]] = {}

    def __init__(self, base_url: str | None = None):
        self.base_url = (
            base_url or os.environ.get("PAAVO_BASE_URL") or self.DEFAULT_BASE_URL
        ).rstrip("/") + "/"

    def fetch(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = endpoint if endpoint.startswith(("http://", "https://")) else urljoin(
            self.base_url, endpoint.lstrip("/")
        )

        logger.info("Requesting Paavo data from %s", url)

        translated_payload = self._expand_all_selections(url, payload)
        response = requests.post(url, json=translated_payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        if not isinstance(data, dict):
            raise ValueError(f"Expected a JSON object from Paavo PXWeb, got {type(data).__name__}")
        return data

    def _expand_all_selections(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        query = payload.get("query", [])
        if not any(
            item.get("selection", {}).get("filter") == "all"
            or "*" in item.get("selection", {}).get("values", [])
            for item in query
        ):
            return payload

        variables = self._get_variables(url)
        translated_query = []
        for item in query:
            selection = item.get("selection", {})
            if selection.get("filter") != "all" and "*" not in selection.get("values", []):
                translated_query.append(item)
                continue

            values = variables.get(item["code"])
            if values is None:
                raise ValueError(f"PXWeb table does not contain dimension '{item['code']}'")
            translated_query.append({
                **item,
                "selection": {"filter": "item", "values": values},
            })

        return {**payload, "query": translated_query}

    def _get_variables(self, url: str) -> dict[str, list[str]]:
        if url not in self._variable_cache:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            self._variable_cache[url] = {
                variable["code"]: variable.get("values", [])
                for variable in response.json().get("variables", [])
            }
        return self._variable_cache[url]
