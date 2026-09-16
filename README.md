# SoldierIQ Cyber — Agentic AI Pentest Tool

An open-source, autonomous, multi-agent AI penetration-testing tool with a custom
**SoldierIQ Cyber** dashboard. You start pentests from the UI, watch the agent
team work, and read validated findings (with PoCs + remediation). The engine is
[Strix](https://github.com/usestrix/strix) (Apache-2.0); the dashboard + control
API are our own — **no token, no email, no cloud**, protected by one password.

## What it does

- **Start a pentest from the UI** — "＋ New Pentest" → enter a target you own +
  optional instructions → the agents run in an isolated Kali sandbox.
- **Watch it live** — the run shows as *scanning*, findings stream in, then it
  completes with severity stats + an executive summary.
- **Read findings** — expandable cards: description, impact, technical analysis,
  proof-of-concept code, remediation, CVSS.
- **Download the report PDF** — one click, generated on demand (no email).
- **Browse past runs** — switch between runs in the header.

## Requirements

Runs on a **Docker host** (your Mac): Docker running, Python 3.12, and an LLM
(cloud key or a local Ollama/vLLM endpoint). Launching a scan spins up a Kali
sandbox container, so a real Docker daemon is required.

## Run it locally

```bash
# 1. install
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt

# 2. configure
export STRIX_LLM="openrouter/z-ai/glm-5.3"   # or ollama/llama3 for a local GPU
export LLM_API_KEY="..."                      # or LLM_API_BASE for a local model
export DASH_PASSWORD="choose-a-password"       # login password (default: soldieriq)

# 3. start the app  ->  http://127.0.0.1:8080  (login: admin / your password)
backend/scripts/serve_app.sh 8080
```
Then click **＋ New Pentest**, enter a target you own (e.g. a local OWASP Juice
Shop: `docker run -d -p 3001:3000 bkimminich/juice-shop`, target
`http://host.docker.internal:3001`), tick the authorization box, and **Start scan**.

> ⚠️ Only ever scan a target you own or have explicit written permission to test.

## Layout

```
cyber-ai-tool/
├── Dockerfile            # full-app image (uvicorn); see header for scan-enabled run
├── railway.json
├── backend/
│   ├── requirements.txt      # strix-agent + fastapi + uvicorn
│   ├── api/main.py           # dashboard + control API (list/view/launch runs, PDF)
│   ├── scripts/serve_app.sh  # run the full local app (dashboard + launch scans)
│   ├── scripts/run_scan.sh   # optional: run a scan straight from the CLI
│   └── strix_runs/           # runs live here (bundled demo run included)
└── frontend/
    └── app/index.html        # the dashboard (New Pentest form, run switcher, findings)
```

## API (all behind basic-auth)

`GET /api/runs` · `GET /api/runs/{run}/summary` · `GET /api/runs/{run}/vulnerabilities`
· `GET /api/runs/{run}/report.pdf` · `POST /api/scans` `{target, instruction, authorized}`
· `GET /api/scans/{run}/status`

## Roadmap

- [ ] Add **Metasploit** via MCP (network exploitation)
- [ ] Point the LLM at **Orionhub's local GPU** (Ollama / vLLM) — full air-gap
- [ ] Live agent-transcript streaming; target allowlist
- [ ] Ingest **SA data** (TAK / knowledge base) as agent context

Engine: [Strix](https://github.com/usestrix/strix) (Apache-2.0). This repo is the
SoldierIQ Cyber dashboard + control API around it.
