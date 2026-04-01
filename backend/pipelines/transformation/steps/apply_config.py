def apply_config_transformations(df, dataset_config):
    df = df.copy()
    t = dataset_config.get("transformation", {})

    for target_col, source_col in t.get("dimensions", {}).items():
        if source_col not in df.columns:
            raise ValueError(f"Missing dimension column '{source_col}'")
        df[target_col] = df[source_col]

    rename_map = {
        old: new for old, new in t.get("rename", {}).items()
        if old in df.columns
    }
    df = df.rename(columns=rename_map)

    for col, dtype in t.get("types", {}).items():
        if col not in df.columns:
            continue
        if dtype == "int":
            df[col] = df[col].astype(int)
        elif dtype == "float":
            df[col] = df[col].astype(float)
        elif dtype == "string":
            df[col] = df[col].astype(str)

    value_column = t.get("value_column")
    if value_column:
        if value_column not in df.columns:
            raise ValueError(f"'{value_column}' not found in dataframe")
        df["value"] = df[value_column]

    for rule in t.get("filters", []):
        column = rule["column"]
        if "exclude" in rule:
            df = df[~df[column].isin(rule["exclude"])]
        if "include" in rule:
            df = df[df[column].isin(rule["include"])]

    return df