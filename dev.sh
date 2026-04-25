#!/usr/bin/env bash
set -e

PY="C:/Users/irish/miniconda3/envs/squiidwiki/python.exe"
ROOT="$(cd "$(dirname "$0")" && pwd)"

kill_port() {
  local port=$1
  local pid
  pid=$(netstat -ano 2>/dev/null | grep ":${port} " | grep "LISTENING" | awk '{print $NF}' | head -1)
  if [ -n "$pid" ]; then
    echo "Killing existing process on :${port} (PID $pid)..."
    taskkill /PID "$pid" /F 2>/dev/null || true
    sleep 1
  fi
}

cleanup() {
  echo ""
  echo "Stopping servers..."
  kill "$BACKEND_PID" 2>/dev/null
  exit 0
}
trap cleanup INT TERM

kill_port 8001
kill_port 5173

echo "Starting backend on :8001..."
(cd "$ROOT/backend" && "$PY" -m uvicorn app.main:app --port 8001) &
BACKEND_PID=$!

echo "Starting frontend on :5173..."
(cd "$ROOT/frontend" && npm run dev)
