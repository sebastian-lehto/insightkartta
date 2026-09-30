def select_required_columns(df):
    """
    Keep the required columns for region analytics, while preserving optional
    postal-code fields that are needed for the postal comparison feature.
    """
    required_columns = ["year", "value", "region_code", "region_name"]
    optional_columns = [
        "postal_code",
        "postal_code_name",
        "indicator",
        "indicator_label",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    available_optional = [col for col in optional_columns if col in df.columns]
    final_columns = required_columns + available_optional
    return df[final_columns]