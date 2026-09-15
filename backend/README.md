# backend — engine + viewer server

The Python side of SoldierIQ Cyber. Today it is a thin, well-defined layer
around **Strix** (`strix-agent`), which provides both:

- the **scan engine** (autonomous multi-agent pentester, runs in a Docker sandbox), and
- the **viewer server + REST API** that the dashboard frontend talks to.

## Contents

- `requirements.txt` — pinned `strix-agent==1.6.2` (+ placeholders for future
  FastAPI / Agno code as we build a SoldierIQ-native layer).
- `patches/unblock_history.py` — appends an `is_verified()` override to the Strix
  viewer so **"Past runs" history needs no email one-time-code**. Idempotent.
- `scripts/apply_whitelabel.sh` — apply the unblock patch **and** the frontend
  branding overlay to a LOCAL `strix` install (for local dev).
- `scripts/run_scan.sh` — run a pentest against an authorized target (needs Docker + an LLM).
- `scripts/serve_dashboard.sh` — serve the dashboard locally for a run.
- `strix_runs/` — a bundled finished run (OWASP Juice Shop) used as demo data.

## Viewer REST API (served by `strix view`)

The frontend consumes these (token-authorized):

| Endpoint | Returns |
|----------|---------|
| `GET /api/run` | run metadata + status |
| `GET /api/runs` | run history list (unblocked by the patch — no email) |
| `GET /api/transcript` | live agent transcripts (thinking + tool calls) |
| `GET /api/vulnerabilities` | validated findings |
| `GET /api/report` | the generated pentest report |

## Local dev

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
scripts/apply_whitelabel.sh                     # brand + unblock the local install
scripts/serve_dashboard.sh host-docker-internal-3001_91b4 8080
```

## Where new backend code goes

A SoldierIQ-native API/agent layer (FastAPI + Agno, SA-data ingestion, a custom
tool allowlist for Metasploit) belongs here as its own package alongside the
Strix integration.
