#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
API_PORT="${API_PORT:-8000}"
if [[ -x /opt/venv/bin/python ]]; then
  PYTHON_BIN=/opt/venv/bin/python
elif [[ -x backend/.venv/bin/python ]]; then
  PYTHON_BIN=backend/.venv/bin/python
else
  PYTHON_BIN=python3
fi
"$PYTHON_BIN" -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port "$API_PORT" --reload --reload-dir backend/app &
API_PID=$!
cleanup() {
  kill "$API_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
pnpm --dir frontend dev --hostname 0.0.0.0
