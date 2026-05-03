#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "=== Building frontend ==="
(cd "$ROOT/frontend" && npm run build)

echo ""
echo "=== Restarting squiidwiki service ==="
sudo systemctl restart squiidwiki

echo ""
echo "=== Status ==="
sudo systemctl status squiidwiki --no-pager -n 5
