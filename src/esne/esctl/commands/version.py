# SPDX-License-Identifier: GPL-3.0-or-later
"""esctl version [--extra]

Sans option: la version d'ES-NE sur une ligne. Le frontend l'affiche dans le menu.
--extra: informations complémentaires (distribution), ou rien.
"""
from __future__ import annotations

import sys
from pathlib import Path

from ... import __version__, paths

NAME = "version"


def available() -> bool:
    return True


def read_version() -> str:
    """<share>/esne.version si présent (écrit par le paquet), sinon la version du package Python."""
    version_file = paths.share_dir() / "esne.version"
    try:
        for line in version_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                return line.strip()
    except OSError:
        pass
    return __version__


def read_distribution(os_release: Path = Path("/etc/os-release")) -> str:
    try:
        for line in os_release.read_text(encoding="utf-8").splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return ""


def run(args: list[str]) -> int:
    extra = False
    for arg in args:
        if arg == "--extra":
            extra = True
        else:
            print(f"esctl version: option inconnue: {arg}", file=sys.stderr)
            return 2

    if extra:
        text = read_distribution()
        if text:
            print(text)
        return 0

    print(read_version())
    return 0
