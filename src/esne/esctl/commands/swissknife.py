# SPDX-License-Identifier: GPL-3.0-or-later
"""esctl swissknife --emukill

Ferme l'émulateur lancé par ``es-launcher`` (groupe de processus dont le pid est dans ``<state>/emulator.pid``):
SIGTERM puis, s'il ne s'arrête pas en 5 s, SIGKILL. Sans émulateur en cours, ne fait rien.
"""
from __future__ import annotations

import os
import signal
import sys
import time

from ... import paths

NAME = "swissknife"


def available() -> bool:
    return True


def read_pid() -> int | None:
    try:
        pid = int(paths.emulator_pid_file().read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None
    return pid if pid > 1 else None


def alive(pid: int) -> bool:
    try:
        os.killpg(pid, 0)
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def emukill(grace: float = 5.0, sleep=time.sleep) -> int:
    pid = read_pid()
    if pid is None or not alive(pid):
        return 0
    try:
        os.killpg(pid, signal.SIGTERM)
    except OSError:
        return 0
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline and alive(pid):
        sleep(0.1)
    if alive(pid):
        try:
            os.killpg(pid, signal.SIGKILL)
        except OSError:
            pass
    return 0


def run(args: list[str]) -> int:
    if args == ["--emukill"]:
        return emukill()
    print("usage: esctl swissknife --emukill", file=sys.stderr)
    return 2
