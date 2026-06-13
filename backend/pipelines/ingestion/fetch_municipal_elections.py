from __future__ import annotations

import argparse
import csv
import json
import logging
from pathlib import Path
from typing import Iterable

from backend.pipelines.ingestion.sources.vaalit_html_client import FetchTarget, VaalitHtmlClient

LOGGER = logging.getLogger(__name__)
DEFAULT_YEARS = (2012, 2017, 2021, 2025)
DEFAULT_DATASET_NAME = "municipal_elections_party_votes"


def load_municipality_codes(region_mapping_path: Path) -> list[str]:
    with region_mapping_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        codes = []
        for row in reader:
            region = row.get("region") or row.get("region_code") or row.get("code")
            if region and region.startswith("KU") and len(region) == 5:
                codes.append(region)
    deduped = sorted(set(codes))
    if not deduped:
        raise ValueError(f"No municipality codes found in {region_mapping_path}")
    return deduped


def build_targets(years: Iterable[int], municipality_codes: Iterable[str]) -> list[FetchTarget]:
    return [FetchTarget(year=year, region=code) for year in years for code in municipality_codes]


def write_fetch_report(results: list, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serializable = [result.__dict__ for result in results]
    output_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch municipal election result pages from tulospalvelu.vaalit.fi")
    parser.add_argument("--region-mapping", type=Path, default=Path("backend/data/region_mapping.csv"))
    parser.add_argument("--raw-root", type=Path, default=Path("backend/data/raw"))
    parser.add_argument("--dataset-name", default=DEFAULT_DATASET_NAME)
    parser.add_argument("--years", nargs="*", type=int, default=list(DEFAULT_YEARS))
    parser.add_argument("--report-path", type=Path, default=Path("backend/data/raw/reports/municipal_elections_fetch_report.json"))
    parser.add_argument("--overwrite", action="store_true", help="Refetch even if raw HTML already exists")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = parse_args()

    municipality_codes = load_municipality_codes(args.region_mapping)
    LOGGER.info("Loaded %s municipality codes from %s", len(municipality_codes), args.region_mapping)

    targets = build_targets(args.years, municipality_codes)
    LOGGER.info("Fetching %s municipality-year pages", len(targets))

    client = VaalitHtmlClient(dataset_name=args.dataset_name, raw_root=args.raw_root, overwrite=args.overwrite)
    results = client.fetch_many(targets)

    ok_count = sum(1 for r in results if r.status == "ok")
    not_found_count = sum(1 for r in results if r.status == "not_found")
    error_count = sum(1 for r in results if r.status == "error")

    LOGGER.info(f"Fetched successfully: {ok_count}")
    LOGGER.info(f"Not found: {not_found_count}")
    LOGGER.info(f"Errors: {error_count}")

    write_fetch_report(results, args.report_path)
    LOGGER.info("Wrote fetch report to %s", args.report_path)


if __name__ == "__main__":
    main()
