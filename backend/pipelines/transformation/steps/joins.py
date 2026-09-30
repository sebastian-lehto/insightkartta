import pandas as pd


def apply_joins(df, config):
    t = config.get("transformation", {})

    if t.get("join", {}).get("region_mapping"):
        mapping_df = pd.read_csv("backend/data/region_mapping.csv")
        if "postal_code" in df.columns:
            region_aliases = t.get("join", {}).get("region_aliases", {})
            if region_aliases:
                df["region"] = df["region"].replace(region_aliases)
            df = df.merge(
                mapping_df,
                left_on="region",
                right_on="region_name",
                how="left",
            )
        else:
            df = df.merge(
                mapping_df,
                left_on="region",
                right_on="region_code",
                how="left",
            )

        missing = df[df["region_name"].isna()]["region"].unique()

        if len(missing) > 0:
            print("WARNING: Missing region mappings:", missing)

    return df