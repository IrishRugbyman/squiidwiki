#!/usr/bin/env bash
#
# deploy.sh - rebuild the frontend and restart the LIVE backend.
#
# This is production: squiidwiki.service serves wiki.lbzgiu.xyz, and nginx
# serves frontend/dist/ straight off disk, so the build is live the moment it
# finishes. Needs sudo. There is a brief API outage across the restart.
#
# It is NOT a dev server - it was called dev.sh until 2026-08-25 and CLAUDE.md
# described it as one, which is exactly the mistake this header exists to stop.
# For local work see CLAUDE.md, "Development Commands": uvicorn on :8001 and
# `npm run dev` on :5173.
#
# First-time provisioning (server, Postgres, systemd, nginx, TLS) is docs/DEPLOYMENT.md.

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
