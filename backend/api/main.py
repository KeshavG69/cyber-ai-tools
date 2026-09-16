"""SoldierIQ Cyber — local control API + dashboard server.

Runs on a Docker host (your Mac). Serves the dashboard, lists runs, launches new
pentests with the Strix engine, and serves each run's data + report PDF.

Run it:
    export STRIX_LLM="openrouter/z-ai/glm-5.3"
    export LLM_API_KEY="..."            # or LLM_API_BASE for a local model
    export DASH_PASSWORD="..."          # optional (default: soldieriq)
    uvicorn backend.api.main:app --host 0.0.0.0 --port 8080

⚠️ Only scan targets you own / are authorized to test.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import secrets
import subprocess
import threading
import time

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

# Some platforms (e.g. OrionHub) deliver config as a mounted .env file rather than
# real env vars, and the container CMD runs uvicorn directly (no shell to source it).
# Load any .env we can find so STRIX_LLM / LLM_API_KEY / DASH_* are picked up.
# Real environment variables always take precedence (override=False).
try:
    from dotenv import load_dotenv

    for _envpath in (".env", "/app/.env", "/app/backend/.env"):
        load_dotenv(_envpath, override=False)
    load_dotenv(override=False)  # also search CWD upward
except Exception:
    pass

# STRIX_LLM has no default elsewhere and some platforms don't inject "app default"
# values. Default it (overridable by any real env var / OrionHub MANUAL value) so
# scans can launch — and so the strix subprocess, which reads STRIX_LLM from the
# environment, inherits it. LLM_API_KEY must still be provided by the platform.
os.environ.setdefault("STRIX_LLM", "openrouter/z-ai/glm-5.3")

# Paths are relative to this package so the service is self-contained (works both
# in local dev and when OrionHub builds the backend/ folder as the build context).
APP_DIR = pathlib.Path(__file__).resolve().parent          # .../backend/api
SERVICE_ROOT = APP_DIR.parent                              # .../backend
RUNS_DIR = pathlib.Path(os.environ.get("RUNS_DIR", SERVICE_ROOT / "strix_runs"))
INDEX = APP_DIR / "webui" / "index.html"
DASH_USER = os.environ.get("DASH_USER", "admin")
DASH_PASSWORD = os.environ.get("DASH_PASSWORD", "soldieriq")

RUNS_DIR.mkdir(parents=True, exist_ok=True)
app = FastAPI(title="SoldierIQ Cyber")
security = HTTPBasic()

# run_name -> subprocess.Popen for scans launched by this server
RUNNING: dict[str, subprocess.Popen] = {}
SEV_ORDER = ["critical", "high", "medium", "low", "info"]


def require_auth(cred: HTTPBasicCredentials = Depends(security)) -> bool:
    ok = secrets.compare_digest(cred.username, DASH_USER) and secrets.compare_digest(
        cred.password, DASH_PASSWORD
    )
    if not ok:
        raise HTTPException(status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Basic"})
    return True


def _load(run_dir: pathlib.Path, name: str, default=None):
    p = run_dir / name
    try:
        return json.loads(p.read_text()) if p.exists() else default
    except Exception:
        return default


def _run_dir(run: str) -> pathlib.Path:
    # prevent path traversal — only direct children of RUNS_DIR
    d = (RUNS_DIR / run).resolve()
    if d.parent != RUNS_DIR.resolve() or not d.is_dir():
        raise HTTPException(status_code=404, detail="unknown run")
    return d


def summarize(run_dir: pathlib.Path) -> dict:
    run = _load(run_dir, "run.json", {}) or {}
    vulns = _load(run_dir, "vulnerabilities.json", []) or []
    agents = _load(run_dir, ".state/agents.json", {}) or {}
    ti = (run.get("targets_info") or [{}])[0]
    target = (ti.get("details") or {}).get("target_url") or ti.get("original") or "—"

    def parse(x):
        try:
            return dt.datetime.fromisoformat(x)
        except Exception:
            return None

    start, end = parse(run.get("start_time")), parse(run.get("end_time"))
    counts = {k: 0 for k in SEV_ORDER}
    for v in vulns:
        s = str(v.get("severity", "")).lower()
        if s in counts:
            counts[s] += 1
    lu = run.get("llm_usage") or {}
    sr = run.get("scan_results") or {}
    proc = RUNNING.get(run_dir.name)
    running = bool(proc and proc.poll() is None) or (run.get("status") not in ("completed", "failed", None) and not run.get("end_time"))
    status = "running" if running else (run.get("status") or "completed")
    return {
        "run_name": run.get("run_name") or run_dir.name,
        "target": target,
        "mode": run.get("scan_mode"),
        "status": status,
        "start": run.get("start_time"),
        "end": run.get("end_time"),
        "duration_seconds": int((end - start).total_seconds()) if start and end else None,
        "requests": lu.get("requests"),
        "total_tokens": lu.get("total_tokens"),
        "agents": len(agents.get("names") or {}),
        "total_findings": len(vulns),
        "severity_counts": counts,
        "executive_summary": sr.get("executive_summary"),
        "instruction": run.get("user_instruction") or run.get("instruction"),
    }


def _mtime(run_dir: pathlib.Path) -> float:
    rj = run_dir / "run.json"
    return rj.stat().st_mtime if rj.exists() else run_dir.stat().st_mtime


# ------------------------------------------------------------------ routes


@app.get("/", response_class=HTMLResponse)
def index(_: bool = Depends(require_auth)):
    if not INDEX.exists():
        return HTMLResponse("<h1>SoldierIQ Cyber</h1><p>frontend not found</p>", status_code=500)
    return HTMLResponse(INDEX.read_text())


@app.get("/api/runs")
def list_runs(_: bool = Depends(require_auth)):
    dirs = [d for d in RUNS_DIR.iterdir() if d.is_dir() and (d / "run.json").exists()]
    dirs.sort(key=_mtime, reverse=True)
    return [summarize(d) for d in dirs]


@app.get("/api/runs/{run}/summary")
def run_summary(run: str, _: bool = Depends(require_auth)):
    return summarize(_run_dir(run))


@app.get("/api/runs/{run}/vulnerabilities")
def run_vulns(run: str, _: bool = Depends(require_auth)):
    return JSONResponse(_load(_run_dir(run), "vulnerabilities.json", []) or [])


@app.get("/api/runs/{run}/report.pdf")
def run_pdf(run: str, _: bool = Depends(require_auth)):
    run_dir = _run_dir(run)
    try:
        from strix.interface.viewer.report_pdf import generate_report_pdf

        pdf = generate_report_pdf(run_dir)
    except Exception as e:
        raise HTTPException(status_code=409, detail=f"report not ready: {e}")
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="soldieriq-cyber-{run}.pdf"'},
    )


@app.get("/api/runs/{run}/transcript")
def run_transcript(run: str, after: int = 0, _: bool = Depends(require_auth)):
    """Live agent activity: reasoning ('chat') + tool calls ('tool').

    `after` returns only events past that index so a polling client streams
    incrementally instead of refetching the whole (large) transcript.
    """
    run_dir = _run_dir(run)
    try:
        from strix.interface.viewer.transcript import build_run_state

        state = build_run_state(run_dir)
    except Exception:
        return {"agents": [], "events": [], "total": 0}
    events = state.get("events", []) or []
    after = max(0, int(after))
    return {"agents": state.get("agents", []), "total": len(events), "events": events[after:]}


@app.get("/api/debug/config")
def debug_config(_: bool = Depends(require_auth)):
    """Diagnostic: shows how config reaches the container (presence only, NO values)."""
    keys = ["STRIX_LLM", "LLM_API_KEY", "LLM_API_BASE", "DASH_USER", "DASH_PASSWORD", "RUNS_DIR", "STRIX_RUNTIME_BACKEND"]
    dotenv_files = {p: pathlib.Path(p).exists() for p in (".env", "/app/.env", "/app/backend/.env")}
    return {
        "env_present": {k: bool(os.environ.get(k)) for k in keys},
        "dotenv_files_found": dotenv_files,
        "cwd": os.getcwd(),
        "total_env_vars": len(os.environ),
        # key NAMES only (never values) so we can see the injection mechanism
        "matching_env_names": sorted(
            k for k in os.environ if any(t in k.upper() for t in ("STRIX", "LLM", "DASH", "OPENROUTER"))
        ),
    }


@app.get("/api/scans/{run}/status")
def scan_status(run: str, _: bool = Depends(require_auth)):
    s = summarize(_run_dir(run))
    return {"run_name": run, "status": s["status"], "total_findings": s["total_findings"], "severity_counts": s["severity_counts"], "agents": s["agents"]}


class NewScan(BaseModel):
    target: str
    instruction: str | None = None
    authorized: bool = False
    max_budget: float | None = 10.0  # USD cap passed to the engine; None/0 = no cap


@app.post("/api/scans")
def start_scan(body: NewScan, _: bool = Depends(require_auth)):
    if not body.authorized:
        raise HTTPException(status_code=400, detail="You must confirm you are authorized to test this target.")
    target = body.target.strip()
    if not re.match(r"^https?://[^\s]+$", target):
        raise HTTPException(status_code=400, detail="Target must be an http(s) URL you own/are authorized to test.")
    if not os.environ.get("STRIX_LLM") or not (os.environ.get("LLM_API_KEY") or os.environ.get("LLM_API_BASE")):
        raise HTTPException(status_code=500, detail="Server missing STRIX_LLM / LLM_API_KEY. Set them before launching scans.")

    instruction = (body.instruction or "").strip() or (
        "Authorized security assessment. Perform a thorough OWASP Top 10 assessment and validate findings with working proof-of-concepts."
    )
    cmd = ["strix", "-n", "-t", target, "--instruction", instruction]
    if body.max_budget and body.max_budget > 0:
        cmd += ["--max-budget", str(body.max_budget)]
    proc = subprocess.Popen(
        cmd,
        cwd=str(RUNS_DIR.parent),
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    captured = {"run": None}
    lines: list[str] = []          # rolling buffer of engine output (last 200 lines)
    lock = threading.Lock()

    def _redact(text: str) -> str:
        # never echo secret values back to the client or into logs
        for var in ("LLM_API_KEY", "DASH_PASSWORD"):
            val = os.environ.get(var)
            if val and len(val) >= 6:
                text = text.replace(val, "***")
        return text

    def reader():
        assert proc.stdout is not None
        for line in proc.stdout:
            clean = _redact(line.rstrip("\n"))
            with lock:
                lines.append(clean)
                if len(lines) > 200:
                    del lines[:-200]
            # tee to container stdout so full engine output shows in platform logs
            print(f"[strix] {clean}", flush=True)
            if not captured["run"]:
                m = re.search(r"strix_runs/([A-Za-z0-9._-]+)", line)
                if m:
                    captured["run"] = m.group(1)
                    RUNNING[captured["run"]] = proc
        try:
            proc.stdout.close()
        except Exception:
            pass

    threading.Thread(target=reader, daemon=True).start()
    for _i in range(60):  # wait up to ~30s for the run dir/name
        if captured["run"]:
            break
        if proc.poll() is not None:
            time.sleep(0.3)  # let the reader drain any final lines
            with lock:
                tail = "\n".join(lines[-40:]).strip()
            hint = _redact(tail) or "no output captured from the engine"
            raise HTTPException(
                status_code=500,
                detail=f"Scan process exited (code {proc.returncode}) before a run started. Engine output:\n{hint}",
            )
        time.sleep(0.5)
    if not captured["run"]:
        raise HTTPException(status_code=504, detail="Scan started but run id not detected yet; check Past runs shortly.")
    return {"run_name": captured["run"], "status": "running"}
