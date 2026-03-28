import yaml
from pathlib import Path
from typing import Dict, Any


def load_config(path: str) -> Dict[str, Any]:
    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(config_path, "r") as f:
        return yaml.safe_load(f)