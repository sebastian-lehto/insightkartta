from __future__ import annotations

import json
from pathlib import Path


class InsightNotFoundError(FileNotFoundError):
    """Raised when region insight data does not exist."""


class InsightService:
    def __init__(self) -> None:
        self.analysis_root = Path("backend/data/analysis/region_insights/")

    def get_region_insights(self, region: str) -> dict:
        path = self.analysis_root / f"{region}.json"

        if not path.exists():
            raise InsightNotFoundError(
                f"No region insights found for region {region}"
            )

        return json.loads(path.read_text(encoding="utf-8"))


def get_region_insights(region: str) -> dict:
    service = InsightService()
    return service.get_region_insights(region)