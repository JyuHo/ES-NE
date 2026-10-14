# SPDX-License-Identifier: GPL-3.0-or-later
"""esctl install-core <core> | package <core>

``install-core`` installe le paquet pacman d'un core libretro des dépôts officiels (via pkexec et l'aide
``/usr/lib/esne/install-core``, qui ne connaît qu'une liste blanche). Les cores de l'AUR ne sont jamais installés:
la commande indique le paquet à construire (code 3). ``package`` affiche ``<source> <paquet>``.
"""
from __future__ import annotations

import shutil
import subprocess
import sys

from ... import cores

NAME = "install-core"
EXIT_AUR = 3
EXIT_UNKNOWN = 4


def available() -> bool:
    return shutil.which("pkexec") is not None and shutil.which("pacman") is not None


def run(args: list[str], call=subprocess.call) -> int:
    if len(args) == 2 and args[0] == "package":
        source, package = cores.classify(args[1])
        print(f"{source} {package}".rstrip())
        return 0 if source != "unknown" else EXIT_UNKNOWN
    if len(args) != 1:
        print("usage: esctl install-core <core>", file=sys.stderr)
        return 2
    core = args[0]
    source, package = cores.classify(core)
    if source == "aur":
        print(f"{package} est dans l'AUR: installe-le avec ton assistant AUR (paru -S {package}).", file=sys.stderr)
        return EXIT_AUR
    if source == "unknown":
        print(f"core inconnu: {core}", file=sys.stderr)
        return EXIT_UNKNOWN
    return call(["pkexec", cores.HELPER, core])
