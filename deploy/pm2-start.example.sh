#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/ds-car-price-prediction}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8516}"

APP_DIR="$APP_DIR" HOST="$HOST" PORT="$PORT" pm2 start "$APP_DIR/deploy/run_web.sh" \
  --name ds-car-price-prediction \
  --interpreter bash

pm2 save
pm2 status ds-car-price-prediction
