from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd
import yaml

from backend.services.election_change_calculator import calculate_party_changes
from backend.services.indicator_change_calculator import calculate_indicator_change
from backend.services.relationship_calculator import (
    calculate_indicator_relationships,
    calculate_national_correlations,
    compute_indicator_baselines,
)

LOGGER = logging.getLogger(__name__)

ELECTION_DATASET = "municipal_elections_party_votes"
CONFIG_PATH = Path("backend/pipelines/config/datasets.yaml")
PROCESSED_BASE = Path("backend/data/processed")
ANALYSIS_BASE = Path("backend/data/analysis")


def build_indicator_datasets() -> dict[str, str]:
    """Derive indicator dataset paths from datasets.yaml instead of hardcoding them."""
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    return {
        d["name"]: str(PROCESSED_BASE / d["name"] / "latest.csv")
        for d in config.get("datasets", [])
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

    for dataset_name, path_str in build_indicator_datasets().items():
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
    baselines: dict[str, dict],
) -> dict:
    region_code = str(region_df["region_code"].iloc[0])
    region_name = str(region_df["region_name"].iloc[0])

    years = sorted(region_df["year"].unique())

    latest_year = int(years[-1])
    previous_year = int(years[-2]) if len(years) >= 2 else None

    party_changes = calculate_party_changes(region_df)

    indicators: dict[str, dict] = {}

    for dataset_name, indicator_df in indicator_frames.items():
        municipality_df = indicator_df[
            indicator_df["region_code"] == region_code
        ]

        change = calculate_indicator_change(
            dataset_name=dataset_name,
            region_df=municipality_df,
            start_year=previous_year,
            end_year=latest_year,
        )

        if change is not None:
            indicators[dataset_name] = change

    indicator_relationships = calculate_indicator_relationships(indicators, baselines)

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
        "indicator_relationships": indicator_relationships,
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
        ),
        encoding="utf-8",
    )


def write_national_correlations(
    correlations: dict,
    election_year: int,
    previous_election_year: int,
) -> None:
    output = {
        str(election_year): {
            "election_period": {
                "start": previous_election_year,
                "end": election_year,
            },
            "correlations": correlations,
        }
    }

    ANALYSIS_BASE.mkdir(parents=True, exist_ok=True)
    path = ANALYSIS_BASE / "election_indicator_correlations.json"
    path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    LOGGER.info("Written national correlations to %s", path)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    args = parse_args()

    df = pd.read_csv(args.elections_path)

    required_columns = {
        "region_code",
        "region_name",
        "year",
        "party_raw",
        "party_name",
        "party_code",
        "votes",
        "vote_share_pct",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Election dataset missing required columns: {sorted(missing)}"
        )

    election_years = sorted(df["year"].unique())
    latest_year = int(election_years[-1])
    previous_year = int(election_years[-2]) if len(election_years) >= 2 else None

    indicator_frames = load_indicator_datasets()

    baselines = compute_indicator_baselines(
        indicator_frames,
        start_year=previous_year,
        end_year=latest_year,
    )

    regions = sorted(df["region_code"].unique())

    LOGGER.info(
        "Generating insights for %s regions",
        len(regions),
    )

    for region in regions:
        region_df = df[df["region_code"] == region]
        insight = build_region_insight(region_df, indicator_frames, baselines)
        write_region_insight(insight, args.output_dir)

    LOGGER.info(
        "Generated %s region insight files",
        len(regions),
    )

    if previous_year is not None:
        correlations = calculate_national_correlations(
            elections_df=df,
            indicator_frames=indicator_frames,
            election_year=latest_year,
            previous_election_year=previous_year,
        )
        write_national_correlations(
            correlations=correlations,
            election_year=latest_year,
            previous_election_year=previous_year,
        )


if __name__ == "__main__":
    main()
