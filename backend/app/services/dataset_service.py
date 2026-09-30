import pandas as pd
import yaml
import json
from pathlib import Path
from functools import lru_cache

from backend.pipelines.analysis.engine import AnalysisEngine
from backend.app.utils.serialization import clean_dict


CONFIG_PATH = "backend/pipelines/config/datasets.yaml"
PROCESSED_BASE = Path("backend/data/processed")
ANALYSIS_BASE = Path("backend/data/analysis")


@lru_cache(maxsize=1)
def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_all_dataset_configs():
    config = load_config()
    regular = config.get("datasets", [])
    postal = config.get("postal_code_datasets", [])
    return regular + postal


def get_dataset_config(name):
    match = next((d for d in get_all_dataset_configs() if d["name"] == name), None)
    if match is None:
        raise KeyError(f"Dataset '{name}' not found")
    return match


def list_datasets():
    return [
        {
            "name": d["name"],
            "label": d.get("metadata", {}).get("label", d["name"]),
            "group": d.get("group", "region"),
        }
        for d in get_all_dataset_configs()
    ]


def _normalize_region_key(value):
    return str(value or "").strip().lower().replace("_", " ").replace("-", " ")


def get_region_postal_code_comparison(
    region: str,
    year: int | None = None,
    sort_by: str | None = None,
    sort_desc: bool = True,
):
    region_key = _normalize_region_key(region)
    postal_configs = [
        config for config in get_all_dataset_configs()
        if config.get("group") == "postal_code" and config.get("source") == "paavo"
    ]
    available_years = set()
    regional_frames = {}

    for config in postal_configs:
        dataset_name = config["name"]
        try:
            df = load_processed(dataset_name)
        except FileNotFoundError:
            continue

        if "postal_code" not in df.columns:
            continue

        region_mask = (
            df["region_code"].fillna("").astype(str).str.strip().str.lower().eq(region_key)
            | df["region_name"].fillna("").astype(str).str.strip().str.lower().eq(region_key)
        )
        subset = df[region_mask].copy()
        if subset.empty:
            continue

        subset["year"] = pd.to_numeric(subset["year"], errors="coerce")
        available_years.update(int(value) for value in subset["year"].dropna().unique())
        regional_frames[dataset_name] = (config, subset)

    ordered_years = sorted(available_years)
    selected_year = year if year in available_years else (ordered_years[-1] if ordered_years else None)
    dataset_rows = []
    merged = {}

    for dataset_name, (config, subset) in regional_frames.items():
        latest = subset.sort_values("year").drop_duplicates(
            ["postal_code", "year"], keep="last"
        )
        keep_columns = [
            column for column in
            ("postal_code", "postal_code_name", "region_name", "year", "value")
            if column in latest.columns
        ]
        latest = latest[keep_columns].copy()
        latest["postal_code"] = latest["postal_code"].map(
            lambda code: str(code).strip().zfill(5) if str(code).strip().isdigit() else str(code).strip()
        )
        latest["value"] = pd.to_numeric(latest["value"], errors="coerce")

        dataset_rows.append({
            "name": dataset_name,
            "label": config.get("metadata", {}).get("label", dataset_name),
            "unit": config.get("metadata", {}).get("unit", ""),
            "summary": config.get("metadata", {}).get("visualization", {}).get("summary"),
            "bins": config.get("metadata", {}).get("visualization", {}).get("map", {}).get("bins", []),
        })

        for row in latest.to_dict(orient="records"):
            code = str(row["postal_code"]).strip()
            if code.isdigit():
                code = code.zfill(5)
            entry = merged.setdefault(code, {
                "postal_code": code,
                "region_name": row.get("region_name") or region,
                "postal_code_name": row.get("postal_code_name"),
                "history": {},
            })
            year_key = str(int(row["year"]))
            entry["history"].setdefault(year_key, {})[dataset_name] = row.get("value")

    for entry in merged.values():
        entry["year"] = selected_year
        entry.update(entry["history"].get(str(selected_year), {}))

    ordered_datasets = [
        {
            "name": item["name"],
            "label": item["label"],
            "unit": item["unit"],
            "summary": item["summary"],
            "bins": item["bins"],
        }
        for item in dataset_rows
    ]

    postal_codes = list(merged.values())
    if sort_by and any(row.get(sort_by) is not None for row in postal_codes):
        postal_codes = sorted(
            postal_codes,
            key=lambda item: float(item.get(sort_by) or 0),
            reverse=sort_desc,
        )
    else:
        postal_codes = sorted(
            postal_codes,
            key=lambda item: item["postal_code"],
        )

    return clean_dict({
        "region": region,
        "year": selected_year,
        "years": ordered_years,
        "datasets": ordered_datasets,
        "postal_codes": postal_codes,
    })


def load_processed(dataset_name: str):
    path = PROCESSED_BASE / dataset_name / "latest.csv"

    if not path.exists():
        raise FileNotFoundError(f"No processed data for {dataset_name}")

    return pd.read_csv(path)


def load_analysis(dataset_name: str):
    path = ANALYSIS_BASE / f"{dataset_name}.json"

    if not path.exists():
        return None

    with open(path) as f:
        return json.load(f)


def get_dataset(dataset_name: str):
    config = get_dataset_config(dataset_name)

    df = load_processed(dataset_name)
    analysis = load_analysis(dataset_name)

    return clean_dict({
        "data": df.to_dict(orient="records"),
        "meta": config.get("metadata", {}),
        "analysis": analysis,
    })