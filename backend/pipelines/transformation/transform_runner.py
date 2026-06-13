import pandas as pd
from .steps.pxweb_transformer import PXWebTransformer
from .steps.apply_config import apply_config_transformations
from .steps.joins import apply_joins
from .steps.normalize import select_required_columns


def run_transformation(raw_data: dict, config: dict) -> pd.DataFrame:
    # Step 1: PXWeb → DataFrame
    df = PXWebTransformer(raw_data).transform()

    # Step 2: Apply config-driven transformations
    df = apply_config_transformations(df, config)

    # Step 3: Apply joins (region mapping etc.)
    df = apply_joins(df, config)

    # Step 4: Select only required columns
    df = select_required_columns(df)

    return df