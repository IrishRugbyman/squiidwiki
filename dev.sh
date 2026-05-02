#!/usr/bin/env bash
set -e

PY="C:/Users/irish/miniconda3/envs/squiidwiki/python.exe"
ROOT="$(cd "$(dirname "$0")" && pwd)"

kill_port() {
  local port=$1
  # netstat on Windows produces \r\n lines; strip \r so taskkill gets a clean PID
  local pids
  pids=$(netstat -ano 2>/dev/null \
    | grep ":${port}[[:space:]]" | grep "LISTENING" \
    | awk '{print $NF}' | tr -d '\r' | sort -u)
  if [ -n "$pids" ]; then
    for pid in $pids; do
      echo "  Killing PID $pid on :${port}..."
      taskkill /PID "$pid" /F 2>/dev/null || true
    done
    # Wait until the port is actually free (up to 5s)
    local i=0
    while netstat -ano 2>/dev/null | grep ":${port}[[:space:]]" | grep -q "LISTENING"; do
      sleep 0.5
      i=$((i + 1))
      [ $i -ge 10 ] && { echo "  Warning: :${port} still busy after 5s, continuing anyway"; break; }
    done
  else
    echo "  :${port} is free"
  fi
}

cleanup() {
  echo ""
  echo "Stopping servers..."
  [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null || true
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID"  2>/dev/null || true
  wait "$FRONTEND_PID" 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

echo "=== Clearing ports ==="
kill_port 8001
kill_port 5173

echo ""
echo "=== Starting backend  :8001 ==="
(cd "$ROOT/backend" && "$PY" -m uvicorn app.main:app --port 8001) &
BACKEND_PID=$!

echo "=== Starting frontend :5173 ==="
(cd "$ROOT/frontend" && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "backend PID=$BACKEND_PID  frontend PID=$FRONTEND_PID"
echo "Ctrl+C to stop both."
echo ""

# If either process dies unexpectedly, kill the other and exit
wait "$BACKEND_PID"  && echo "Backend exited."  || echo "Backend crashed."
kill "$FRONTEND_PID" 2>/dev/null || true
wait "$FRONTEND_PID" 2>/dev/null || true
