from __future__ import annotations

import json
from pathlib import Path

ANALYSIS_ROOT = Path("backend/data/analysis/region_insights/")
CORRELATIONS_PATH = Path("backend/data/analysis/election_indicator_correlations.json")


class InsightNotFoundError(FileNotFoundError):
    """Raised when region insight data does not exist."""


def _load_json(path: Path, missing_message: str) -> dict:
    if not path.exists():
        raise InsightNotFoundError(missing_message)

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        raise InsightNotFoundError(f"Invalid JSON in {path}: {exc}") from exc


def get_region_insights(region: str) -> dict:
    path = ANALYSIS_ROOT / f"{region}.json"
    return _load_json(
        path,
        f"No region insights found for region {region}",
    )


def get_election_correlations() -> dict:
    return _load_json(
        CORRELATIONS_PATH,
        "Election indicator correlations not yet generated",
    )
