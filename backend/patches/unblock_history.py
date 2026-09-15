#!/usr/bin/env python3
"""Unblock the Strix viewer's "Past runs" history (remove the email gate).

The Strix viewer normally gates the run-history list (`/api/runs`) behind an
email one-time-code via ``auth.is_verified()``. This appends a module-level
override so ``is_verified()`` always returns True — the last definition wins —
which unlocks local run history with NO email verification required.

Idempotent. Run once after ``pip install strix-agent``:

    python backend/patches/unblock_history.py
"""
import pathlib

import strix.interface.viewer.auth as auth

MARKER = "SoldierIQ white-label: local history always unlocked"

path = pathlib.Path(auth.__file__)
text = path.read_text()

if MARKER in text:
    print(f"already unblocked: {path}")
else:
    path.write_text(text + f"\n\ndef is_verified():  # {MARKER}, no email\n    return True\n")
    print(f"unblocked history gate: {path}")
