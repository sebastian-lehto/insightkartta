import pandas as pd
from pathlib import Path


class ProcessedStorage:
    def __init__(self, base_path: str = "backend/data/processed"):
        self.base_path = Path(base_path)

    def save(self, dataset_name: str, df: pd.DataFrame) -> Path:
        dataset_path = self.base_path / dataset_name
        dataset_path.mkdir(parents=True, exist_ok=True)

        file_path = dataset_path / "data.parquet"

        df.to_parquet(file_path, index=False)

        return file_path