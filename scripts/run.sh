#!/usr/bin/env bash
# Запуск API: ./scripts/run.sh
set -euo pipefail

cd "$(dirname "$0")/.."

exec uvicorn booking_api.main:app \
  --app-dir src \
  --host 127.0.0.1 \
  --port 8000 \
  --reload
