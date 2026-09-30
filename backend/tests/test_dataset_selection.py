import pytest

from backend.pipelines.utils.dataset_selection import select_datasets


def test_select_datasets_filters_by_group():
    config = {
        "datasets": [{"name": "population", "group": "region"}],
        "postal_code_datasets": [
            {"name": "postal_population", "group": "postal_code"},
            {"name": "postal_income", "group": "postal_code"},
        ],
    }

    assert [item["name"] for item in select_datasets(config, group="postal_code")] == [
        "postal_population",
        "postal_income",
    ]


def test_select_datasets_rejects_unknown_name_or_group():
    config = {
        "datasets": [{"name": "population", "group": "region"}],
        "postal_code_datasets": [],
    }

    with pytest.raises(ValueError, match="Unknown dataset"):
        select_datasets(config, dataset_names=["missing"])

    with pytest.raises(ValueError, match="No datasets configured"):
        select_datasets(config, group="postal_code")