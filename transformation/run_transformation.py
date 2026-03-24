import json
from pathlib import Path

from transformation.pxweb_transformer import PXWebTransformer
from transformation.unemployment import clean_unemployment
from pipelines.storage.processed import ProcessedStorage


def load_latest_raw(dataset_name: str) -> dict:
    path = Path(f"data/raw/{dataset_name}")
    latest_file = sorted(path.glob("*.json"))[-1]

    with open(latest_file) as f:
        return json.load(f)


def main():
    dataset_name = "unemployment_basic"

    raw_data = load_latest_raw(dataset_name)

    transformer = PXWebTransformer(raw_data)
    df = transformer.transform()

    df_clean = clean_unemployment(df)

    storage = ProcessedStorage()
    output_path = storage.save(dataset_name, df_clean)

    print(f"Processed data saved to {output_path}")


if __name__ == "__main__":
    main()