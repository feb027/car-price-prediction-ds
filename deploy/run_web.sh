#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/ds-car-price-prediction}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8516}"
PYTHON_BIN="${PYTHON_BIN:-$APP_DIR/.venv/bin/python}"

cd "$APP_DIR"
exec "$PYTHON_BIN" -m uvicorn api.main:app --host "$HOST" --port "$PORT"
