import pandas as pd

from backend.services.relationship_calculator import (
    calculate_indicator_relationships,
    calculate_national_correlations,
    compute_indicator_baselines,
)
from backend.services.indicator_change_calculator import calculate_indicator_change


def _indicator_df(rows):
    return pd.DataFrame(rows, columns=["region_code", "year", "value"])


def test_baseline_uses_mean_of_municipalities_not_the_national_sum():
    """Regression test for CONTEXT.md §10.9: for an absolute-count indicator
    like population, the SSS row is Finland's total change (a large sum),
    not a per-municipality average. Using it as the baseline made every
    single municipality look "below average". mean_municipal_change must be
    the small per-municipality figure, clearly different from the SSS total.
    """
    indicator_frames = {
        "population": _indicator_df(
            [
                ("SSS", 2021, 5_000_000),
                ("SSS", 2025, 5_104_000),  # national total change: +104,000
                ("KU091", 2021, 600_000),
                ("KU091", 2025, 600_500),  # +500
                ("KU092", 2021, 50_000),
                ("KU092", 2025, 50_300),  # +300
            ]
        )
    }

    baselines = compute_indicator_baselines(indicator_frames, start_year=2021, end_year=2025)
    population_baseline = baselines["population"]

    assert population_baseline["national_change"] == 104_000
    # mean of (+500, +300) = 400 — nowhere near the national total.
    assert population_baseline["mean_municipal_change"] == 400.0


def test_indicator_relationships_uses_mean_municipal_change_as_national_reference():
    indicator_frames = {
        "population": _indicator_df(
            [
                ("SSS", 2021, 5_000_000),
                ("SSS", 2025, 5_104_000),
                ("KU091", 2021, 600_000),
                ("KU091", 2025, 600_500),
                ("KU092", 2021, 50_000),
                ("KU092", 2025, 50_300),
            ]
        )
    }
    baselines = compute_indicator_baselines(indicator_frames, start_year=2021, end_year=2025)

    helsinki_change = calculate_indicator_change(
        dataset_name="population",
        region_df=indicator_frames["population"][indicator_frames["population"]["region_code"] == "KU091"],
        start_year=2021,
        end_year=2025,
    )

    relationships = calculate_indicator_relationships({"population": helsinki_change}, baselines)

    # national_absolute_change must equal the mean-of-municipalities baseline
    # (400), never the SSS row's 104,000.
    assert relationships["population"]["national_absolute_change"] == 400.0
    assert relationships["population"]["data_status"] == "complete"


def _elections_and_indicator_fixture(n_municipalities=12):
    election_rows = []
    indicator_rows = []

    for i in range(1, n_municipalities + 1):
        region_code = f"KU{i:03d}"
        previous_share = 10.0
        latest_share = previous_share + 0.5 * i  # vote_share_change = 0.5 * i

        election_rows.append(
            {
                "region_code": region_code,
                "party_code": "VIHR",
                "party_name": "The Greens",
                "vote_share_pct": previous_share,
                "year": 2021,
            }
        )
        election_rows.append(
            {
                "region_code": region_code,
                "party_code": "VIHR",
                "party_name": "The Greens",
                "vote_share_pct": latest_share,
                "year": 2025,
            }
        )

        indicator_rows.append((region_code, 2021, 10.0))
        indicator_rows.append((region_code, 2025, 10.0 + i))  # absolute_change = i

    elections_df = pd.DataFrame(election_rows)
    indicator_frames = {"unemployment": _indicator_df(indicator_rows)}
    return elections_df, indicator_frames


def test_national_correlations_detects_a_real_relationship():
    elections_df, indicator_frames = _elections_and_indicator_fixture()

    correlations = calculate_national_correlations(
        elections_df=elections_df,
        indicator_frames=indicator_frames,
        election_year=2025,
        previous_election_year=2021,
    )

    vihr = correlations["unemployment"]["VIHR"]
    assert vihr["classification"] == "strong_positive"
    assert vihr["pearson_r"] > 0.99
    assert vihr["n"] == 12


def test_national_correlations_skips_nan_correlation_without_crashing():
    """A constant indicator change across all municipalities makes the
    correlation undefined (zero variance => NaN). The function must skip
    that party/dataset pair instead of raising or returning NaN.
    """
    elections_df, indicator_frames = _elections_and_indicator_fixture()
    # Flatten every municipality's indicator change to the same value.
    indicator_frames["unemployment"]["value"] = 10.0

    correlations = calculate_national_correlations(
        elections_df=elections_df,
        indicator_frames=indicator_frames,
        election_year=2025,
        previous_election_year=2021,
    )

    assert "unemployment" not in correlations
