"""Modeling helpers for the car price prediction project."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from src.data_preprocessing import (
    DATA_PATH,
    NUMERIC_FEATURES,
    TARGET,
    apply_numeric_imputation,
    fit_training_medians,
    load_car_sales_data,
    make_feature_frame,
    prepare_modeling_data,
)


@dataclass(frozen=True)
class BaselineModelBundle:
    """Trained baseline model and preprocessing fitted on the train split."""

    model: LinearRegression
    train_medians: pd.Series
    metrics: dict[str, float]
    features: list[str]
    target: str
    train_rows: int
    test_rows: int
    random_state: int


def train_baseline_model(
    data_path: Path | str = DATA_PATH,
    *,
    test_size: float = 0.20,
    random_state: int = 42,
) -> BaselineModelBundle:
    """Train the LinearRegression baseline with train-only median imputation."""
    df = load_car_sales_data(data_path)
    X, y = prepare_modeling_data(df)
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
    )

    train_medians = fit_training_medians(X_train_raw)
    X_train = apply_numeric_imputation(X_train_raw, train_medians)
    X_test = apply_numeric_imputation(X_test_raw, train_medians)

    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    metrics = {
        "RMSE": float(mean_squared_error(y_test, y_pred) ** 0.5),
        "R2 Score": float(r2_score(y_test, y_pred)),
    }
    return BaselineModelBundle(
        model=model,
        train_medians=train_medians,
        metrics=metrics,
        features=list(NUMERIC_FEATURES),
        target=TARGET,
        train_rows=len(X_train),
        test_rows=len(X_test),
        random_state=random_state,
    )


def predict_price_in_thousands(
    bundle: BaselineModelBundle,
    values: dict[str, float] | pd.DataFrame,
) -> float:
    """Predict car price in thousands of dollars for one feature row."""
    feature_frame = make_feature_frame(values)
    feature_frame = apply_numeric_imputation(feature_frame, bundle.train_medians)
    return float(bundle.model.predict(feature_frame)[0])


def describe_baseline_model() -> dict[str, object]:
    """Return baseline model metadata used by notebook and app."""
    return {
        "model": "LinearRegression",
        "target": TARGET,
        "features": NUMERIC_FEATURES,
        "train_test_split": "80/20",
        "metrics": ["RMSE", "R2 Score"],
    }
