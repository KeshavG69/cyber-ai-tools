#!/usr/bin/env bash
# Serve the white-labeled dashboard locally for a run under ./strix_runs.
# Run backend/scripts/apply_whitelabel.sh once first so the local strix install
# is branded + unblocked.
#
# Usage: ./serve_dashboard.sh [run-name] [port]
set -euo pipefail
RUN_NAME="${1:-host-docker-internal-3001_91b4}"
PORT="${2:-8080}"
# --host 0.0.0.0 so it is reachable off localhost; --no-open for headless hosts.
strix view "$RUN_NAME" --host 0.0.0.0 --port "$PORT" --no-open
