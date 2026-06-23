from __future__ import annotations

import json
from pathlib import Path

ANALYSIS_ROOT = Path("backend/data/analysis/region_insights/")
CORRELATIONS_PATH = Path("backend/data/analysis/election_indicator_correlations.json")


class InsightNotFoundError(FileNotFoundError):
    """Raised when region insight data does not exist."""


def get_region_insights(region: str) -> dict:
    path = ANALYSIS_ROOT / f"{region}.json"

    if not path.exists():
        raise InsightNotFoundError(
            f"No region insights found for region {region}"
        )

    return json.loads(path.read_text(encoding="utf-8"))


def get_election_correlations() -> dict:
    if not CORRELATIONS_PATH.exists():
        raise InsightNotFoundError("Election indicator correlations not yet generated")

    return json.loads(CORRELATIONS_PATH.read_text(encoding="utf-8"))
