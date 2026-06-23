def select_required_columns(df):
    """
    Keep only the required columns: year, value, region_code, region_name.
    Removes all other columns from the dataframe.
    """
    required_columns = ["year", "value", "region_code", "region_name"]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    return df[required_columns]