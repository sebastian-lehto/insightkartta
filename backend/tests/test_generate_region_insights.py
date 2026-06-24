import pandas as pd

from backend.pipelines.analysis.generate_region_insights import (
    build_region_insight,
    derive_periods,
)


def test_derive_periods_pairs_consecutive_years():
    assert derive_periods([2012, 2017, 2021, 2025]) == [
        (2012, 2017),
        (2017, 2021),
        (2021, 2025),
    ]


def test_derive_periods_handles_a_single_year():
    assert derive_periods([2025]) == []


def test_region_insight_periods_are_most_recent_first():
    region_df = pd.DataFrame(
        [
            {
                "region_code": "KU091",
                "region_name": "Helsinki",
                "year": year,
                "party_raw": "Centre Party",
                "party_name": "Centre Party",
                "party_code": "KESK",
                "votes": 500 + year,
                "vote_share_pct": 5.0,
            }
            for year in (2017, 2021, 2025)
        ]
    )
    periods = [(2017, 2021), (2021, 2025)]
    baselines_by_period = {(2017, 2021): {}, (2021, 2025): {}}

    insight = build_region_insight(region_df, {}, baselines_by_period, periods)

    assert [p["election_summary"] for p in insight["periods"]] == [
        {"latest_year": 2025, "previous_year": 2021},
        {"latest_year": 2021, "previous_year": 2017},
    ]
