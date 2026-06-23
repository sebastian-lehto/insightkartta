from __future__ import annotations

from typing import Any

import pandas as pd


def calculate_indicator_change(
    *,
    dataset_name: str,
    region_df: pd.DataFrame,
    start_year: int,
    end_year: int,
    value_column: str = "value",
) -> dict[str, Any] | None:
    """
    Calculate indicator change over an election period.

    Example:

        election period:
            2021 -> 2025

        available indicator years:
            2021, 2022, 2023, 2024

        comparison becomes:
            2021 -> 2024

    The latest available observation less than or equal to
    end_year is used.

    Likewise, the latest available observation less than or
    equal to start_year is used.
    """

    if region_df.empty:
        return None

    if "region" in region_df.columns:
        duplicate_index = ["region", "year"]
    elif "region_code" in region_df.columns:
        duplicate_index = ["region_code", "year"]
    else:
        duplicate_index = ["year"]

    if region_df[duplicate_index].duplicated().any():
        raise ValueError(
            f"{dataset_name} contains duplicate region-year rows"
        )

    available_years = sorted(region_df["year"].unique())

    start_candidates = [
        year for year in available_years
        if year <= start_year
    ]

    end_candidates = [
        year for year in available_years
        if year <= end_year
    ]

    if not start_candidates:
        return None

    if not end_candidates:
        return None

    actual_start_year = max(start_candidates)
    actual_end_year = max(end_candidates)

    if actual_start_year == actual_end_year:
        return None

    start_row = region_df.loc[
        region_df["year"] == actual_start_year
    ].iloc[0]

    end_row = region_df.loc[
        region_df["year"] == actual_end_year
    ].iloc[0]

    start_value = float(start_row[value_column])
    end_value = float(end_row[value_column])

    absolute_change = end_value - start_value

    if start_value == 0:
        relative_change_pct = None
    else:
        relative_change_pct = (
            absolute_change / start_value
        ) * 100

    return {
        "dataset": dataset_name,

        # election comparison period
        "election_start_year": int(start_year),
        "election_end_year": int(end_year),

        # actual indicator observations used
        "indicator_start_year": int(actual_start_year),
        "indicator_end_year": int(actual_end_year),

        "start_value": start_value,
        "end_value": end_value,

        "absolute_change": absolute_change,
        "relative_change_pct": relative_change_pct,
    }