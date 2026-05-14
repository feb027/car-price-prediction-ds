from __future__ import annotations

import pandas as pd

from src.data_preprocessing import (
    NUMERIC_FEATURES,
    TARGET,
    apply_numeric_imputation,
    fit_training_medians,
    make_feature_frame,
)
from src.modeling import predict_price_in_thousands, train_baseline_model


def test_feature_schema_excludes_target() -> None:
    assert TARGET not in NUMERIC_FEATURES
    assert "Power_perf_factor" not in NUMERIC_FEATURES
    assert NUMERIC_FEATURES == [
        "Engine_size",
        "Horsepower",
        "Wheelbase",
        "Width",
        "Length",
        "Curb_weight",
        "Fuel_capacity",
        "Fuel_efficiency",
    ]


def test_baseline_metrics_are_realistic_without_power_perf_proxy() -> None:
    bundle = train_baseline_model()

    assert 5.0 < bundle.metrics["RMSE"] < 10.0
    assert 0.60 < bundle.metrics["R2 Score"] < 0.90


def test_imputation_uses_training_medians_only() -> None:
    X_train = pd.DataFrame({feature: [1.0, 3.0] for feature in NUMERIC_FEATURES})
    X_test = pd.DataFrame({feature: [None] for feature in NUMERIC_FEATURES})

    medians = fit_training_medians(X_train)
    X_test_imputed = apply_numeric_imputation(X_test, medians)

    assert medians.eq(2.0).all()
    assert X_test_imputed.iloc[0].eq(2.0).all()


def test_prediction_pipeline_smoke() -> None:
    bundle = train_baseline_model()
    values = {feature: float(bundle.train_medians[feature]) for feature in NUMERIC_FEATURES}
    prediction = predict_price_in_thousands(bundle, values)

    assert isinstance(prediction, float)
    assert prediction > 0


def test_make_feature_frame_preserves_schema_order() -> None:
    values = {feature: 1.0 for feature in reversed(NUMERIC_FEATURES)}
    frame = make_feature_frame(values)

    assert list(frame.columns) == NUMERIC_FEATURES
