# SPDX-License-Identifier: GPL-3.0-or-later
"""Jeux compressés (.zip, .7z): extraction pour les cores qui ne lisent pas les archives.

Un core dont le fichier ``.info`` liste ``zip`` / ``7z`` dans ``supported_extensions`` (arcade, par exemple) reçoit l'archive telle
quelle. Pour les autres, le contenu est extrait dans ``<cache>/extract/<système>/<nom de l'archive>/``: seul le dernier jeu est
gardé. Un contenu d'un seul fichier est renommé d'après l'archive, pour que les sauvegardes et états portent le même nom
que le jeu dans ES.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import zipfile
from pathlib import Path

from . import paths

log = logging.getLogger("es-launcher")

ARCHIVES = (".zip", ".7z")
SEVEN_ZIP = ("7z", "7zz", "7za", "7zr")
PREFERRED = ("m3u", "cue", "gdi", "ccd", "chd", "iso")  # fichiers « d'entrée » d'un contenu à plusieurs fichiers


def supported_extensions(info_file: Path) -> set[str] | None:
    """Extensions listées par le fichier .info d'un core (sans point, minuscules); None si illisible ou absent."""
    try:
        for line in info_file.read_text(encoding="utf-8", errors="replace").splitlines():
            key, _, value = line.partition("=")
            if key.strip() == "supported_extensions":
                return {ext.strip().lower() for ext in value.strip().strip('"').split("|") if ext.strip()}
    except OSError:
        pass
    return None


def pick_member(names: list[str], supported: set[str]) -> str | None:
    """Fichier à donner au core parmi ceux de l'archive: extension reconnue, fichiers d'entrée d'abord."""
    candidates = [n for n in names if not n.endswith("/") and Path(n).suffix.lstrip(".").lower() in supported]
    if not candidates:
        return None
    rank = {ext: i for i, ext in enumerate(PREFERRED)}
    return sorted(candidates, key=lambda n: (rank.get(Path(n).suffix.lstrip(".").lower(), len(rank)), n.lower()))[0]


def _list_zip(archive: Path) -> list[str]:
    with zipfile.ZipFile(archive) as z:
        return z.namelist()


def _extract_zip(archive: Path, target: Path) -> None:
    with zipfile.ZipFile(archive) as z:
        z.extractall(target)  # extractall neutralise les chemins absolus et « .. »


def _list_7z(archive: Path, tool: str, run=None) -> list[str]:
    run = run or subprocess.run
    out = run([tool, "l", "-ba", "-slt", str(archive)], capture_output=True, text=True, check=True).stdout
    names, current = [], {}
    for line in out.splitlines() + [""]:
        if not line.strip():
            if current.get("Path") and current.get("Folder") != "+":
                names.append(current["Path"])
            current = {}
            continue
        key, _, value = line.partition(" = ")
        current[key.strip()] = value.strip()
    return names


def _extract_7z(archive: Path, target: Path, tool: str, run=None) -> None:
    run = run or subprocess.run
    run([tool, "x", "-y", f"-o{target}", str(archive)], capture_output=True, check=True)


def seven_zip(which=shutil.which) -> str | None:
    for tool in SEVEN_ZIP:
        if which(tool):
            return tool
    return None


def prepare(rom: str, system: str, info_file: Path | None, which=shutil.which) -> str:
    """Chemin à donner au core. ``rom`` revient inchangé sauf archive que le core ne sait pas lire."""
    archive = Path(rom)
    suffix = archive.suffix.lower()
    if suffix not in ARCHIVES or info_file is None:
        return rom
    supported = supported_extensions(info_file)
    if not supported or suffix.lstrip(".") in supported:
        return rom  # info inconnue, ou le core lit l'archive lui-même

    tool = None
    if suffix == ".7z":
        tool = seven_zip(which)
        if tool is None:
            log.warning("%s: 7z introuvable (paquet 7zip), le core reçoit l'archive telle quelle", archive.name)
            return rom

    root = paths.cache_dir() / "extract" / system
    target = root / archive.stem
    stamp = f"{archive.stat().st_size}:{int(archive.stat().st_mtime)}"
    marker = target / ".esne-source"
    try:
        names = _list_zip(archive) if suffix == ".zip" else _list_7z(archive, tool)
        member = pick_member(names, supported)
        if member is None:
            log.warning("%s: aucun fichier reconnu par le core (%s)", archive.name, ", ".join(sorted(supported)))
            return rom
        if not (marker.is_file() and marker.read_text() == stamp and (target / member).is_file()):
            shutil.rmtree(root, ignore_errors=True)  # on ne garde que le dernier jeu
            target.mkdir(parents=True)
            _extract_zip(archive, target) if suffix == ".zip" else _extract_7z(archive, target, tool)
            marker.write_text(stamp)
            log.info("%s extrait dans %s", archive.name, target)
        result = target / member
        if len([n for n in names if not n.endswith("/")]) == 1:
            renamed = target / f"{archive.stem}{result.suffix}"
            if not renamed.exists():
                result.rename(renamed)
            result = renamed
        return str(result)
    except (OSError, zipfile.BadZipFile, subprocess.CalledProcessError) as exc:
        log.warning("%s: extraction impossible (%s), le core reçoit l'archive telle quelle", archive.name, exc)
        return rom
