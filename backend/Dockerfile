# SoldierIQ Cyber — self-contained service image (Option B: in-container engine).
#
# Build CONTEXT is this backend/ folder (that is how OrionHub builds the detected
# "backend" service). Everything the app needs lives here: the API (api/),
# the dashboard (api/webui/), the bundled demo run (strix_runs/), and the
# runtime patch (patches/) that registers an in-container Strix backend.
#
# Option B = no Docker. Strix 1.6.2 ships only the "docker" runtime backend,
# which needs a Docker daemon — unavailable on Railway Services / OrionHub k3s
# pods. patches/local_backend.py registers a "local" backend that runs the
# pentest tools INSIDE THIS CONTAINER via the openai-agents unix_local sandbox.
# STRIX_RUNTIME_BACKEND=local selects it. The tools must therefore be installed
# in this image (see the apt layer below).
#
# ⚠️ In local mode the engine runs exploit tooling in this container with NO
# nested-sandbox isolation — the container/pod itself is the only boundary.
# Only deploy where that is acceptable, and only scan authorized targets.
FROM python:3.12-slim
WORKDIR /app

# --- Pentest toolset available to the in-container ("local") backend ----------
# Core network/web/recon CLIs the agent shells out to. Extend as needed; a
# heavier Kali set can be added here or swap this base for a Kali-derived image.
RUN apt-get update && apt-get install -y --no-install-recommends \
        nmap \
        curl \
        wget \
        git \
        jq \
        whois \
        dnsutils \
        iputils-ping \
        netcat-openbsd \
        ca-certificates \
        openssl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Register the in-container "local" Strix backend into the installed package.
# Runs at build time so the image ships already patched (idempotent).
RUN python patches/local_backend.py

# Infra + Option-B defaults. App config (DASH_USER/DASH_PASSWORD, STRIX_LLM,
# LLM_API_KEY, RUNS_DIR) is left UNSET so platform-provided values win.
# STRIX_RUNTIME_BACKEND=local makes scans run in THIS container (no Docker).
ENV PORT=8080 \
    PYTHONPATH=/app \
    STRIX_RUNTIME_BACKEND=local
EXPOSE 8080
# Context is backend/, so the package is importable as api.main at /app.
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
