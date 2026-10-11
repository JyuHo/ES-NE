# SPDX-License-Identifier: GPL-3.0-or-later
"""esctl info [--full]

Écran « Informations système » d'ES: une ligne ``LIBELLÉ:valeur`` par information. Le frontend
coupe sur ``:`` et traduit le libellé (en majuscules): les valeurs n'en contiennent donc jamais.
"""
from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

from . import version

NAME = "info"


def available() -> bool:
    return True


def _clean(text: str) -> str:
    return " ".join(str(text).replace(":", " ").split())


def read_cpu_model(cpuinfo: Path = Path("/proc/cpuinfo")) -> str:
    try:
        for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
            key, _, value = line.partition(":")
            if key.strip() in ("model name", "Model", "Hardware") and value.strip():
                return value.strip()
    except OSError:
        pass
    return ""


def read_memory_mb(meminfo: Path = Path("/proc/meminfo")) -> int | None:
    try:
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        pass
    return None


def collect() -> list[tuple[str, str]]:
    uname = platform.uname()
    session = os.environ.get("XDG_SESSION_TYPE", "")
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
    memory = read_memory_mb()

    rows = [
        ("SYSTEM", version.read_distribution() or uname.system),
        ("ES-NE", version.read_version()),
        ("ARCHITECTURE", uname.machine),
        ("KERNEL", uname.release),
        ("CPU MODEL", read_cpu_model()),
        ("CPU CORES", str(os.cpu_count() or "")),
        ("MEMORY", f"{memory} MB" if memory is not None else ""),
        ("SESSION", " ".join(part for part in (desktop, session) if part)),
    ]
    return [(label, _clean(value)) for label, value in rows if value]


def run(args: list[str]) -> int:
    for arg in args:
        if arg != "--full":
            print(f"esctl info: option inconnue: {arg}", file=sys.stderr)
            return 2
    for label, value in collect():
        print(f"{label}:{value}")
    return 0
