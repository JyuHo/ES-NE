# SPDX-License-Identifier: GPL-3.0-or-later
"""esctl thebezelproject list | install <système> | remove <système>

Remplace ``batocera-es-thebezelproject``. Les bezels viennent des dépôts GitHub de The Bezel Project
(``bezelproject-<Système>``, archive ``master.zip``). On ne garde que les images (``retroarch/overlay/GameBezels/**.png``
et l'image du système) dans ``<data>/decorations/thebezelproject/{games/<système>,systems}``.

``list`` écrit une ligne par système: ``[I]`` (installé) ou ``[A]`` (disponible), le nom du système ES et l'adresse du dépôt.
"""
from __future__ import annotations

import io
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from ... import bezels, paths

NAME = "thebezelproject"
GITHUB = "https://github.com/thebezelproject"
ARCHIVE = GITHUB + "/{repo}/archive/refs/heads/master.zip"
GAME_MARKER = "/retroarch/overlay/GameBezels/"
SYSTEM_MARKER = "/retroarch/overlay/"


def available() -> bool:
    return True


def root() -> Path:
    return paths.data_dir() / "decorations" / bezels.TBP_SET


def installed(system: str) -> bool:
    return (root() / "games" / system).is_dir()


def list_lines() -> list[str]:
    return [f"[{'I' if installed(system) else 'A'}] {system} {GITHUB}/{repo}" for system, repo in sorted(bezels.TBP_REPOS.items())]


def download(url: str, progress=print) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "esctl (ES-NE)"})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 (adresse fixe https)
        total = int(response.headers.get("Content-Length") or 0)
        chunks, done, step = [], 0, 0
        while True:
            block = response.read(1 << 20)
            if not block:
                break
            chunks.append(block)
            done += len(block)
            if total and done * 10 // total > step:
                step = done * 10 // total
                progress(f"{step * 10}%")
    return b"".join(chunks)


def extract(data: bytes, system: str, target: Path) -> int:
    """Extrait les images du zip dans ``target`` (``games/<système>`` et ``systems/<système>.png``); renvoie le nombre de bezels."""
    games = target / "games" / system
    count = 0
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for info in archive.infolist():
            name = info.filename
            if info.is_dir() or not name.lower().endswith(".png"):
                continue
            leaf = Path(name).name  # jamais de chemin issu de l'archive
            if GAME_MARKER in "/" + name:
                destination = games / leaf
                count += 1
            elif ("/" + name).rsplit("/", 1)[0].endswith(SYSTEM_MARKER.rstrip("/")):
                destination = target / "systems" / f"{system}.png"
            else:
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, open(destination, "wb") as out:
                shutil.copyfileobj(source, out)
    return count


def install(system: str, fetch=download, base: Path | None = None) -> int:
    repo = bezels.TBP_REPOS.get(system)
    if repo is None:
        print(f"esctl thebezelproject: système inconnu: {system}", file=sys.stderr)
        return 1
    base = base or root()
    print(f"Downloading {system} bezels")
    try:
        data = fetch(ARCHIVE.format(repo=repo))
    except (urllib.error.URLError, OSError) as exc:
        print(f"esctl thebezelproject: téléchargement impossible: {exc}", file=sys.stderr)
        return 1
    print(f"Extracting {system} bezels")
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=base) as tmp:
        staging = Path(tmp)
        try:
            count = extract(data, system, staging)
        except zipfile.BadZipFile:
            print("esctl thebezelproject: archive invalide", file=sys.stderr)
            return 1
        if count == 0:
            print("esctl thebezelproject: aucun bezel dans l'archive", file=sys.stderr)
            return 1
        _replace(staging / "games" / system, base / "games" / system)
        if (staging / "systems" / f"{system}.png").is_file():
            (base / "systems").mkdir(parents=True, exist_ok=True)
            shutil.move(str(staging / "systems" / f"{system}.png"), base / "systems" / f"{system}.png")
    print(f"{count} bezels installed")
    return 0


def _replace(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), destination)


def remove(system: str, base: Path | None = None) -> int:
    if system not in bezels.TBP_REPOS:
        print(f"esctl thebezelproject: système inconnu: {system}", file=sys.stderr)
        return 1
    base = base or root()
    shutil.rmtree(base / "games" / system, ignore_errors=True)
    (base / "systems" / f"{system}.png").unlink(missing_ok=True)
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
    print("usage: esctl thebezelproject list | install <système> | remove <système>", file=sys.stderr)
    return 2
