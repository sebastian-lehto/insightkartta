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

def enrich_with_region_mapping(df: pd.DataFrame) -> pd.DataFrame:
    mapping_df = pd.read_csv("backend/data/region_mapping.csv")

    df_merged = df.merge(
        mapping_df,
        left_on="region",
        right_on="region_code",
        how="left"
    )

    missing_regions = df_merged[df_merged["region_name"].isna()]["region"].unique()

    if len(missing_regions) > 0:
        print("WARNING: Dropping unmapped regions:", missing_regions)

    df = df_merged[df_merged["region_name"].notna()]

    return df