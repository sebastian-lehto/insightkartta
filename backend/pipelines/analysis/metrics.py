import pandas as pd


def compute_trend(df: pd.DataFrame, value_col: str) -> float:
    """Simple trend: last - first"""
    return df[value_col].iloc[-1] - df[value_col].iloc[0]


def find_peak_year(df: pd.DataFrame, value_col: str, year_col: str):
    idx = df[value_col].idxmax()
    return df.loc[idx, year_col], df.loc[idx, value_col]


def compute_average(df: pd.DataFrame, value_col: str) -> float:
    return df[value_col].mean()