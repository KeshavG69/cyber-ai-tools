# SoldierIQ Cyber — Agentic AI Pentest Tool

An open-source, autonomous, multi-agent AI penetration-testing tool with a custom
**SoldierIQ Cyber** dashboard. Start pentests from the UI, watch the agents reason
and run tools live, and read validated findings (with PoCs + remediation). The
engine is [Strix](https://github.com/usestrix/strix) (Apache-2.0); the dashboard +
control API are our own — **no token, no email, no cloud** — behind one password.

## What it does
- **Start a pentest from the UI** — ＋ New Pentest → target + instructions + a
  budget cap → the agents run in an isolated Kali sandbox.
- **Watch live** — the **Activity** tab streams each agent's reasoning + tool calls;
  the roster shows agents flipping running → completed.
- **Findings** — expandable cards: description, impact, technical analysis, PoC,
  remediation, CVSS. **Past runs** view lists every run.
- **Download the report PDF** — generated on demand, no email.

## Structure (single self-contained service)
```
cyber-ai-tool/
├── .env.example              # copy to .env (STRIX_LLM, LLM_API_KEY, DASH_*)
└── backend/                  # the whole deployable service (build context)
    ├── Dockerfile            # builds this folder -> one image
    ├── requirements.txt      # pinned lockfile (reproducible) + requirements.in
    ├── api/
    │   ├── main.py           # dashboard + control API (list/view/launch runs, PDF)
    │   └── webui/index.html  # the dashboard (served at /)
    ├── scripts/
    │   ├── serve_app.sh      # run the full app locally (loads ../.env)
    │   └── run_scan.sh       # optional: launch a scan from the CLI
    └── strix_runs/           # runs live here (bundled demo run included)
```
> Everything the service needs is under `backend/`, so platforms that build a
> service from its folder (e.g. **OrionHub**, which builds the `backend/` context)
> get a complete image — dashboard included.

## Run locally
```bash
cp .env.example .env          # set LLM_API_KEY + DASH_PASSWORD
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
backend/scripts/serve_app.sh 8080     # http://127.0.0.1:8080  (login: admin / your password)
```
Or via Docker (same as the platform build):
```bash
docker build -t soldieriq-cyber backend/
docker run -d -p 8080:8080 --env-file .env soldieriq-cyber
```

## Requirements & the one caveat
Runs on a **Docker host** (your Mac / an Orionhub node). Viewing runs works
anywhere; **launching** a scan needs a real Docker daemon (Strix starts a Kali
sandbox container), so on Kubernetes the pod needs Docker access (node socket).

## Config (env)
`STRIX_LLM`, `LLM_API_KEY` (or `LLM_API_BASE` for a local model), `DASH_USER`
(default `admin`), `DASH_PASSWORD`, `PORT` (default 8080), `RUNS_DIR`.

## API (behind basic-auth)
`GET /api/runs` · `/api/runs/{run}/summary` · `/vulnerabilities` · `/report.pdf` ·
`/transcript` · `POST /api/scans` `{target, instruction, authorized, max_budget}` ·
`GET /api/scans/{run}/status`

## Roadmap
- [ ] Metasploit via MCP (network exploitation)
- [ ] LLM on Orionhub's local GPU (Ollama / vLLM) — full air-gap
- [ ] Scan-launch on k3s (mount node Docker socket)
- [ ] Ingest SA data (TAK / knowledge base) as agent context

Engine: [Strix](https://github.com/usestrix/strix) (Apache-2.0).
