import pandas as pd

from backend.pipelines.transformation.steps.normalize import select_required_columns


def test_select_required_columns_keeps_postal_code_when_present():
    df = pd.DataFrame([
        {
            "year": 2023,
            "value": 1234,
            "region_code": "KU091",
            "region_name": "Helsinki",
            "postal_code": "00100",
        }
    ])

    transformed = select_required_columns(df)

    assert "postal_code" in transformed.columns
    assert transformed.iloc[0]["postal_code"] == "00100"
