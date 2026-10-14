# SPDX-License-Identifier: GPL-3.0-or-later
"""esctl install-core <core> | package <core>

``install-core`` installe le paquet pacman d'un core libretro des dépôts officiels (via pkexec et l'aide
``/usr/lib/esne/install-core``, qui ne connaît qu'une liste blanche). Un core de l'AUR (liste blanche) est cloné dans
``~/.cache/esne/aur/<paquet>``, construit avec makepkg sous l'utilisateur (PKGBUILD non relu: l'appelant prévient),
puis installé par ``/usr/lib/esne/install-aur-core`` après authentification. Si paru ou yay est installé, c'est lui qui construit
(``--sudo pkexec``: le mot de passe passe par polkit, dépendances comprises). ``package`` affiche ``<source> <paquet>``.
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


def assistant() -> str | None:
    """Assistant AUR installé (paru de préférence), ou None."""
    for name in ("paru", "yay"):
        if shutil.which(name):
            return name
    return None


def build_aur(package: str, call=subprocess.call, base: Path | None = None) -> Path | None:
    """Clone (ou met à jour) le PKGBUILD de l'AUR puis construit le paquet: renvoie le fichier .pkg.tar, ou None."""
    directory = (base or cache_dir()) / package
    directory.parent.mkdir(parents=True, exist_ok=True)
    if (directory / ".git").is_dir():
        status = call(["git", "-C", str(directory), "pull", "--ff-only"])
    else:
        status = call(["git", "clone", "--depth", "1", cores.AUR_GIT.format(package=package), str(directory)])
    if status != 0 or not (directory / "PKGBUILD").is_file():  # un paquet inexistant donne un dépôt vide
        print(f"{package}: absent de l'AUR", file=sys.stderr)
        return None
    for old in directory.glob("*.pkg.tar.*"):
        old.unlink()
    if call(["makepkg", "-f", "--noconfirm", "--nocheck"], cwd=str(directory)) != 0:
        print(f"construction de {package} impossible (dépendances manquantes ? voir makepkg)", file=sys.stderr)
        return None
    built = sorted(p for p in directory.glob("*.pkg.tar.*") if "-debug-" not in p.name and not p.name.endswith(".sig"))
    return built[-1] if built else None


def install_aur(core: str, call=subprocess.call, build=build_aur, helper=None) -> int:
    """Installe un core de l'AUR: avec paru/yay s'il y en a un (pkexec remplace sudo), sinon makepkg + aide root."""
    names = cores.AUR[core]
    tool = (helper or assistant)()
    for name in names:
        if tool:
            if call([tool, "-S", "--needed", "--noconfirm", "--sudo", "pkexec", name]) == 0:
                return 0
            continue
        built = build(name)
        if built is not None:
            return call(["pkexec", cores.AUR_HELPER, str(built)])
    print(f"aucun paquet de l'AUR n'a pu être installé pour {core} (essayés: {', '.join(names)})", file=sys.stderr)
    return EXIT_AUR


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
        if assistant() is None and (shutil.which("git") is None or shutil.which("makepkg") is None):
            print(f"git et base-devel (makepkg) sont requis pour construire {package}, ou installe paru/yay", file=sys.stderr)
            return EXIT_AUR
        return install_aur(core, call=call, build=build)
    return call(["pkexec", cores.HELPER, core])
