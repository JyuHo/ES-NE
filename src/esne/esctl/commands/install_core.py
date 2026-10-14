# SPDX-License-Identifier: GPL-3.0-or-later
"""esctl install-core <core> | package <core>

``install-core`` installe le paquet pacman d'un core libretro des dépôts officiels (via pkexec et l'aide
``/usr/lib/esne/install-core``, qui ne connaît qu'une liste blanche). Un core de l'AUR (liste blanche) est cloné dans
``~/.cache/esne/aur/<paquet>``, construit avec makepkg sous l'utilisateur (PKGBUILD non relu: l'appelant prévient),
puis installé par ``/usr/lib/esne/install-aur-core`` après authentification. ``package`` affiche ``<source> <paquet>``.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from ... import cores

NAME = "install-core"
EXIT_AUR = 3  # construction impossible (outils absents ou échec)
EXIT_UNKNOWN = 4


def available() -> bool:
    return shutil.which("pkexec") is not None and shutil.which("pacman") is not None


def cache_dir() -> Path:
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "esne" / "aur"


def build_aur(package: str, call=subprocess.call, base: Path | None = None) -> Path | None:
    """Clone (ou met à jour) le PKGBUILD de l'AUR puis construit le paquet: renvoie le fichier .pkg.tar, ou None."""
    directory = (base or cache_dir()) / package
    directory.parent.mkdir(parents=True, exist_ok=True)
    if (directory / ".git").is_dir():
        status = call(["git", "-C", str(directory), "pull", "--ff-only"])
    else:
        status = call(["git", "clone", "--depth", "1", cores.AUR_GIT.format(package=package), str(directory)])
    if status != 0:
        print(f"téléchargement de {package} depuis l'AUR impossible", file=sys.stderr)
        return None
    for old in directory.glob("*.pkg.tar.*"):
        old.unlink()
    if call(["makepkg", "-f", "--noconfirm", "--nocheck"], cwd=str(directory)) != 0:
        print(f"construction de {package} impossible (dépendances manquantes ? voir makepkg)", file=sys.stderr)
        return None
    built = sorted(p for p in directory.glob("*.pkg.tar.*") if "-debug-" not in p.name and not p.name.endswith(".sig"))
    return built[-1] if built else None


def run(args: list[str], call=subprocess.call, build=build_aur) -> int:
    if len(args) == 2 and args[0] == "package":
        source, package = cores.classify(args[1])
        print(f"{source} {package}".rstrip())
        return 0 if source != "unknown" else EXIT_UNKNOWN
    if len(args) != 1:
        print("usage: esctl install-core <core>", file=sys.stderr)
        return 2
    core = args[0]
    source, package = cores.classify(core)
    if source == "unknown":
        print(f"core inconnu: {core}", file=sys.stderr)
        return EXIT_UNKNOWN
    if source == "aur":
        for tool in ("git", "makepkg"):
            if shutil.which(tool) is None and build is build_aur:
                print(f"{tool} est requis pour construire {package} (paquets base-devel et git)", file=sys.stderr)
                return EXIT_AUR
        built = build(package)
        if built is None:
            return EXIT_AUR
        return call(["pkexec", cores.AUR_HELPER, str(built)])
    return call(["pkexec", cores.HELPER, core])
