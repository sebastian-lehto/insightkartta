import pandas as pd
from .steps.pxweb_transformer import PXWebTransformer
from .steps.apply_config import apply_config_transformations
from .steps.joins import apply_joins


def run_transformation(raw_data: dict, config: dict) -> pd.DataFrame:
    # Step 1: PXWeb → DataFrame
    df = PXWebTransformer(raw_data).transform()

    # Step 2: Apply config-driven transformations
    df = apply_config_transformations(df, config)

    # Step 3: Apply joins (region mapping etc.)
    df = apply_joins(df, config)

    return df