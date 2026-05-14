"""Smoke test the web app model pipeline without browser interaction."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_preprocessing import NUMERIC_FEATURES, load_car_sales_data
from src.modeling import predict_price_in_thousands, train_baseline_model


def main() -> None:
    df = load_car_sales_data()
    top10 = df.nlargest(10, "Sales_in_thousands")
    recommended = top10[NUMERIC_FEATURES].median(numeric_only=True).to_dict()

    bundle = train_baseline_model()
    prediction = predict_price_in_thousands(bundle, recommended)

    assert bundle.train_rows > bundle.test_rows > 0
    assert set(bundle.features) == set(NUMERIC_FEATURES)
    assert prediction > 0

    print("App pipeline smoke OK")
    print(f"Train/test rows: {bundle.train_rows}/{bundle.test_rows}")
    print(f"RMSE: {bundle.metrics['RMSE']:.6f}")
    print(f"R2 Score: {bundle.metrics['R2 Score']:.6f}")
    print(f"Recommended-spec prediction: {prediction:.3f} thousand USD")


if __name__ == "__main__":
    main()
