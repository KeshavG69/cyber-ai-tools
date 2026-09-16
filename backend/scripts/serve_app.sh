#!/usr/bin/env bash
# Run the full local SoldierIQ Cyber app: dashboard + control API (launch scans).
# Must run on a Docker host (your Mac) — scans launch Kali sandbox containers.
#
# Config comes from a gitignored `.env` at the repo root (copy .env.example),
# or from the shell environment. Required to launch scans:
#   STRIX_LLM      e.g. openrouter/z-ai/glm-5.3   (or ollama/llama3 for local GPU)
#   LLM_API_KEY    your provider key              (or LLM_API_BASE for a local model)
# Optional: DASH_USER (default admin), DASH_PASSWORD (default soldieriq).
#
#   backend/scripts/serve_app.sh [port]
set -euo pipefail
PORT="${1:-8080}"
cd "$(cd "$(dirname "$0")/../.." && pwd)"   # repo root

# Use the project virtualenv if present.
if [ -f .venv/bin/activate ]; then . .venv/bin/activate; fi

# Fail with a clear setup hint if deps aren't installed.
if ! command -v uvicorn >/dev/null 2>&1; then
  echo "uvicorn not found. First-time setup:" >&2
  echo "  python3 -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt" >&2
  exit 1
fi

# Load .env if present (never committed — see .gitignore)
if [ -f .env ]; then set -a; . ./.env; set +a; fi

: "${STRIX_LLM:?set STRIX_LLM in .env (e.g. openrouter/z-ai/glm-5.3) to enable launching scans}"
: "${LLM_API_KEY:?set LLM_API_KEY in .env (or LLM_API_BASE for a local model)}"

echo "SoldierIQ Cyber app on http://127.0.0.1:${PORT}  (login: ${DASH_USER:-admin})"
exec uvicorn backend.api.main:app --host 0.0.0.0 --port "$PORT"
