def normalize_to_value(df, value_column: str):
    """
    Standardize dataset to use a unified 'value' column.
    Keeps original column for debugging if needed.
    """
    df = df.copy()

    if value_column not in df.columns:
        raise ValueError(f"Column '{value_column}' not found in dataframe")

    df["value"] = df[value_column]

    return df