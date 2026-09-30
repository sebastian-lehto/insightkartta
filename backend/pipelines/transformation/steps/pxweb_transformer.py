import pandas as pd
from typing import Dict, Any, List


class PXWebTransformer:
    """Transformer for PXWeb JSON - supports both column-based and dimension-based formats."""

    def __init__(self, raw_data: Dict[str, Any], config: Dict[str, Any] | None = None):
        # Handle wrapper from ingestion
        self.data = raw_data.get("data", raw_data)
        self.config = config or {}

    def transform(self) -> pd.DataFrame:
        """Transform PXWeb data to DataFrame, detecting and handling both formats."""
        
        # Detect format and use appropriate transformer
        if "columns" in self.data:
            return self._transform_column_format()
        elif "dimension" in self.data:
            return self._transform_dimension_format()
        else:
            raise ValueError("Unknown PXWeb JSON format - expected 'columns' or 'dimension' key")

    def _transform_column_format(self) -> pd.DataFrame:
        """Transform newer PXWeb format: {columns: [...], data: [{key: [...], values: [...]}]}"""
        columns = self.data["columns"]
        rows = self.data["data"]

        # Separate dimensions and metrics
        dimension_cols = [col for col in columns if col["type"] in ("d", "t")]
        metric_cols = [col for col in columns if col["type"] == "c"]

        # Normalize codes for API format compatibility.
        # Post-June 2026 API uses machine IDs (alue_23_20260101, timeperiod_y) for dimensions
        # and subject-prefixed codes (tyokay-tyollisyysaste) for metrics. Use the human-readable
        # text label for dimensions and strip the prefix for metrics so downstream config
        # (datasets.yaml rename/filter keys) works unchanged across API versions.
        dim_names = [
            self._normalize_dim_code(col["code"], col.get("text", col["code"]))
            for col in dimension_cols
        ]
        metric_names = [self._normalize_metric_code(col["code"]) for col in metric_cols]

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

        return pd.DataFrame(records)

    def _transform_dimension_format(self) -> pd.DataFrame:
        """Transform older PXWeb format: {dimension: {...}, id: [...], value: [...]}"""
        dimensions = self.data["dimension"]
        id_order = self.data["id"]
        values = self.data["value"]

        records: List[Dict[str, Any]] = []

        for idx, value in enumerate(values):
            record = {}

            # Build dimensional key by converting flat index to multi-dimensional coordinates
            coords = self._flat_index_to_coords(idx, self.data["size"])

            value_dimension = self.config.get("transformation", {}).get("value_dimension")

            # Map coordinates to dimension values
            for i, dim_name in enumerate(id_order):
                source_dim_name = dim_name
                dim_data = dimensions[dim_name]
                dim_categories = dim_data["category"]
                
                # Get the category label at this coordinate
                if "index" in dim_categories:
                    # Reverse lookup: find label for this index position
                    category_index = coords[i]
                    index_to_label = {v: k for k, v in dim_categories["index"].items()}
                    category_code = index_to_label.get(category_index, str(category_index))
                    labels = dim_categories.get("label", {})
                    if dim_name == value_dimension or source_dim_name == value_dimension:
                        record["indicator"] = category_code
                        record["indicator_label"] = labels.get(category_code, category_code)
                    else:
                        record[dim_name] = category_code
                        if source_dim_name != dim_name:
                            record[source_dim_name] = category_code
                        if category_code in labels:
                            record[f"{dim_name}_label"] = labels[category_code]
                            if source_dim_name != dim_name:
                                record[f"{source_dim_name}_label"] = labels[category_code]
                else:
                    record[dim_name] = str(coords[i])

            if value_dimension:
                record["value"] = self._numeric_value(value)
                records.append(record)
                continue

            # Add the value (usually has a generic name like "Tiedot")
            # Find the metric column name from the last dimension
            metric_name = None
            if len(id_order) > 0:
                last_dim = id_order[-1]
                if last_dim in dimensions:
                    # Get the actual metric name
                    dim_cats = dimensions[last_dim]["category"]
                    if "index" in dim_cats:
                        index_to_label = {v: k for k, v in dim_cats["index"].items()}
                        metric_name = index_to_label.get(coords[-1])

            if metric_name:
                record[metric_name] = self._numeric_value(value)
            else:
                # Fallback to generic name
                record["value"] = value

            records.append(record)

        return pd.DataFrame(records)

    @staticmethod
    def _numeric_value(value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _normalize_dim_code(code: str, text: str) -> str:
        # Machine-code dimensions start lowercase with underscores/digits (alue_23_20260101).
        # Take only the first word of the text label so year-qualified labels like
        # "Alue 2026" normalize to "Alue", matching datasets.yaml dimension keys.
        if code and code[0].islower() and ("_" in code or any(c.isdigit() for c in code)):
            return text.split()[0]
        return code

    @staticmethod
    def _normalize_metric_code(code: str) -> str:
        # Post-June 2026 metric codes carry a subject prefix: "tyokay-tyollisyysaste".
        # Strip it so rename keys in datasets.yaml (e.g. "tyollisyysaste") still match.
        if "-" in code:
            return code.split("-", 1)[1]
        return code

    @staticmethod
    def _flat_index_to_coords(flat_idx: int, dimensions: List[int]) -> List[int]:
        """Convert a flat index to multi-dimensional coordinates given dimension sizes."""
        coords = []
        for size in reversed(dimensions):
            coords.append(flat_idx % size)
            flat_idx //= size
        return list(reversed(coords))