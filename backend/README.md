# backend — the SoldierIQ Cyber service

Self-contained FastAPI service: dashboard + control API + the Strix engine it
drives. This whole folder is the Docker build context (`Dockerfile` here), so it
ships as one complete image.

- `Dockerfile` — builds this folder; runs `uvicorn api.main:app` on `$PORT`.
- `requirements.txt` — pinned lockfile (reproducible); `requirements.in` is the
  human-readable top-level.
- `api/main.py` — FastAPI app (paths are relative to the package, so it works in
  local dev and in the container). Endpoints (all behind basic-auth):
  - `GET  /` — the dashboard (serves `api/webui/index.html`)
  - `GET  /api/runs` · `/api/runs/{run}/summary` · `/vulnerabilities` · `/report.pdf` · `/transcript`
  - `POST /api/scans` `{target, instruction, authorized, max_budget}` — launch a scan
  - `GET  /api/scans/{run}/status`
- `api/webui/index.html` — the dashboard UI (New Pentest form, live Activity feed,
  findings, Past runs).
- `scripts/serve_app.sh` — run the full app locally (loads `../.env`).
- `scripts/run_scan.sh` — optional CLI scan launcher.
- `strix_runs/` — runs are written here; ships with a demo run (OWASP Juice Shop).

### Env
`STRIX_LLM` + `LLM_API_KEY` (or `LLM_API_BASE`) to launch scans; `DASH_USER`
(default `admin`) / `DASH_PASSWORD` (default `soldieriq`); `PORT`; `RUNS_DIR`
(default `strix_runs/` beside the package).

Launching a scan runs `strix -n -t <target>` in a Kali sandbox container, so this
must run on a **Docker host**.
