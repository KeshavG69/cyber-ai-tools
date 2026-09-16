#!/usr/bin/env python3
"""Make strix-agent 1.6.2 run fully in-container (no Docker daemon).

strix-agent 1.6.2 ships only the "docker" runtime backend, and its CLI
hard-exits at startup if the `docker` binary is missing (check_docker_installed)
or fails while pulling the sandbox image (pull_docker_image) — both BEFORE it
ever consults the selected runtime backend. On Railway Services / OrionHub k3s
pods there is no Docker daemon, so scans die instantly with "DOCKER NOT
INSTALLED".

This patch does two things, both gated on STRIX_RUNTIME_BACKEND=local:
  1. registers a "local" runtime backend backed by the openai-agents
     unix_local sandbox, so pentest tools run inside THIS container/pod; and
  2. turns check_docker_installed() / pull_docker_image() into no-ops so the
     CLI's Docker preflight is skipped.

The tools must be installed in the image (see backend/Dockerfile). Idempotent —
safe to run repeatedly. Run after `pip install strix-agent`.
"""
import importlib
import pathlib


def _append_once(module_name: str, marker: str, snippet: str) -> None:
    mod = importlib.import_module(module_name)
    path = pathlib.Path(mod.__file__)
    text = path.read_text()
    if marker in text:
        print(f"already patched: {path}")
        return
    path.write_text(text + snippet)
    print(f"patched ({marker}): {path}")


# --- 1. in-container "local" runtime backend ---------------------------------
BACKEND_MARKER = "SoldierIQ in-container local backend"
BACKEND_SNIPPET = '''

# --- SoldierIQ in-container local backend (no Docker) ---
async def _local_backend(*, image=None, manifest=None, exposed_ports=(), bind_mounts=None):
    """Run tools in THIS container's filesystem via the SDK unix_local sandbox.

    `image`/`bind_mounts` are ignored (execution is local); tools must be
    installed in the image. Selected via STRIX_RUNTIME_BACKEND=local.
    """
    from agents.sandbox.sandboxes.unix_local import (
        UnixLocalSandboxClient,
        UnixLocalSandboxClientOptions,
    )

    client = UnixLocalSandboxClient()
    options = UnixLocalSandboxClientOptions(exposed_ports=tuple(exposed_ports or ()))
    session = await client.create(options=options, manifest=manifest)
    await session.start()
    return client, session


register_backend("local", _local_backend, supports_bind_mounts=False)
'''

# --- 2. skip the CLI Docker preflight in local mode --------------------------
PREFLIGHT_MARKER = "SoldierIQ skip Docker preflight"
PREFLIGHT_SNIPPET = '''

# --- SoldierIQ skip Docker preflight when STRIX_RUNTIME_BACKEND=local ---
import os as _soldieriq_os

_soldieriq_orig_check_docker_installed = check_docker_installed
_soldieriq_orig_pull_docker_image = pull_docker_image


def _soldieriq_local_mode() -> bool:
    return _soldieriq_os.environ.get("STRIX_RUNTIME_BACKEND", "docker").strip().lower() == "local"


def check_docker_installed() -> None:  # noqa: F811
    if _soldieriq_local_mode():
        return
    _soldieriq_orig_check_docker_installed()


def pull_docker_image() -> None:  # noqa: F811
    if _soldieriq_local_mode():
        return
    _soldieriq_orig_pull_docker_image()
'''


if __name__ == "__main__":
    _append_once("strix.runtime.backends", BACKEND_MARKER, BACKEND_SNIPPET)
    _append_once("strix.interface.environment", PREFLIGHT_MARKER, PREFLIGHT_SNIPPET)
