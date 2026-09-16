# backend

Python side of SoldierIQ Cyber: the **control API + dashboard server** and the
**Strix engine** it drives.

- `requirements.txt` — `strix-agent` (engine + PDF) + `fastapi` + `uvicorn`.
- `api/main.py` — FastAPI app. Serves the dashboard and:
  - `GET  /api/runs` — list runs (computed from `strix_runs/`)
  - `GET  /api/runs/{run}/summary` — overview (target, timing, severity counts…)
  - `GET  /api/runs/{run}/vulnerabilities` — findings
  - `GET  /api/runs/{run}/report.pdf` — report PDF, generated on demand (no email)
  - `POST /api/scans` `{target, instruction, authorized}` — launch a pentest
  - `GET  /api/scans/{run}/status` — live status while a scan runs

  All routes are behind HTTP basic-auth (`DASH_USER` / `DASH_PASSWORD`).
- `scripts/serve_app.sh` — run the full app locally (uvicorn on the host).
- `scripts/run_scan.sh` — optional: launch a scan straight from the CLI.
- `strix_runs/` — where runs are written; ships with a demo run (OWASP Juice Shop).

### Env
- `STRIX_LLM` + `LLM_API_KEY` (or `LLM_API_BASE`) — required to launch scans.
- `DASH_USER` (default `admin`) / `DASH_PASSWORD` (default `soldieriq`).
- `RUNS_DIR` (default `backend/strix_runs`) / `PORT` (default 8080).

Launching a scan runs `strix -n -t <target>` in a Kali sandbox container, so this
must run on a **Docker host**. A future SoldierIQ-native layer (Agno agents,
SA-data ingestion, a Metasploit tool allowlist) belongs here.
