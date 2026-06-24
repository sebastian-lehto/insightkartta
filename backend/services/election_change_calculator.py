from __future__ import annotations

import pandas as pd


def calculate_party_changes(
    region_df: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> list[dict]:
    """
    Calculate party-level election changes between two specific
    elections for a municipality.
    """

    available_years = set(region_df["year"].unique())

    if start_year not in available_years or end_year not in available_years:
        return []

    latest_year = end_year
    previous_year = start_year

    # Joined on party_code rather than party_raw/party_name: the same party's
    # English label has been re-translated between some election cycles (e.g.
    # "Green League" -> "The Greens"), while party_code stays stable.
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
        on="party_code",
        how="outer",
        suffixes=("_latest", "_previous"),
    )

    merged["party_raw"] = merged["party_raw_latest"].fillna(
        merged["party_raw_previous"]
    )
    merged["party_name"] = merged["party_name_latest"].fillna(
        merged["party_name_previous"]
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