from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app

ROOT = Path(__file__).resolve().parents[1]


def test_api_metadata_contains_student_and_features() -> None:
    client = TestClient(app)
    response = client.get("/api/metadata")

    assert response.status_code == 200
    data = response.json()
    assert data["student"]["name"] == "Febnawan Fatur Rochman"
    assert data["student"]["npm"] == "237006029"
    assert len(data["features"]) == 8
    assert "Power_perf_factor" not in data["model"]["features"]
    assert len(data["topSales"]) == 10


def test_api_predict_with_default_values() -> None:
    client = TestClient(app)
    metadata = client.get("/api/metadata").json()
    payload = {feature["name"]: feature["default"] for feature in metadata["features"]}

    response = client.post("/api/predict", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] > 0
    assert data["predictionUsd"] == data["prediction"] * 1000
    assert list(data["input"].keys()) == metadata["model"]["features"]
    assert "Power_perf_factor" not in data["input"]
    assert data["modelRmse"] > 0
    assert data["estimatedRange"]["lower"] < data["prediction"] < data["estimatedRange"]["upper"]


def test_frontend_assets_are_no_store_and_current() -> None:
    client = TestClient(app)

    index_response = client.get("/")
    assert index_response.status_code == 200
    assert index_response.headers["cache-control"] == "no-store, max-age=0"
    assert "/static/app.js?v=showroom-ux-6" in index_response.text

    js_response = client.get("/static/app.js?v=showroom-ux-6")
    assert js_response.status_code == 200
    assert js_response.headers["cache-control"] == "no-store, max-age=0"
    assert 'input.type = "text"' in js_response.text
    assert "formatInputValue(feature.default, feature)" in js_response.text
    assert "chart-bar" in js_response.text


def test_frontend_sources_include_click_and_chart_regression_guards() -> None:
    index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    styles = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")

    assert 'id="predict-button"' in index
    assert 'id="submit-status"' in index
    assert "showroom-ux-6" in index
    assert "8 numerik" in index
    assert "Power_perf_factor" not in index
    assert 'id="prediction-range"' in index
    assert "<details>" not in index
    assert "<summary>" not in index
    assert "model-input" in index
    assert 'style="display: none;"' in index
    assert "renderSalesChart" in app_js
    assert "sales-svg" in app_js
    assert "Prediksi berhasil dihitung" in app_js
    assert "estimatedRange" in app_js
    assert "featureRangeText" in app_js
    assert "desimal pakai koma" not in app_js
    assert "aria-invalid" in app_js
    assert 'els.resultState.style.display = "none"' in app_js
    assert 'els.resultPanel.style.display = "grid"' in app_js
    assert "[hidden]" in styles
    assert "display: none !important" in styles
    assert "inset 4px" not in styles
    assert "linear-gradient" not in styles
    assert ".sales-svg" in styles
    assert ".hero-badges" in styles
