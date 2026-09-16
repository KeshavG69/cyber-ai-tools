#!/usr/bin/env python3
"""Register an in-container 'local' Strix runtime backend (no Docker).

strix-agent 1.6.2 only ships the 'docker' backend, but exposes register_backend()
and the underlying openai-agents SDK ships a local (in-process) sandbox
(UnixLocalSandboxClient). This appends a 'local' backend so
STRIX_RUNTIME_BACKEND=local runs the tools inside THIS container/pod — no Docker
daemon required. The pentest tools must be installed in the image.

Idempotent. Run after `pip install strix-agent`.
"""
import pathlib

import strix.runtime.backends as backends

path = pathlib.Path(backends.__file__)
text = path.read_text()
MARKER = "SoldierIQ in-container local backend"

SNIPPET = '''

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

if MARKER in text:
    print(f"already patched: {path}")
else:
    path.write_text(text + SNIPPET)
    print(f"registered 'local' backend in: {path}")
