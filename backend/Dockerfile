# SoldierIQ Cyber — self-contained service image.
#
# Build CONTEXT is this backend/ folder (that is how OrionHub builds the detected
# "backend" service). Everything the app needs lives here: the API (api/),
# the dashboard (api/webui/), and the bundled demo run (strix_runs/).
#
# Reading/serving runs works anywhere. LAUNCHING a scan needs a Docker host
# (Strix spins up a Kali sandbox), i.e. run with the node's Docker socket + LLM env.
FROM python:3.12-slim
WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Only infra defaults here. App config (DASH_USER/DASH_PASSWORD, STRIX_LLM,
# LLM_API_KEY, RUNS_DIR) is left UNSET so platform-provided values (OrionHub env
# or a mounted .env) win; the app falls back to sensible defaults in code.
ENV PORT=8080 \
    PYTHONPATH=/app
EXPOSE 8080
# Context is backend/, so the package is importable as api.main at /app.
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
