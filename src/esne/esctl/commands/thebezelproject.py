# SPDX-License-Identifier: GPL-3.0-or-later
"""esctl thebezelproject list | install <système> | remove <système> | games <système>

Remplace ``batocera-es-thebezelproject``. ``install`` télécharge l'image du système du dépôt GitHub de The Bezel Project
(``bezelproject-<Système>``, dossier ``retroarch/overlay``) dans ``<data>/decorations/thebezelproject/systems/<système>.png``:
c'est le bezel de repli et ce qui active les bezels du système. Les bezels par jeu (``games/<système>/<ROM>.png``) sont
téléchargés à la demande au lancement d'un jeu (voir ``tbp.py``); ``games`` les télécharge d'avance pour toutes les ROM du système.

``list`` écrit une ligne par système: ``[I]`` (installé) ou ``[A]`` (disponible), le nom du système ES et l'adresse du dépôt.
"""
from __future__ import annotations

import json
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from ... import bezels, paths, tbp

NAME = "thebezelproject"
GITHUB = "https://github.com/thebezelproject"
API = "https://api.github.com/repos/thebezelproject/{repo}/contents/retroarch/overlay"
RAW = "https://raw.githubusercontent.com/thebezelproject/{repo}/master/retroarch/overlay/{name}"


def available() -> bool:
    return True


def root() -> Path:
    return paths.data_dir() / "decorations" / bezels.TBP_SET


def target(system: str, base: Path | None = None) -> Path:
    return (base or root()) / "systems" / f"{system}.png"


def cleanup(base: Path, system: str | None = None) -> None:
    """Supprime les restes d'une ancienne version (jeu « thebezelproject-system »), les bezels des jeux du système si
    ``system`` est donné, et les dossiers vides: ES liste chaque dossier de ``decorations/`` comme un jeu de décorations."""
    if system:
        shutil.rmtree(base / "games" / system, ignore_errors=True)
    shutil.rmtree(base.parent / "thebezelproject-system", ignore_errors=True)
    for folder in (base / "games", base / "systems", base):
        try:
            folder.rmdir()  # seulement s'il est vide
        except OSError:
            pass


def installed(system: str) -> bool:
    return target(system).is_file()


def list_lines() -> list[str]:
    return [f"[{'I' if installed(system) else 'A'}] {system} {GITHUB}/{repo}" for system, repo in sorted(bezels.TBP_REPOS.items())]


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "esctl (ES-NE)"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def pick_image(names: list[str]) -> str | None:
    """Image du système parmi celles du dossier overlay (MAME en a deux: on prend l'horizontale)."""
    images = sorted(name for name in names if name.lower().endswith(".png"))
    horizontal = [name for name in images if "vertical" not in name.lower()]
    return (horizontal or images or [None])[0]


def install(system: str, get=fetch, base: Path | None = None) -> int:
    repo = bezels.TBP_REPOS.get(system)
    if repo is None:
        print(f"esctl thebezelproject: système inconnu: {system}", file=sys.stderr)
        return 1
    print(f"Downloading {system} bezel")
    try:
        listing = json.loads(get(API.format(repo=repo)))
        name = pick_image([entry["name"] for entry in listing if entry.get("type") == "file"])
        if name is None:
            print("esctl thebezelproject: aucune image dans le dépôt", file=sys.stderr)
            return 1
        data = get(RAW.format(repo=repo, name=urllib.parse.quote(name)))
    except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"esctl thebezelproject: téléchargement impossible: {exc}", file=sys.stderr)
        return 1
    if not data.startswith(b"\x89PNG"):
        print("esctl thebezelproject: le fichier téléchargé n'est pas une image PNG", file=sys.stderr)
        return 1
    destination = target(system, base)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    temporary.write_bytes(data)
    temporary.replace(destination)
    cleanup(base or root())
    print(f"{system} bezel installed")
    return 0


def remove(system: str, base: Path | None = None) -> int:
    if system not in bezels.TBP_REPOS:
        print(f"esctl thebezelproject: système inconnu: {system}", file=sys.stderr)
        return 1
    base = base or root()
    target(system, base).unlink(missing_ok=True)
    cleanup(base, system)
    return 0


SKIP_SUFFIXES = {".xml", ".txt", ".png", ".jpg", ".jpeg", ".mp4", ".sav", ".srm", ".state", ".cfg", ".ini", ".db", ".bak", ".tmp"}


def rom_stems(system: str, roms: Path | None = None) -> list[str]:
    """Noms (sans extension) des ROM du système, sans doublons (un ``.cue`` et son ``.bin`` donnent un seul nom)."""
    folder = (roms or paths.roms_dir()) / system
    stems = set()
    try:
        entries = list(folder.iterdir())
    except OSError:
        return []
    for entry in entries:
        if entry.name.startswith(".") or entry.suffix.lower() in SKIP_SUFFIXES:
            continue
        stems.add(entry.stem if entry.is_file() else entry.name)
    return sorted(stems)


def games(system: str, get=None, roms: Path | None = None, base: Path | None = None) -> int:
    if system not in bezels.TBP_REPOS:
        print(f"esctl thebezelproject: système inconnu: {system}", file=sys.stderr)
        return 1
    stems = rom_stems(system, roms)
    get = get or tbp.fetch
    if tbp.load_index(system, get) is None:
        print("esctl thebezelproject: liste des bezels indisponible (réseau ?)", file=sys.stderr)
        return 1
    done = missing = 0
    for stem in stems:
        if tbp.ensure_game(system, stem, get, base) is None:
            missing += 1
        else:
            done += 1
    print(f"{system}: {done} bezels de jeu en place, {missing} jeux sans bezel (le bezel du système sera utilisé)")
    return 0


def run(args: list[str]) -> int:
    action = args[0] if args else ""
    if action == "list" and len(args) == 1:
        print("\n".join(list_lines()))
        return 0
    if action == "install" and len(args) == 2:
        return install(args[1])
    if action == "remove" and len(args) == 2:
        return remove(args[1])
    if action == "games" and len(args) == 2:
        return games(args[1])
    print("usage: esctl thebezelproject list | install <système> | remove <système> | games <système>", file=sys.stderr)
    return 2
