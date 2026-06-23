from __future__ import annotations

import pandas as pd

from backend.services.indicator_change_calculator import calculate_indicator_change

NATIONAL_REGION_CODE = "SSS"
MUNICIPALITY_PREFIX = "KU"
RELATIVE_THRESHOLD = 0.5
MIN_NATIONAL_VOTE_SHARE_PCT = 3.0
MIN_MUNICIPALITIES_FOR_CORRELATION = 10


def compute_indicator_baselines(
    indicator_frames: dict[str, pd.DataFrame],
    start_year: int,
    end_year: int,
) -> dict[str, dict]:
    """
    For each indicator, compute the national (SSS) change and the distribution
    (mean + std) of municipality-level changes over the given election period.

    Used to classify a region's indicator change as above/below/similar to
    the national picture.
    """
    baselines: dict[str, dict] = {}

    for dataset_name, df in indicator_frames.items():
        national_df = df[df["region_code"] == NATIONAL_REGION_CODE]
        national_result = calculate_indicator_change(
            dataset_name=dataset_name,
            region_df=national_df,
            start_year=start_year,
            end_year=end_year,
        )
        national_change = (
            float(national_result["absolute_change"]) if national_result else None
        )

        municipality_changes: list[float] = []
        for region_code in df["region_code"].unique():
            if not str(region_code).startswith(MUNICIPALITY_PREFIX):
                continue
            region_df = df[df["region_code"] == region_code]
            result = calculate_indicator_change(
                dataset_name=dataset_name,
                region_df=region_df,
                start_year=start_year,
                end_year=end_year,
            )
            if result is not None:
                municipality_changes.append(float(result["absolute_change"]))

        series = pd.Series(municipality_changes)
        baselines[dataset_name] = {
            "national_change": national_change,
            "mean_municipal_change": float(series.mean()) if len(series) > 0 else None,
            "std_municipal_change": float(series.std(ddof=0)) if len(series) > 0 else None,
        }

    return baselines


def _classify_relative(deviation: float, std: float | None) -> str:
    if not std:
        return "similar"
    normalized = deviation / std
    if normalized > RELATIVE_THRESHOLD:
        return "above_average"
    if normalized < -RELATIVE_THRESHOLD:
        return "below_average"
    return "similar"


def calculate_indicator_relationships(
    regional_indicators: dict,
    baselines: dict[str, dict],
) -> dict:
    """
    For each indicator with data in the region insight, add national context:
    how the regional change compares to the national picture for the same period.
    """
    relationships: dict = {}

    for dataset_name, indicator_data in regional_indicators.items():
        baseline = baselines.get(dataset_name)
        if baseline is None:
            continue

        mean_change = baseline["mean_municipal_change"]
        if mean_change is None:
            relationships[dataset_name] = {
                "election_period": {
                    "start": indicator_data["election_start_year"],
                    "end": indicator_data["election_end_year"],
                },
                "data_status": "no_national_data",
            }
            continue

        regional_change = float(indicator_data["absolute_change"])
        deviation = regional_change - mean_change
        relative = _classify_relative(deviation, baseline["std_municipal_change"])

        relationships[dataset_name] = {
            "election_period": {
                "start": indicator_data["election_start_year"],
                "end": indicator_data["election_end_year"],
            },
            "regional_absolute_change": round(regional_change, 4),
            "national_absolute_change": round(mean_change, 4),
            "deviation_from_national": round(deviation, 4),
            "relative_to_national": relative,
            "data_status": "complete",
        }

    return relationships


def _classify_correlation(r: float) -> str:
    abs_r = abs(r)
    direction = "positive" if r >= 0 else "negative"
    if abs_r < 0.1:
        return "none"
    if abs_r < 0.3:
        return f"weak_{direction}"
    if abs_r < 0.5:
        return f"moderate_{direction}"
    return f"strong_{direction}"


def calculate_national_correlations(
    elections_df: pd.DataFrame,
    indicator_frames: dict[str, pd.DataFrame],
    election_year: int,
    previous_election_year: int,
) -> dict[str, dict]:
    """
    For each indicator, compute Pearson correlation across all municipalities
    between the indicator change over the election period and vote share change
    for each major party (>= MIN_NATIONAL_VOTE_SHARE_PCT national average).

    Returns: {dataset_name: {party_code: {party_name, pearson_r, classification, n}}}
    """
    latest = elections_df[elections_df["year"] == election_year]
    previous = elections_df[elections_df["year"] == previous_election_year]

    vote_merged = latest[
        ["region_code", "party_code", "party_name", "vote_share_pct"]
    ].merge(
        previous[["region_code", "party_code", "vote_share_pct"]].rename(
            columns={"vote_share_pct": "vote_share_previous"}
        ),
        on=["region_code", "party_code"],
        how="inner",
    )
    vote_merged["vote_share_change"] = (
        vote_merged["vote_share_pct"] - vote_merged["vote_share_previous"]
    )

    national_avg = latest.groupby("party_code")["vote_share_pct"].mean().dropna()
    major_parties = national_avg[
        national_avg >= MIN_NATIONAL_VOTE_SHARE_PCT
    ].index.tolist()

    vote_pivot = vote_merged[
        vote_merged["party_code"].isin(major_parties)
    ].pivot_table(
        index="region_code",
        columns="party_code",
        values="vote_share_change",
        aggfunc="first",
    )

    party_names: dict[str, str] = (
        vote_merged[vote_merged["party_code"].isin(major_parties)]
        .drop_duplicates("party_code")
        .set_index("party_code")["party_name"]
        .to_dict()
    )

    correlations: dict[str, dict] = {}

    for dataset_name, indicator_df in indicator_frames.items():
        municipality_changes: dict[str, float] = {}
        for region_code in indicator_df["region_code"].unique():
            if not str(region_code).startswith(MUNICIPALITY_PREFIX):
                continue
            region_df = indicator_df[indicator_df["region_code"] == region_code]
            result = calculate_indicator_change(
                dataset_name=dataset_name,
                region_df=region_df,
                start_year=previous_election_year,
                end_year=election_year,
            )
            if result is not None:
                municipality_changes[region_code] = float(result["absolute_change"])

        if not municipality_changes:
            continue

        indicator_series = pd.Series(municipality_changes, name="indicator_change")
        joined = vote_pivot.join(indicator_series, how="inner").dropna(
            subset=["indicator_change"]
        )

        if len(joined) < MIN_MUNICIPALITIES_FOR_CORRELATION:
            continue

        party_correlations: dict[str, dict] = {}
        for party_code in major_parties:
            if party_code not in joined.columns:
                continue
            pair = joined[["indicator_change", party_code]].dropna()
            if len(pair) < MIN_MUNICIPALITIES_FOR_CORRELATION:
                continue
            r_val = pair.corr()["indicator_change"][party_code]
            if pd.isna(r_val):
                continue
            r = float(r_val)
            party_correlations[party_code] = {
                "party_name": str(party_names.get(party_code, party_code)),
                "pearson_r": round(r, 4),
                "classification": _classify_correlation(r),
                "n": int(len(pair)),
            }

        if party_correlations:
            correlations[dataset_name] = party_correlations

    return correlations
