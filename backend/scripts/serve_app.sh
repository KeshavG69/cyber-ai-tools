#!/usr/bin/env bash
# Run the full local SoldierIQ Cyber app: dashboard + control API (launch scans).
# Must run on a Docker host (your Mac) — scans launch Kali sandbox containers.
#
#   export STRIX_LLM="openrouter/z-ai/glm-5.3"   # or ollama/llama3 for local GPU
#   export LLM_API_KEY="..."                      # or LLM_API_BASE for a local model
#   export DASH_PASSWORD="..."                    # optional (default: soldieriq)
#   backend/scripts/serve_app.sh [port]
set -euo pipefail
PORT="${1:-8080}"
cd "$(cd "$(dirname "$0")/../.." && pwd)"   # repo root

: "${STRIX_LLM:?set STRIX_LLM (e.g. openrouter/z-ai/glm-5.3) to enable launching scans}"
: "${LLM_API_KEY:?set LLM_API_KEY (or LLM_API_BASE for a local model)}"

echo "SoldierIQ Cyber app on http://127.0.0.1:${PORT}  (login: ${DASH_USER:-admin})"
exec uvicorn backend.api.main:app --host 0.0.0.0 --port "$PORT"
