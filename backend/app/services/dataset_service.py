import pandas as pd
import yaml
import json
from pathlib import Path

from backend.pipelines.analysis.engine import AnalysisEngine
from backend.app.utils.serialization import clean_dict


CONFIG_PATH = "backend/pipelines/config/datasets.yaml"
PROCESSED_BASE = Path("backend/data/processed")
ANALYSIS_BASE = Path("backend/data/analysis")


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_dataset_config(name):
    config = load_config()
    return next(d for d in config["datasets"] if d["name"] == name)


def list_datasets():
    config = load_config()

    return [
        {
            "name": d["name"],
            "label": d.get("metadata", {}).get("label", d["name"]),
        }
        for d in config["datasets"]
    ]


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