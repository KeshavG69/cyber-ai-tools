#!/usr/bin/env bash
# Apply the SoldierIQ Cyber white-label to the LOCAL strix install:
#   1) unblock the "Past runs" email gate (patches/unblock_history.py)
#   2) overlay the branded index.html (frontend/whitelabel/index.html)
#
# Run after: pip install strix-agent==1.6.2
set -euo pipefail
BACKEND="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$BACKEND/.." && pwd)"

python "$BACKEND/patches/unblock_history.py"

STATIC="$(python -c "import strix, os; print(os.path.join(os.path.dirname(strix.__file__), 'interface', 'viewer', 'static'))")"
cp "$ROOT/frontend/whitelabel/index.html" "$STATIC/index.html"
echo "white-label overlay applied to: $STATIC"
