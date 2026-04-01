def apply_config_transformations(df, config):
    t = config.get("transformation", {})

    df = df.copy()

    # ✅ 1. Map dimensions → standard names
    if "dimensions" in t:
        for new_name, old_name in t["dimensions"].items():
            df[new_name] = df[old_name]

    # ✅ 2. Rename value columns
    if "rename" in t:
        df = df.rename(columns=t["rename"])

    # ✅ 3. Apply filters
    for f in t.get("filters", []):
        if "exclude" in f:
            df = df[~df[f["column"]].isin(f["exclude"])]

    # ✅ 4. Normalize to "value"
    value_column = t.get("value_column")
    if value_column:
        if value_column not in df.columns:
            raise ValueError(f"{value_column} not found in df")
        df["value"] = df[value_column]

    # ✅ 5. Ensure correct types
    if "year" in df.columns:
        df["year"] = df["year"].astype(int)

    return df