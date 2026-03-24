import pandas as pd
from typing import Dict, Any, List


class PXWebTransformer:
    """Transformer for PXWeb JSON (columns + data format)."""

    def __init__(self, raw_data: Dict[str, Any]):
        # Handle wrapper from ingestion
        self.data = raw_data.get("data", raw_data)

    def transform(self) -> pd.DataFrame:
        columns = self.data["columns"]
        rows = self.data["data"]

        # Separate dimensions and metrics
        dimension_cols = [col for col in columns if col["type"] in ("d", "t")]
        metric_cols = [col for col in columns if col["type"] == "c"]

        dim_names = [col["code"] for col in dimension_cols]
        metric_names = [col["code"] for col in metric_cols]

        records: List[Dict[str, Any]] = []

        for row in rows:
            record = {}

            # Map dimension keys
            for i, dim_name in enumerate(dim_names):
                record[dim_name] = row["key"][i]

            # Map metric values
            for i, metric_name in enumerate(metric_names):
                value = row["values"][i]

                # Convert to numeric if possible
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    value = None

                record[metric_name] = value

            records.append(record)

        df = pd.DataFrame(records)

        return df