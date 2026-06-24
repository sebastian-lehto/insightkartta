from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def api_client():
    """TestClient wired to backend/tests/fixtures instead of backend/data/.

    Monkeypatches every hardcoded data-path constant used by the API services
    and clears load_config's @lru_cache so each test sees the fixture config,
    not whatever a previous test or the real backend/data/ left cached.
    """
    from backend.app.services import dataset_service, insight_service

    originals = {
        "CONFIG_PATH": dataset_service.CONFIG_PATH,
        "PROCESSED_BASE": dataset_service.PROCESSED_BASE,
        "ANALYSIS_BASE": dataset_service.ANALYSIS_BASE,
        "ANALYSIS_ROOT": insight_service.ANALYSIS_ROOT,
        "CORRELATIONS_PATH": insight_service.CORRELATIONS_PATH,
    }

    dataset_service.CONFIG_PATH = str(FIXTURES_DIR / "datasets.yaml")
    dataset_service.PROCESSED_BASE = FIXTURES_DIR / "processed"
    dataset_service.ANALYSIS_BASE = FIXTURES_DIR / "analysis"
    insight_service.ANALYSIS_ROOT = FIXTURES_DIR / "analysis" / "region_insights"
    insight_service.CORRELATIONS_PATH = (
        FIXTURES_DIR / "analysis" / "election_indicator_correlations.json"
    )
    dataset_service.load_config.cache_clear()

    from backend.app.main import app
    from fastapi.testclient import TestClient

    try:
        with TestClient(app) as client:
            yield client
    finally:
        dataset_service.CONFIG_PATH = originals["CONFIG_PATH"]
        dataset_service.PROCESSED_BASE = originals["PROCESSED_BASE"]
        dataset_service.ANALYSIS_BASE = originals["ANALYSIS_BASE"]
        insight_service.ANALYSIS_ROOT = originals["ANALYSIS_ROOT"]
        insight_service.CORRELATIONS_PATH = originals["CORRELATIONS_PATH"]
        dataset_service.load_config.cache_clear()
