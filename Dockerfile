# SoldierIQ Cyber — dashboard image (Railway-ready).
#
# Serves the white-labeled Strix viewer + REST API for a bundled run.
# This image is the CONTROL PLANE (the dashboard). It does NOT run scans —
# scanning needs a Docker host (your Mac / Orionhub). See README.md.
#
# Railway builds this Dockerfile from the repo root.
FROM python:3.12-slim
WORKDIR /app

# --- Backend: Strix provides the viewer server + REST API + engine ---
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# --- Apply backend patch (unblock Past-runs email gate) + frontend overlay ---
COPY backend/patches ./patches
COPY frontend/whitelabel ./frontend/whitelabel
RUN python patches/unblock_history.py \
 && SITE="$(python -c "import strix, os; print(os.path.join(os.path.dirname(strix.__file__), 'interface', 'viewer', 'static'))")" \
 && cp frontend/whitelabel/index.html "$SITE/index.html"

# --- Bundled demo run so the dashboard shows real findings on deploy ---
COPY backend/strix_runs ./strix_runs

# Railway injects $PORT; default 8080 for local `docker run`.
ENV PORT=8080
ENV RUN_NAME=host-docker-internal-3001_91b4
EXPOSE 8080

# Bind 0.0.0.0 so the platform can route to it; --no-open (headless container).
CMD ["sh", "-c", "strix view \"$RUN_NAME\" --host 0.0.0.0 --port \"$PORT\" --no-open"]
