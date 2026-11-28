#!/usr/bin/env bash
# Запуск тестов: ./scripts/test.sh [доп. аргументы pytest]
set -euo pipefail

cd "$(dirname "$0")/.."

exec python -m pytest "$@"
