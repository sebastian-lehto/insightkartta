from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd
from bs4 import BeautifulSoup, Tag

LOGGER = logging.getLogger(__name__)
DATASET_NAME = "municipal_elections_party_votes"
PARTY_TABLE_CLASS = "tulosPuolueTaulu"
PARTY_ROW_CLASS = "clickable"


@dataclass(frozen=True)
class PartyResultRow:
    region: str
    year: int
    party_raw: str
    votes: int
    vote_share_pct: Optional[float]
    seats: Optional[int]
    vote_delta: Optional[int]
    vote_share_delta_pct: Optional[float]
    seats_delta: Optional[int]
    total_votes_cast: Optional[int]
    total_valid_votes: Optional[int]
    total_seats: Optional[int]
    invalid_votes_total: Optional[int]
    source_url: str


class ParseError(RuntimeError):
    """Raised when expected election-result structure is missing or malformed."""


class MunicipalElectionPartyParser:
    """
    Parse municipality-level party rows from official election result HTML.

    Important:
    The page repeats class names later in the row for comparisons to regional elections.
    To avoid mixing metrics, we parse the first 7 cells by position for party rows.
    """

    _SHOW_PREFIX_RE = re.compile(
        r"^Show\s+(advance|rejected)\s+votes\s+and\s+election\s+day\s+votes\s+",
        flags=re.IGNORECASE,
    )

    def parse_html(self, *, html: str, region: str, year: int, source_url: str) -> list[PartyResultRow]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_=PARTY_TABLE_CLASS)
        if table is None:
            raise ParseError(f"No table.{PARTY_TABLE_CLASS} found for {region} {year}")

        total_votes_cast, total_seats, invalid_votes_total = self._extract_totals(table)

        total_valid_votes = None
        if total_votes_cast is not None and invalid_votes_total is not None:
            total_valid_votes = total_votes_cast - invalid_votes_total

        rows: list[PartyResultRow] = []
        tbody = table.find("tbody") or table
        for tr in tbody.find_all("tr"):
            classes = tr.get("class", [])
            if PARTY_ROW_CLASS not in classes:
                continue

            cells = tr.find_all("td")
            if not cells:
                continue

            # Skip totals row.
            if any("tulosPuolueYhteensa" in td.get("class", []) for td in cells):
                continue

            # Skip rejected/invalid vote summary row.
            if self._is_invalid_votes_row(cells):
                continue

            rows.append(
                self._parse_party_row(
                    tr=tr,
                    region=region,
                    year=year,
                    source_url=source_url,
                    total_votes_cast=total_votes_cast,
                    total_valid_votes=total_valid_votes,
                    total_seats=total_seats,
                    invalid_votes_total=invalid_votes_total,
                )
            )

        if not rows:
            raise ParseError(f"No party rows parsed for {region} {year}")
        return rows

    def _extract_totals(self, table: Tag) -> tuple[int | None, int | None, int | None]:
        total_votes_cast: int | None = None
        total_seats: int | None = None
        invalid_votes_total: int | None = None

        tbody = table.find("tbody") or table
        for tr in tbody.find_all("tr"):
            cells = tr.find_all("td")
            if not cells:
                continue

            # Totals row
            if any("tulosPuolueYhteensa" in td.get("class", []) for td in cells):
                valid_votes_cell = self._find_cell_with_classes(cells, {"vahvaYhteensa", "puoAan"})
                total_seats_cell = self._find_cell_with_classes(cells, {"vahvaYhteensa", "puoPaik"})

                if valid_votes_cell is not None:
                    total_votes_cast = self._parse_int(valid_votes_cell.get_text(" ", strip=True))
                if total_seats_cell is not None:
                    total_seats = self._parse_int(total_seats_cell.get_text(" ", strip=True))

            # Rejected / invalid votes row
            elif self._is_invalid_votes_row(cells):
                invalid_votes_cell = self._find_cell_with_classes(cells, {"colorGreyMitaton", "puoAan"})
                if invalid_votes_cell is not None:
                    invalid_votes_total = self._parse_int(invalid_votes_cell.get_text(" ", strip=True))

        return total_votes_cast, total_seats, invalid_votes_total

    def _parse_party_row(
        self,
        *,
        tr: Tag,
        region: str,
        year: int,
        source_url: str,
        total_votes_cast: Optional[int],
        total_valid_votes: Optional[int],
        total_seats: Optional[int],
        invalid_votes_total: Optional[int],
    ) -> PartyResultRow:
        cells = tr.find_all("td")
        if len(cells) < 7:
            raise ParseError(f"Expected at least 7 cells in party row for {region} {year}, found {len(cells)}")

        party_raw = self._extract_party_name(cells[0])
        votes = self._parse_required_int(cells[1].get_text(" ", strip=True), field_name="votes")
        vote_share_pct = self._parse_float(cells[2].get_text(" ", strip=True))
        seats = self._parse_int(cells[3].get_text(" ", strip=True))
        vote_delta = self._parse_int(cells[4].get_text(" ", strip=True))
        vote_share_delta_pct = self._parse_float(cells[5].get_text(" ", strip=True))
        seats_delta = self._parse_int(cells[6].get_text(" ", strip=True))

        return PartyResultRow(
            region=region,
            year=year,
            party_raw=party_raw,
            votes=votes,
            vote_share_pct=vote_share_pct,
            seats=seats,
            vote_delta=vote_delta,
            vote_share_delta_pct=vote_share_delta_pct,
            seats_delta=seats_delta,
            total_votes_cast=total_votes_cast,
            total_valid_votes=total_valid_votes,
            total_seats=total_seats,
            invalid_votes_total=invalid_votes_total,
            source_url=source_url,
        )

    def _extract_party_name(self, cell: Tag) -> str:
        raw_text = self._normalize_space(cell.get_text(" ", strip=True))
        cleaned = self._SHOW_PREFIX_RE.sub("", raw_text)
        cleaned = self._normalize_space(cleaned)

        # Defensive guard in case helper text changes but still leaks through.
        if cleaned.lower().startswith("show "):
            parts = cleaned.split(" votes ", 1)
            if len(parts) == 2:
                cleaned = self._normalize_space(parts[1])

        return cleaned

    @staticmethod
    def _find_cell_with_classes(cells: list[Tag], required_classes: set[str]) -> Tag | None:
        for td in cells:
            td_classes = set(td.get("class", []))
            if required_classes.issubset(td_classes):
                return td
        return None

    def _is_invalid_votes_row(self, cells: list[Tag]) -> bool:
        if self._find_cell_with_classes(cells, {"colorGreyMitaton", "puoAan"}) is not None:
            return True

        first_text = self._normalize_space(cells[0].get_text(" ", strip=True)).lower()
        return "rejected votes" in first_text

    @staticmethod
    def _normalize_space(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _parse_required_int(value: str, *, field_name: str) -> int:
        parsed = MunicipalElectionPartyParser._parse_int(value)
        if parsed is None:
            raise ParseError(f"Could not parse required integer field {field_name}: {value!r}")
        return parsed

    @staticmethod
    def _parse_int(value: str) -> Optional[int]:
        normalized = value.strip().replace("\xa0", " ")
        if normalized in {"", "-", "–"}:
            return None
        normalized = re.sub(r"[^\d\-]", "", normalized)
        if normalized in {"", "-"}:
            return None
        return int(normalized)

    @staticmethod
    def _parse_float(value: str) -> Optional[float]:
        normalized = value.strip().replace("\xa0", " ").replace("%", "").replace(",", ".")
        normalized = re.sub(r"[^0-9.\-]", "", normalized)
        if normalized in {"", "-", ".", "-."}:
            return None
        return float(normalized)


def load_manifests(raw_dataset_root: Path) -> list[dict]:
    manifests = []
    for manifest_path in sorted(raw_dataset_root.glob("*/*.manifest.json")):
        manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))
    if not manifests:
        raise ValueError(f"No manifest files found under {raw_dataset_root}")
    return manifests


def load_region_mapping(region_mapping_path: Path) -> pd.DataFrame:
    df = pd.read_csv(region_mapping_path)

    required_cols = {"region_code", "region_name"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"region_mapping.csv must contain columns: {sorted(required_cols)}. "
            f"Missing: {sorted(missing_cols)}"
        )

    return df.rename(columns={"region_code": "region"})


def load_party_mapping(party_mapping_path: Path | None) -> pd.DataFrame | None:
    if party_mapping_path is None or not party_mapping_path.exists():
        return None
    return pd.read_csv(party_mapping_path)


def normalize_rows(manifests: list[dict]) -> pd.DataFrame:
    parser = MunicipalElectionPartyParser()
    parsed_rows: list[dict] = []

    for manifest in manifests:
        status = manifest.get("status", "ok")
        html_path_value = manifest.get("html_path")

        if status != "ok":
            LOGGER.info(
                "Skipping manifest for %s %s because status=%s",
                manifest.get("year"),
                manifest.get("region"),
                status,
            )
            continue

        if not html_path_value:
            LOGGER.warning(
                "Skipping manifest for %s %s because html_path is missing",
                manifest.get("year"),
                manifest.get("region"),
            )
            continue

        html_path = Path(html_path_value)
        if not html_path.exists():
            LOGGER.warning(
                "Skipping manifest for %s %s because html file does not exist: %s",
                manifest.get("year"),
                manifest.get("region"),
                html_path,
            )
            continue

        html = html_path.read_text(encoding="utf-8")
        rows = parser.parse_html(
            html=html,
            region=manifest["region"],
            year=int(manifest["year"]),
            source_url=manifest["source_url"],
        )
        for row in rows:
            parsed_rows.append(row.__dict__)

    if not parsed_rows:
        raise ValueError("No parsed election rows produced")
    return pd.DataFrame(parsed_rows)


def validate_dataset(df: pd.DataFrame) -> None:
    required_columns = {
        "region",
        "year",
        "party_raw",
        "votes",
        "vote_share_pct",
        "seats",
        "total_valid_votes",
    }
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required parsed columns: {sorted(missing)}")

    if df[["region", "year", "party_raw"]].duplicated().any():
        dupes = df.loc[
            df[["region", "year", "party_raw"]].duplicated(keep=False),
            ["region", "year", "party_raw"],
        ]
        raise ValueError(f"Duplicate municipality-year-party rows found:\n{dupes.head(20)}")

    if (df["votes"] < 0).any():
        raise ValueError("Negative votes found, which should be impossible")

    totals = (
        df.groupby(["region", "year"], dropna=False)["votes"].sum().reset_index(name="party_vote_sum")
        .merge(
            df.groupby(["region", "year"], dropna=False)["total_valid_votes"].max().reset_index(),
            on=["region", "year"],
            how="left",
        )
    )

    mismatched = totals[
        totals["total_valid_votes"].notna() & (totals["party_vote_sum"] != totals["total_valid_votes"])
    ]

    if not mismatched.empty:
        raise ValueError(
            "Sum of party votes did not match total_valid_votes for some municipality-years. "
            "This usually means totals or invalid votes were parsed incorrectly.\n"
            f"{mismatched.head(20).to_string(index=False)}"
        )


def write_processed_dataset(df: pd.DataFrame, output_root: Path, dataset_name: str) -> Path:
    dataset_dir = output_root / dataset_name
    dataset_dir.mkdir(parents=True, exist_ok=True)
    latest_path = dataset_dir / "latest.csv"
    df.sort_values(["year", "region", "party_code", "party_raw"]).to_csv(latest_path, index=False)
    return latest_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize municipal election party totals from raw HTML.")
    parser.add_argument("--raw-dataset-root", type=Path, default=Path(f"backend/data/raw/{DATASET_NAME}"))
    parser.add_argument("--processed-root", type=Path, default=Path("backend/data/processed"))
    parser.add_argument("--region-mapping", type=Path, default=Path("backend/data/region_mapping.csv"))
    parser.add_argument("--party-mapping", type=Path, default=Path("backend/data/party_mapping.csv"))
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = parse_args()

    manifests = load_manifests(args.raw_dataset_root)
    LOGGER.info("Loaded %s raw manifest entries", len(manifests))

    df = normalize_rows(manifests)
    LOGGER.info("Parsed %s election party rows", len(df))

    region_mapping_df = load_region_mapping(args.region_mapping)

    df = df.merge(
        region_mapping_df[["region", "region_name"]],
        on="region",
        how="left",
    )

    if df["region_name"].isna().any():
        missing = sorted(df.loc[df["region_name"].isna(), "region"].unique().tolist())
        raise ValueError(f"Missing region_name mapping for regions: {missing[:20]}")

    party_mapping_df = load_party_mapping(args.party_mapping)
    if party_mapping_df is not None:
        df = df.merge(party_mapping_df, on="party_raw", how="left")
    else:
        df["party_code"] = df["party_raw"]
        df["party_name"] = df["party_raw"]

    df["election_type"] = "municipal"
    df["source_type"] = "official_html"
    df["value"] = df["votes"]

    validate_dataset(df)

    output_path = write_processed_dataset(df, args.processed_root, DATASET_NAME)
    LOGGER.info("Wrote processed dataset to %s", output_path)


if __name__ == "__main__":
    main()