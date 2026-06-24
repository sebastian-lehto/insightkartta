import pandas as pd

from backend.services.election_change_calculator import calculate_party_changes


def _row(year, party_raw, party_code, votes, vote_share_pct, party_name="Vihreä liitto"):
    return {
        "year": year,
        "party_raw": party_raw,
        "party_name": party_name,
        "party_code": party_code,
        "votes": votes,
        "vote_share_pct": vote_share_pct,
    }


def test_join_on_party_code_survives_a_relabeled_party_raw():
    """Regression test for CONTEXT.md §10.13: party_raw for VIHR was
    re-translated from "Green League" (2012/2017) to "The Greens" (2021/2025).
    Joining on party_raw made the party look brand new across that boundary —
    a 0-vote 'previous' instead of its real prior vote count. party_code is
    stable and must be the join key.
    """
    df = pd.DataFrame(
        [
            _row(2017, "Green League", "VIHR", votes=1000, vote_share_pct=10.0),
            _row(2021, "The Greens", "VIHR", votes=1200, vote_share_pct=12.0),
        ]
    )

    records = calculate_party_changes(df, start_year=2017, end_year=2021)

    assert len(records) == 1
    record = records[0]
    assert record["party_code"] == "VIHR"
    assert record["votes_previous"] == 1000
    assert record["votes_latest"] == 1200
    assert record["vote_change"] == 200
    assert record["vote_share_change_pct"] == 2.0


def test_party_only_present_in_latest_year_gets_zero_previous_votes():
    """A genuinely new party (no row in the previous election) should still
    show 0 previous votes — that's correct, unlike the relabeling case above.
    """
    df = pd.DataFrame(
        [
            _row(2017, "Centre Party", "KESK", votes=500, vote_share_pct=5.0),
            _row(2021, "Centre Party", "KESK", votes=520, vote_share_pct=5.2),
            _row(2021, "New Party", "NEW", votes=300, vote_share_pct=3.0, party_name="New Party"),
        ]
    )

    records = calculate_party_changes(df, start_year=2017, end_year=2021)
    new_party = next(r for r in records if r["party_code"] == "NEW")

    assert new_party["votes_previous"] == 0
    assert new_party["votes_latest"] == 300


def test_missing_year_returns_empty_list():
    df = pd.DataFrame([_row(2021, "Centre Party", "KESK", votes=500, vote_share_pct=5.0)])

    assert calculate_party_changes(df, start_year=2017, end_year=2021) == []
