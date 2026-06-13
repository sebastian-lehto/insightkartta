from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from backend.services.election_change_calculator import calculate_party_changes
from backend.services.indicator_change_calculator import calculate_indicator_change

LOGGER = logging.getLogger(__name__)

ELECTION_DATASET = "municipal_elections_party_votes"

INDICATOR_DATASETS = {
    "population": "backend/data/processed/population/latest.csv",
    "unemployment": "backend/data/processed/unemployment/latest.csv",
    "education_upper_secondary": "backend/data/processed/education_upper_secondary/latest.csv",
    "education_tertiary": "backend/data/processed/education_tertiary/latest.csv",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate municipality election insight JSON files."
    )

    parser.add_argument(
        "--elections-path",
        type=Path,
        default=Path(
            f"backend/data/processed/{ELECTION_DATASET}/latest.csv"
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "backend/data/analysis/region_insights"
        ),
    )

    return parser.parse_args()

def load_indicator_datasets() -> dict[str, pd.DataFrame]:
    datasets: dict[str, pd.DataFrame] = {}

    for dataset_name, path_str in INDICATOR_DATASETS.items():
        path = Path(path_str)

        if not path.exists():
            LOGGER.warning(
                "Indicator dataset not found: %s",
                path,
            )
            continue

        datasets[dataset_name] = pd.read_csv(path)

    return datasets

def build_region_insight(
    region_df: pd.DataFrame,
    indicator_frames: dict[str, pd.DataFrame],
) -> dict:
    region_code = str(region_df["region"].iloc[0])
    region_name = str(region_df["region_name"].iloc[0])

    years = sorted(region_df["year"].unique())

    latest_year = int(years[-1])
    previous_year = int(years[-2]) if len(years) >= 2 else None

    party_changes = calculate_party_changes(region_df)

    indicators: dict[str, dict] = {}

    for dataset_name, indicator_df in indicator_frames.items():
        municipality_df = indicator_df[
            indicator_df["region"] == region_code
        ]

        change = calculate_indicator_change(
            dataset_name=dataset_name,
            region_df=municipality_df,
            start_year=previous_year,
            end_year=latest_year,
        )

        if change is not None:
            indicators[dataset_name] = change

    return {
        "region": {
            "code": region_code,
            "name": region_name,
        },
        "election_summary": {
            "latest_year": latest_year,
            "previous_year": previous_year,
        },
        "party_changes": party_changes,
        "indicators": indicators,
    }

def write_region_insight(
    insight: dict,
    output_dir: Path,
) -> None:
    region_code = insight["region"]["code"]

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = output_dir / f"{region_code}.json"

    output_path.write_text(
        json.dumps(
            insight,
            ensure_ascii=False,
            indent=2,
            default=int,
        ),
        encoding="utf-8",
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    args = parse_args()

    df = pd.read_csv(args.elections_path)

    required_columns = {
        "region",
        "region_name",
        "year",
        "party_raw",
        "votes",
        "vote_share_pct",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Election dataset missing required columns: {sorted(missing)}"
        )

    regions = sorted(df["region"].unique())

    LOGGER.info(
        "Generating insights for %s regions",
        len(regions),
    )

    for region in regions:
        region_df = df[df["region"] == region]

        indicator_frames = load_indicator_datasets()
        insight = build_region_insight(region_df, indicator_frames)

        write_region_insight(
            insight,
            args.output_dir,
        )

    LOGGER.info(
        "Generated %s region insight files",
        len(regions),
    )


if __name__ == "__main__":
    main()