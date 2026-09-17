#!/usr/bin/env bash
# Run a pentest with the Strix engine against an AUTHORIZED target.
#
# Requires a Docker host (your Mac / Orionhub) — the engine launches an
# isolated Kali sandbox container. Set the LLM before running:
#   export STRIX_LLM="openrouter/z-ai/glm-5.3-flash"   # or ollama/llama3 for local GPU
#   export LLM_API_KEY="..."                      # or LLM_API_BASE for a local model
#
# ⚠️  Only ever target systems you OWN or have written permission to test
#     (e.g. a local OWASP Juice Shop / DVWA / Metasploitable instance).
#     From a container, reach a host service via host.docker.internal.
#
# Usage: ./run_scan.sh <target-url> ["extra instruction"]
set -euo pipefail
TARGET="${1:?Usage: run_scan.sh <target-url> [instruction]}"
INSTRUCTION="${2:-Authorized security assessment. Perform a thorough OWASP Top 10 assessment and validate findings with working proof-of-concepts.}"
: "${STRIX_LLM:?set STRIX_LLM (e.g. openrouter/z-ai/glm-5.3-flash, or ollama/llama3 for a local model)}"
: "${LLM_API_KEY:?set LLM_API_KEY (or LLM_API_BASE for a local model endpoint)}"

# Runs write to ./strix_runs/<run-name>. Copy a finished run into backend/strix_runs
# (and set RUN_NAME in the Dockerfile) to surface it on the deployed dashboard.
strix -n -t "$TARGET" --instruction "$INSTRUCTION"
