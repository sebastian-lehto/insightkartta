from pathlib import Path

import yaml

from backend.pipelines.ingestion.paavo import PaavoClient
from backend.pipelines.transformation.transform_runner import run_transformation


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def test_paavo_client_posts_to_configured_pxweb_url(monkeypatch):
    endpoint = (
        "https://pxdata.stat.fi/PxWeb/api/v1/fi/"
        "Postinumeroalueittainen_avoin_tieto/uusin/12f7.px"
    )
    payload = {
        "query": [{
            "code": "postinumeroalue_4_20260101",
            "selection": {"filter": "item", "values": ["SSS", "00100"]},
        }],
        "response": {"format": "json-stat2"},
    }
    response_data = {"class": "dataset", "id": ["postinumeroalue_4_20260101"]}
    calls = []

    def fake_post(url, json, timeout):
        calls.append((url, json, timeout))
        return FakeResponse(response_data)

    monkeypatch.setattr("backend.pipelines.ingestion.paavo.requests.post", fake_post)

    result = PaavoClient().fetch(endpoint, payload)

    assert calls == [(endpoint, payload, 60)]
    assert result is response_data


def test_paavo_client_resolves_relative_endpoint_against_pxweb_catalog(monkeypatch):
    calls = []

    def fake_post(url, json, timeout):
        calls.append(url)
        return FakeResponse({"class": "dataset"})

    monkeypatch.setattr("backend.pipelines.ingestion.paavo.requests.post", fake_post)

    PaavoClient().fetch("Postinumeroalueittainen_avoin_tieto/table.px", {})

    assert calls == [
        "https://pxdata.stat.fi/PxWeb/api/v1/fi/"
        "Postinumeroalueittainen_avoin_tieto/table.px"
    ]


def test_paavo_client_expands_all_selections_from_table_metadata(monkeypatch):
    endpoint = "https://pxdata.stat.fi/PxWeb/api/v1/fi/Postinumero/12f7.px"
    client = PaavoClient()
    client._variable_cache.pop(endpoint, None)
    metadata = {
        "variables": [
            {"code": "postal_area", "values": ["SSS", "00100", "00120"]},
            {"code": "year", "values": ["2023", "2024"]},
        ]
    }
    payload = {
        "query": [
            {"code": "postal_area", "selection": {"filter": "all", "values": ["*"]}},
            {"code": "year", "selection": {"filter": "all", "values": ["*"]}},
        ]
    }
    posted_payloads = []
    monkeypatch.setattr(
        "backend.pipelines.ingestion.paavo.requests.get",
        lambda url, timeout: FakeResponse(metadata),
    )

    def fake_post(url, json, timeout):
        posted_payloads.append(json)
        return FakeResponse({"class": "dataset"})

    monkeypatch.setattr("backend.pipelines.ingestion.paavo.requests.post", fake_post)

    client.fetch(endpoint, payload)

    assert posted_payloads[0]["query"] == [
        {"code": "postal_area", "selection": {"filter": "item", "values": ["SSS", "00100", "00120"]}},
        {"code": "year", "selection": {"filter": "item", "values": ["2023", "2024"]}},
    ]
    client._variable_cache.pop(endpoint, None)


def test_postal_code_configs_select_history_and_paavo_indicators():
    config = yaml.safe_load(
        Path("backend/pipelines/config/datasets.yaml").read_text(encoding="utf-8")
    )
    datasets = {dataset["name"]: dataset for dataset in config["postal_code_datasets"]}
    expected_codes = {
        "postal_code_population": "he_vakiy",
        "postal_code_median_income": "hr_mtu",
        "postal_code_unemployment": "pt_tyott",
    }

    for name, indicator_code in expected_codes.items():
        dataset = datasets[name]
        assert dataset["endpoint"].endswith("/uusin/12f7.px")
        assert dataset["payload"]["response"]["format"] == "json-stat2"
        assert dataset["payload"]["query"][0]["code"] == "postinumeroalue_4_20260101"
        assert dataset["payload"]["query"][1]["code"] == "timeperiod_y"
        assert dataset["payload"]["query"][2]["code"] == "contentscode"
        assert dataset["payload"]["query"][2]["selection"]["values"] == [indicator_code]
        assert dataset["transformation"]["value_dimension"] == "contentscode"


def test_paavo_json_stat_response_transforms_to_historical_postal_row():
    config = yaml.safe_load(
        Path("backend/pipelines/config/datasets.yaml").read_text(encoding="utf-8")
    )
    dataset = next(
        item for item in config["postal_code_datasets"]
        if item["name"] == "postal_code_population"
    )
    response = {
        "class": "dataset",
        "id": ["postinumeroalue_4_20260101", "timeperiod_y", "contentscode"],
        "size": [1, 1, 1],
        "dimension": {
            "postinumeroalue_4_20260101": {
                "category": {
                    "index": {"00100": 0},
                    "label": {"00100": "00100 Helsinki keskusta - Etu-Töölö (Helsinki)"},
                }
            },
            "timeperiod_y": {
                "category": {"index": {"2024": 0}, "label": {"2024": "2024"}},
            },
            "contentscode": {
                "category": {
                    "index": {"he_vakiy": 0},
                    "label": {"he_vakiy": "Asukkaat yhteensä (HE)"},
                }
            },
        },
        "value": [12000],
    }

    transformed = run_transformation({"data": response}, dataset)
    row = transformed.iloc[0].to_dict()

    assert row["year"] == 2024
    assert row["value"] == 12000.0
    assert row["region_code"] == "KU091"
    assert row["region_name"] == "Helsinki"
    assert row["postal_code"] == "00100"
    assert row["postal_code_name"] == "Helsinki keskusta - Etu-Töölö"
    assert row["indicator"] == "he_vakiy"