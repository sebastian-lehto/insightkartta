import json
from pathlib import Path

from backend.pipelines.transformation.pxweb_transformer import PXWebTransformer
from backend.pipelines.transformation.unemployment import clean_unemployment, enrich_with_region_mapping
from backend.pipelines.storage.processed import ProcessedStorage


def load_latest_raw(dataset_name: str) -> dict:
    path = Path(f"backend/data/raw/{dataset_name}")
    latest_file = sorted(path.glob("*.json"))[-1]

    with open(latest_file) as f:
        return json.load(f)


def main():
    dataset_name = "unemployment_basic"

    raw_data = load_latest_raw(dataset_name)

    transformer = PXWebTransformer(raw_data)
    df = transformer.transform()

    df_clean = clean_unemployment(df)
    df_mapped = enrich_with_region_mapping(df_clean) 

    storage = ProcessedStorage()
    output_path = storage.save(dataset_name, df_mapped)

    print(f"Processed data saved to {output_path}")


if __name__ == "__main__":
    main()