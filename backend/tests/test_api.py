def test_datasets_lists_configured_datasets(api_client):
    res = api_client.get("/datasets")
    assert res.status_code == 200
    assert res.json() == [{"name": "unemployment", "label": "Unemployment Rate"}]


def test_get_dataset_returns_data_meta_and_analysis(api_client):
    res = api_client.get("/unemployment")
    assert res.status_code == 200
    body = res.json()

    assert body["meta"]["label"] == "Unemployment Rate"
    assert body["meta"]["unit"] == "%"
    assert body["meta"]["visualization"]["map"]["bins"] == [4, 6, 8, 10, 15]

    assert {"region_code": "KU091", "region_name": "Helsinki", "year": 2025, "value": 9.5} in body["data"]

    assert body["analysis"]["GenericAnalysis"]["metrics"]["peak_value"] == 11.0


def test_unknown_dataset_returns_404_not_500(api_client):
    res = api_client.get("/does-not-exist")
    assert res.status_code == 404


def test_region_insights_returns_periods_array(api_client):
    res = api_client.get("/regions/KU091/insights")
    assert res.status_code == 200
    body = res.json()

    assert body["region"]["name"] == "Helsinki"
    assert len(body["periods"]) == 1
    assert body["periods"][0]["election_summary"]["latest_year"] == 2025


def test_missing_region_insight_returns_404_not_500(api_client):
    res = api_client.get("/regions/KU999/insights")
    assert res.status_code == 404


def test_election_correlations_keyed_by_end_year(api_client):
    res = api_client.get("/elections/correlations")
    assert res.status_code == 200
    body = res.json()

    assert "2025" in body
    assert body["2025"]["correlations"]["unemployment"]["VIHR"]["classification"] == "weak_negative"


def test_election_correlations_404_when_not_yet_generated(api_client, monkeypatch):
    from backend.app.services import insight_service

    monkeypatch.setattr(
        insight_service, "CORRELATIONS_PATH", insight_service.CORRELATIONS_PATH.parent / "does-not-exist.json"
    )

    res = api_client.get("/elections/correlations")
    assert res.status_code == 404
