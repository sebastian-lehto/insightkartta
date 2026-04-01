import pandas as pd


def clean_unemployment(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df = df.rename(columns={
        "Alue": "region",
        "Vuosi": "year",
        "tyollisyysaste": "employment_rate",
        "tyottomyysaste": "unemployment_rate",
        "taloudellinenhuoltosuhde": "dependency_ratio",
    })

    df["year"] = df["year"].astype(int)

    return df