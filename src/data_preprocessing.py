"""Data loading and preprocessing helpers for the car sales project."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "Car_sales.xlsx"
SHEET_NAME = "Car_sales"

NUMERIC_FEATURES = [
    "Engine_size",
    "Horsepower",
    "Wheelbase",
    "Width",
    "Length",
    "Curb_weight",
    "Fuel_capacity",
    "Fuel_efficiency",
]

TARGET = "Price_in_thousands"


def get_feature_columns() -> list[str]:
    """Return baseline numeric feature columns for LinearRegression."""
    return list(NUMERIC_FEATURES)


def load_car_sales_data(data_path: Path | str = DATA_PATH) -> pd.DataFrame:
    """Load the audited car sales dataset."""
    return pd.read_excel(data_path, sheet_name=SHEET_NAME)


def prepare_modeling_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Drop rows with missing target and return raw features/target.

    Feature missing values are intentionally left untouched here. Median
    imputation must be fitted after the train/test split to avoid leakage.
    """
    modeling_df = df.dropna(subset=[TARGET]).copy()
    X = modeling_df[NUMERIC_FEATURES].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(modeling_df[TARGET], errors="coerce")
    return X, y


def fit_training_medians(X_train: pd.DataFrame) -> pd.Series:
    """Fit numeric feature medians from the training split only."""
    return X_train[NUMERIC_FEATURES].median(numeric_only=True)


def apply_numeric_imputation(X: pd.DataFrame, medians: pd.Series) -> pd.DataFrame:
    """Apply training medians to a feature dataframe."""
    return X[NUMERIC_FEATURES].copy().fillna(medians)


def make_feature_frame(values: dict[str, float] | pd.DataFrame) -> pd.DataFrame:
    """Create a feature dataframe with the exact baseline column order."""
    if isinstance(values, pd.DataFrame):
        frame = values.copy()
    else:
        frame = pd.DataFrame([values])
    return frame[NUMERIC_FEATURES].apply(pd.to_numeric, errors="coerce")
