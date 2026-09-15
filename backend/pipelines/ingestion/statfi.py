import re
import requests
import logging
from typing import Any, Dict, List
from .base import BaseAPIClient

logger = logging.getLogger(__name__)


class StatisticsFinlandClient(BaseAPIClient):
    BASE_URL = "https://pxdata.stat.fi/PXWeb/api/v1/fi/StatFin"

    def _to_short_endpoint(self, endpoint: str) -> str:
        """Convert long endpoint to short format required by current API.

        'tyokay/statfin_tyokay_pxt_115x.px' -> 'tyokay/115x.px'
        """
        parts = endpoint.split("/")
        if len(parts) >= 2:
            folder = parts[0]
            table = parts[-1]
            m = re.match(r"statfin_\w+_pxt_(.+)", table)
            if m:
                return f"{folder}/{m.group(1)}"
        return endpoint

    def _get_table_variables(self, short_endpoint: str) -> List[Dict]:
        """GET table metadata to discover dimension variable codes and values."""
        url = f"{self.BASE_URL}/{short_endpoint}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json().get("variables", [])

    def _translate_payload(self, payload: Dict, variables: List[Dict]) -> Dict:
        """Translate text-label filter codes to actual dimension codes.

        Handles API format changes where 'Alue' became 'alue_23_20260101', etc.
        Also translates short Tiedot values to full codes ('vaesto' -> 'vaerak-vaesto').
        """
        if not payload.get("query"):
            return payload

        text_to_code = {v["text"]: v["code"] for v in variables}
        # Build prefix fallback: "Alue" matches "Alue 2026", etc.
        text_prefix_to_code = {
            v["text"].split()[0]: v["code"]
            for v in variables
            if v["text"].split()[0] not in text_to_code
        }

        code_to_value_map: Dict[str, Dict[str, str]] = {}
        valid_values: Dict[str, set] = {}
        for var in variables:
            short_to_full: Dict[str, str] = {}
            full_codes: set = set(var.get("values", []))
            valid_values[var["code"]] = full_codes
            for full_code in full_codes:
                short = full_code.split("-", 1)[1] if "-" in full_code else full_code
                short_to_full[short] = full_code
            code_to_value_map[var["code"]] = short_to_full

        translated_query = []
        for item in payload["query"]:
            original_code = item["code"]
            actual_code = (
                text_to_code.get(original_code)
                or text_prefix_to_code.get(original_code)
                or original_code
            )
            value_map = code_to_value_map.get(actual_code, {})
            valid = valid_values.get(actual_code)
            translated_values = []
            for v in item["selection"]["values"]:
                translated = value_map.get(v, v)
                # Drop values absent from this table (e.g. MA1/MA2 regional aggregates
                # that exist in some tables but not others).
                if valid is None or translated in valid:
                    translated_values.append(translated)
            if not translated_values:
                continue
            translated_query.append({
                "code": actual_code,
                "selection": {
                    "filter": item["selection"]["filter"],
                    "values": translated_values,
                },
            })

        return {**payload, "query": translated_query}

    def fetch(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        short_endpoint = self._to_short_endpoint(endpoint)
        url = f"{self.BASE_URL}/{short_endpoint}"

        logger.info(f"Requesting data from {url}")

        try:
            variables = self._get_table_variables(short_endpoint)
            translated_payload = self._translate_payload(payload, variables)
            response = requests.post(url, json=translated_payload, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

        logger.info("Data fetched successfully")
        return response.json()
