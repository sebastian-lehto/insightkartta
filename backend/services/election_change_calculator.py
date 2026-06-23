from __future__ import annotations

import pandas as pd


def calculate_party_changes(region_df: pd.DataFrame) -> list[dict]:
    """
    Calculate party-level election changes between the two latest
    elections available for a municipality.
    """

    years = sorted(region_df["year"].unique())

    if len(years) < 2:
        return []

    latest_year = years[-1]
    previous_year = years[-2]

    latest = (
        region_df[region_df["year"] == latest_year][
            [
                "party_raw",
                "party_name",
                "party_code",
                "votes",
                "vote_share_pct",
            ]
        ]
        .rename(
            columns={
                "votes": "votes_latest",
                "vote_share_pct": "vote_share_latest",
            }
        )
        .copy()
    )

    previous = (
        region_df[region_df["year"] == previous_year][
            [
                "party_raw",
                "party_name",
                "party_code",
                "votes",
                "vote_share_pct",
            ]
        ]
        .rename(
            columns={
                "votes": "votes_previous",
                "vote_share_pct": "vote_share_previous",
            }
        )
        .copy()
    )

    merged = latest.merge(
        previous,
        on="party_raw",
        how="outer",
        suffixes=("_latest", "_previous"),
    )

    merged["party_name"] = merged["party_name_latest"].fillna(
        merged["party_name_previous"]
    )
    merged["party_code"] = merged["party_code_latest"].fillna(
        merged["party_code_previous"]
    )

    merged["votes_latest"] = merged["votes_latest"].fillna(0)
    merged["votes_previous"] = merged["votes_previous"].fillna(0)

    merged["vote_share_latest"] = merged["vote_share_latest"].fillna(0)
    merged["vote_share_previous"] = merged["vote_share_previous"].fillna(0)

    merged["vote_change"] = (
        merged["votes_latest"]
        - merged["votes_previous"]
    )

    merged["vote_share_change_pct"] = (
        merged["vote_share_latest"]
        - merged["vote_share_previous"]
    )

    merged = merged.sort_values(
        by="vote_share_change_pct",
        ascending=False,
    )

    records: list[dict] = []

    for _, row in merged.iterrows():
        records.append(
            {
                "party": row["party_raw"],
                "party_name": row["party_name"],
                "party_code": row["party_code"],
                "votes_latest": int(row["votes_latest"]),
                "votes_previous": int(row["votes_previous"]),
                "vote_change": int(row["vote_change"]),
                "vote_share_latest": float(row["vote_share_latest"]),
                "vote_share_previous": float(row["vote_share_previous"]),
                "vote_share_change_pct": float(
                    row["vote_share_change_pct"]
                ),
            }
        )

    return records