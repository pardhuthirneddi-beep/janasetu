#!/usr/bin/env bash
set -euo pipefail
cd /app
API_PORT="${API_PORT:-8000}"
/opt/venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port "$API_PORT" &
API_PID=$!
cleanup() {
  kill "$API_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
pnpm --dir frontend start --hostname 0.0.0.0 --port "${PORT:-3000}"
