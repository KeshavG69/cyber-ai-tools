# SoldierIQ Cyber — Agentic AI Pentest Tool

An open-source, autonomous, multi-agent AI penetration-testing tool with a
white-labeled **SoldierIQ Cyber** dashboard. Built on [Strix](https://github.com/usestrix/strix)
(Apache-2.0) as the agent engine, designed to run **fully locally / air-gapped**
(local-GPU LLMs, zero data egress) on a Docker host such as **Orionhub**.

## Architecture — two planes

| Plane | What | Where it runs |
|-------|------|---------------|
| **Control plane** (this dashboard image) | White-labeled viewer UI + REST API that shows runs, agent transcripts, and findings | Railway, or any host (no Docker-in-Docker needed) |
| **Execution plane** (the scan engine) | The autonomous agents that actually run the pentest, in an isolated Kali sandbox **container** | A **Docker host** — your Mac now, **Orionhub GPU box** for the real thing |

> ⚠️ The scan engine needs a real Docker daemon (it launches sandbox containers).
> PaaS platforms that block privileged Docker (Railway, Render, Cloud Run) can host
> the **dashboard** but **not** the engine. Run the engine on Orionhub / a Docker VM.

## Layout

```
cyber-ai-tool/
├── Dockerfile            # builds the dashboard image (Railway builds this)
├── railway.json          # Railway deploy config
├── backend/              # Python side — engine + viewer server (Strix) + patches
│   ├── requirements.txt      # strix-agent==1.6.2 (+ future FastAPI/Agno code)
│   ├── patches/
│   │   └── unblock_history.py # removes the email gate on "Past runs"
│   ├── scripts/
│   │   ├── apply_whitelabel.sh   # apply brand + unblock to a LOCAL strix install
│   │   ├── run_scan.sh           # run a pentest against an authorized target
│   │   └── serve_dashboard.sh    # serve the dashboard locally
│   └── strix_runs/           # bundled demo run (OWASP Juice Shop) for the dashboard
└── frontend/             # UI — white-label overlay now; custom Next.js app later
    └── whitelabel/
        └── index.html        # SoldierIQ Cyber branding overlay for the viewer
```

## Quick start (dashboard, locally via Docker)

```bash
docker build -t soldieriq-cyber .
docker run -d --name siq-dash -p 8080:8080 soldieriq-cyber
docker logs siq-dash | grep token   # copy the ?token=... link
# open http://127.0.0.1:8080/?token=...
```

## Deploy the dashboard to Railway

```bash
railway init          # or: railway link
railway up            # builds the Dockerfile, deploys
```
Grab the `?token=...` link from **Deployments → Logs** and open
`https://<app>.up.railway.app/?token=...`.

## Run a scan (on a Docker host: Mac / Orionhub)

```bash
pip install strix-agent==1.6.2
export STRIX_LLM="openrouter/z-ai/glm-5.3"   # or ollama/llama3 for a local GPU
export LLM_API_KEY="..."                      # or LLM_API_BASE for a local model
backend/scripts/run_scan.sh http://host.docker.internal:3001
```
Copy the finished run from `strix_runs/<name>` into `backend/strix_runs/` and set
`RUN_NAME` in the `Dockerfile` to surface it on the deployed dashboard.

> ⚠️ Only ever scan a target you own or have written permission to test
> (e.g. local OWASP Juice Shop / DVWA / Metasploitable).

## Roadmap

- [ ] Add **Metasploit** to the engine via MCP (`~/.strix/mcp-servers.json`)
- [ ] Point the LLM at **Orionhub's local GPU** (Ollama / vLLM) for full air-gap
- [ ] Fixed-token / password auth on the dashboard (drop the `?token=` in logs)
- [ ] Custom **Next.js** frontend in `frontend/` consuming the viewer REST API
- [ ] Ingest **SA data** (TAK / knowledge base) as agent context

## Credit / license

Engine + viewer: [Strix](https://github.com/usestrix/strix) (Apache-2.0).
This repo is the SoldierIQ Cyber white-label + packaging around it.
