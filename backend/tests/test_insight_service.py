import json

import pandas as pd
import pytest

from backend.app.services import dataset_service, insight_service


def test_get_region_postal_code_comparison_sorts_by_selected_metric(monkeypatch):
    def fake_load_processed(name):
        if name == "postal_code_population":
            return pd.DataFrame([
                {"year": 2023, "value": 200, "region_code": "KU091", "region_name": "Helsinki", "postal_code": "00100"},
                {"year": 2023, "value": 100, "region_code": "KU091", "region_name": "Helsinki", "postal_code": "00200"},
            ])
        if name == "postal_code_median_income":
            return pd.DataFrame([
                {"year": 2023, "value": 35000, "region_code": "KU091", "region_name": "Helsinki", "postal_code": "00100"},
                {"year": 2023, "value": 25000, "region_code": "KU091", "region_name": "Helsinki", "postal_code": "00200"},
            ])
        if name == "postal_code_unemployment":
            return pd.DataFrame([
                {"year": 2023, "value": 8.5, "region_code": "KU091", "region_name": "Helsinki", "postal_code": "00100"},
                {"year": 2023, "value": 12.5, "region_code": "KU091", "region_name": "Helsinki", "postal_code": "00200"},
            ])
        raise FileNotFoundError(name)

    monkeypatch.setattr(dataset_service, "load_processed", fake_load_processed)
    monkeypatch.setattr(
        dataset_service,
        "get_dataset_config",
        lambda name: {
            "name": name,
            "metadata": {"label": name, "unit": "%" if "unemployment" in name else "people" if "population" in name else "EUR"},
        },
    )

    result = dataset_service.get_region_postal_code_comparison("Helsinki", sort_by="postal_code_unemployment", sort_desc=False)

    assert [row["postal_code"] for row in result["postal_codes"]] == ["00100", "00200"]
    assert result["postal_codes"][0]["postal_code_unemployment"] == 8.5


def test_get_region_postal_code_comparison_cleans_non_finite_values(monkeypatch):
    def fake_load_processed(name):
        if name == "postal_code_population":
            return pd.DataFrame([
                {
                    "year": 2017,
                    "value": float("nan"),
                    "region_code": "KU091",
                    "region_name": "Helsinki",
                    "postal_code": "00100",
                }
            ])
        raise FileNotFoundError(name)

    monkeypatch.setattr(dataset_service, "load_processed", fake_load_processed)
    monkeypatch.setattr(
        dataset_service,
        "get_dataset_config",
        lambda name: {"name": name, "metadata": {"label": name, "unit": "people"}},
    )

    result = dataset_service.get_region_postal_code_comparison("KU091")

    assert result["postal_codes"][0]["postal_code_population"] is None
    json.dumps(result, allow_nan=False)


def test_postal_comparison_returns_metric_history_and_config_metadata(monkeypatch):
    configs = [
        {
            "name": "postal_code_population",
            "source": "paavo",
            "group": "postal_code",
            "metadata": {
                "label": "Residents",
                "unit": "people",
                "visualization": {"summary": "total", "map": {"bins": [1, 2, 3, 4, 5]}},
            },
        },
        {
            "name": "postal_code_median_income",
            "source": "paavo",
            "group": "postal_code",
            "metadata": {
                "label": "Median income",
                "unit": "EUR",
                "visualization": {"summary": "median", "map": {"bins": [10, 20, 30, 40, 50]}},
            },
        },
    ]
    frames = {
        "postal_code_population": pd.DataFrame([
            {"year": 2023, "value": 100, "region_code": "KU091", "region_name": "Helsinki", "postal_code": "00100"},
            {"year": 2024, "value": 110, "region_code": "KU091", "region_name": "Helsinki", "postal_code": "00100"},
        ]),
        "postal_code_median_income": pd.DataFrame([
            {"year": 2023, "value": 30000, "region_code": "KU091", "region_name": "Helsinki", "postal_code": "00100"},
            {"year": 2024, "value": 32000, "region_code": "KU091", "region_name": "Helsinki", "postal_code": "00100"},
        ]),
    }

    monkeypatch.setattr(dataset_service, "get_all_dataset_configs", lambda: configs)
    monkeypatch.setattr(dataset_service, "load_processed", lambda name: frames[name])

    result = dataset_service.get_region_postal_code_comparison("KU091")

    assert result["years"] == [2023, 2024]
    assert result["year"] == 2024
    assert result["postal_codes"][0]["postal_code_population"] == 110
    assert result["postal_codes"][0]["history"]["2023"]["postal_code_population"] == 100
    assert result["datasets"][0]["summary"] == "total"
    assert result["datasets"][0]["bins"] == [1, 2, 3, 4, 5]


def test_get_region_insights_raises_not_found_for_invalid_json(monkeypatch, tmp_path):
    insight_dir = tmp_path / "region_insights"
    insight_dir.mkdir()
    broken_file = insight_dir / "KU999.json"
    broken_file.write_text('{"region": "ok"}\n{"region": "still bad"}', encoding="utf-8")

    monkeypatch.setattr(insight_service, "ANALYSIS_ROOT", insight_dir)

    with pytest.raises(insight_service.InsightNotFoundError):
        insight_service.get_region_insights("KU999")


def test_get_election_correlations_raises_not_found_for_invalid_json(monkeypatch, tmp_path):
    bad_correlations = tmp_path / "election_indicator_correlations.json"
    bad_correlations.write_text('{"year": 2021}\n{"year": 2025}', encoding="utf-8")

    monkeypatch.setattr(insight_service, "CORRELATIONS_PATH", bad_correlations)

    with pytest.raises(insight_service.InsightNotFoundError):
        insight_service.get_election_correlations()
