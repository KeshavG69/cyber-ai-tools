# frontend

The custom **SoldierIQ Cyber** dashboard — a single self-contained page, no build
step, no framework.

- `app/index.html` — talks to the backend API (`../backend/api/main.py`):
  - a **run switcher** (header dropdown) listing runs from `GET /api/runs`
  - **＋ New Pentest** → a form (target URL, instructions, authorization checkbox)
    that `POST`s to `/api/scans`, then polls `/api/scans/{run}/status` and updates
    live as the scan runs
  - the overview, severity stats, and an expandable **findings list** (description /
    impact / technical analysis / PoC / remediation / CVSS)
  - a **Download PDF** link (`/api/runs/{run}/report.pdf`)

It is served by the FastAPI app at `/` (behind basic-auth). There is no Strix
viewer, token, or email — just our UI reading plain JSON from our own API.

A future richer frontend (e.g. Next.js, live agent-transcript streaming) would
consume the same API and can replace this file.
