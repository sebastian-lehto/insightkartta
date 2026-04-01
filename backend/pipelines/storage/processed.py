from pathlib import Path
from datetime import datetime
import pandas as pd


class ProcessedStorage:
    def __init__(self, base_path: str = "backend/data/processed"):
        self.base_path = Path(base_path)

    def save(self, dataset_name: str, df: pd.DataFrame) -> tuple[Path, Path]:
        dataset_path = self.base_path / dataset_name
        dataset_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        versioned_file = dataset_path / f"{dataset_name}_{timestamp}.csv"
        latest_file = dataset_path / "latest.csv"

        df.to_csv(versioned_file, index=False)
        df.to_csv(latest_file, index=False)

        return versioned_file, latest_file