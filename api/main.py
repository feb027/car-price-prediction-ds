"""FastAPI backend for the car price prediction web app."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_preprocessing import NUMERIC_FEATURES, TARGET, load_car_sales_data
from src.modeling import BaselineModelBundle, predict_price_in_thousands, train_baseline_model

STUDENT = {
    "name": "Febnawan Fatur Rochman",
    "npm": "237006029",
    "class": "Informatika A - FT UNSIL",
}

FEATURE_META = {
    "Engine_size": {
        "label": "Ukuran mesin",
        "unit": "liter",
        "group": "Performa mesin",
        "min": 0.5,
        "max": 10.0,
        "step": 0.1,
    },
    "Horsepower": {
        "label": "Horsepower",
        "unit": "hp",
        "group": "Performa mesin",
        "min": 40,
        "max": 600,
        "step": 5,
    },
    "Wheelbase": {
        "label": "Jarak sumbu roda",
        "unit": "inci",
        "group": "Dimensi kendaraan",
        "min": 80,
        "max": 160,
        "step": 0.5,
    },
    "Width": {
        "label": "Lebar",
        "unit": "inci",
        "group": "Dimensi kendaraan",
        "min": 50,
        "max": 100,
        "step": 0.5,
    },
    "Length": {
        "label": "Panjang",
        "unit": "inci",
        "group": "Dimensi kendaraan",
        "min": 120,
        "max": 250,
        "step": 0.5,
    },
    "Curb_weight": {
        "label": "Berat kosong",
        "unit": "ribu lbs",
        "group": "Efisiensi & bobot",
        "min": 1.0,
        "max": 7.0,
        "step": 0.1,
    },
    "Fuel_capacity": {
        "label": "Kapasitas BBM",
        "unit": "galon",
        "group": "Efisiensi & bobot",
        "min": 5,
        "max": 40,
        "step": 0.5,
    },
    "Fuel_efficiency": {
        "label": "Efisiensi BBM",
        "unit": "mpg",
        "group": "Efisiensi & bobot",
        "min": 5,
        "max": 60,
        "step": 1,
    },
}


class PredictionRequest(BaseModel):
    """Validated request body for a single car price prediction."""

    Engine_size: float = Field(ge=0.5, le=10.0)
    Horsepower: float = Field(ge=40, le=600)
    Wheelbase: float = Field(ge=80, le=160)
    Width: float = Field(ge=50, le=100)
    Length: float = Field(ge=120, le=250)
    Curb_weight: float = Field(ge=1.0, le=7.0)
    Fuel_capacity: float = Field(ge=5, le=40)
    Fuel_efficiency: float = Field(ge=5, le=60)

    def as_feature_dict(self) -> dict[str, float]:
        """Return values in the exact model feature order."""
        payload = self.model_dump()
        return {feature: float(payload[feature]) for feature in NUMERIC_FEATURES}


@lru_cache(maxsize=1)
def get_model_bundle() -> BaselineModelBundle:
    """Train and cache the baseline model once per process."""
    return train_baseline_model()


@lru_cache(maxsize=1)
def get_metadata_payload() -> dict[str, object]:
    """Build frontend metadata from dataset and trained model."""
    bundle = get_model_bundle()
    df = load_car_sales_data()
    top10 = df.nlargest(10, "Sales_in_thousands")[
        ["Manufacturer", "Model", "Sales_in_thousands", "Price_in_thousands", *NUMERIC_FEATURES]
    ].copy()
    top10["Mobil"] = top10["Manufacturer"] + " " + top10["Model"]
    defaults = top10[NUMERIC_FEATURES].median(numeric_only=True).to_dict()

    return {
        "student": STUDENT,
        "model": {
            "name": "LinearRegression",
            "target": TARGET,
            "features": list(NUMERIC_FEATURES),
            "trainRows": bundle.train_rows,
            "testRows": bundle.test_rows,
            "split": "80:20",
            "randomState": bundle.random_state,
            "metrics": bundle.metrics,
        },
        "features": [
            {"name": feature, **FEATURE_META[feature], "default": float(defaults[feature])}
            for feature in NUMERIC_FEATURES
        ],
        "topSales": [
            {
                "rank": int(index + 1),
                "manufacturer": str(row["Manufacturer"]),
                "model": str(row["Model"]),
                "car": str(row["Mobil"]),
                "sales": float(row["Sales_in_thousands"]),
                "price": float(row["Price_in_thousands"]),
            }
            for index, row in top10.reset_index(drop=True).iterrows()
        ],
    }


app = FastAPI(
    title="Car Sales Price Prediction API",
    description="FastAPI backend for a Data Science final project web interface.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=ROOT / "web"), name="static")


@app.middleware("http")
async def no_store_web_assets(request: Request, call_next):
    """Avoid stale frontend JS/CSS during iterative Tailnet previews."""
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Serve the web frontend."""
    return FileResponse(ROOT / "web" / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    """Health check endpoint for local/VPS smoke tests."""
    return {"status": "ok"}


@app.get("/api/metadata")
def metadata() -> dict[str, object]:
    """Return model metadata, defaults, and dataset references for the frontend."""
    return get_metadata_payload()


@app.post("/api/predict")
def predict(request: PredictionRequest) -> dict[str, object]:
    """Predict price in thousands of USD for one car specification."""
    try:
        bundle = get_model_bundle()
        values = request.as_feature_dict()
        prediction = predict_price_in_thousands(bundle, values)
        rmse = float(bundle.metrics["RMSE"])
    except Exception as exc:  # pragma: no cover - defensive API boundary
        raise HTTPException(status_code=500, detail=f"Prediction failed: {type(exc).__name__}") from exc

    lower = max(0.0, prediction - rmse)
    upper = prediction + rmse
    return {
        "prediction": prediction,
        "predictionUsd": prediction * 1000,
        "unit": "thousand_usd",
        "modelRmse": rmse,
        "estimatedRange": {
            "lower": lower,
            "upper": upper,
            "lowerUsd": lower * 1000,
            "upperUsd": upper * 1000,
        },
        "input": values,
    }
