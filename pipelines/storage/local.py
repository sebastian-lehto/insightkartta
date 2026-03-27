import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class LocalStorage:
    def __init__(self, base_path: str = "data/raw"):
        self.base_path = Path(base_path)

    def save(self, dataset_name: str, data: dict) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        dataset_path = self.base_path / dataset_name
        dataset_path.mkdir(parents=True, exist_ok=True)

        file_path = dataset_path / f"{timestamp}.json"

        wrapper = {
            "metadata": {
                "dataset": dataset_name,
                "timestamp": timestamp,
            },
            "data": data,
        }

        with open(file_path, "w") as f:
            json.dump(wrapper, f, indent=2)

        logger.info(f"Saved dataset to {file_path}")

        return file_path