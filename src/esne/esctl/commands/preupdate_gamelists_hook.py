# SPDX-License-Identifier: GPL-3.0-or-later
"""esctl preupdate-gamelists-hook

Appelé par ES avant la mise à jour des gamelists. Exécute, dans l'ordre alphabétique, les scripts exécutables de
``<config>/hooks/preupdate-gamelists/`` (aucun par défaut). Un script en échec est signalé sur stderr mais n'arrête pas ES.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from ... import paths

NAME = "preupdate-gamelists-hook"


def available() -> bool:
    return True


def hooks_dir() -> Path:
    return paths.config_dir() / "hooks" / "preupdate-gamelists"


def run(args: list[str], directory: Path | None = None) -> int:
    directory = directory or hooks_dir()
    if not directory.is_dir():
        return 0
    failed = 0
    for script in sorted(directory.iterdir()):
        if not script.is_file() or not os.access(script, os.X_OK):
            continue
        try:
            result = subprocess.run([str(script)], timeout=120)
        except (OSError, subprocess.SubprocessError) as exc:
            print(f"esctl preupdate-gamelists-hook: {script.name}: {exc}", file=sys.stderr)
            failed += 1
            continue
        if result.returncode != 0:
            print(f"esctl preupdate-gamelists-hook: {script.name} a renvoyé {result.returncode}", file=sys.stderr)
            failed += 1
    return 1 if failed else 0
