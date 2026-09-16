# SoldierIQ Cyber — full app image (dashboard + control API).
#
# Serves the dashboard and the REST API (list runs, view findings, download PDF,
# and launch new pentests). Reading runs works anywhere; LAUNCHING a scan needs a
# Docker host — run with the Docker socket mounted and the LLM env set:
#
#   docker run -d -p 8080:8080 \
#     -e DASH_PASSWORD=secret -e STRIX_LLM=openrouter/z-ai/glm-5.3 -e LLM_API_KEY=... \
#     -v /var/run/docker.sock:/var/run/docker.sock \
#     soldieriq-cyber
#
# For local development prefer backend/scripts/serve_app.sh (uvicorn on the host).
FROM python:3.12-slim
WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY . .

ENV PORT=8080 \
    DASH_USER=admin \
    DASH_PASSWORD=soldieriq \
    PYTHONPATH=/app \
    RUNS_DIR=/app/backend/strix_runs
EXPOSE 8080
CMD ["sh", "-c", "uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT}"]
