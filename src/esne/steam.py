# SPDX-License-Identifier: GPL-3.0-or-later
"""Jeux Steam installés: lit les bibliothèques de Steam et crée un fichier ``.steam`` (contenant l'appid) par jeu.

Un jeu est installé quand ``steamapps/appmanifest_<appid>.acf`` a le bit 4 de ``StateFlags``. Les outils de Steam (Proton,
Steam Linux Runtime, redistribuables) sont écartés. ``es-genconfig`` appelle ``seed`` à chaque exécution; un fichier existant
n'est jamais écrasé et un jeu déjà présent (même appid) n'est pas recréé sous un autre nom.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOTS = (
    "~/.local/share/Steam",
    "~/.steam/steam",
    "~/.steam/root",
    "~/.var/app/com.valvesoftware.Steam/.local/share/Steam",
    "~/.var/app/com.valvesoftware.Steam/data/Steam",
)
TOOL_PREFIXES = ("Proton", "Steam Linux Runtime", "Steamworks Common Redistributables", "Steam Controller Configs")
TOOL_IDS = {"228980"}  # Steamworks Common Redistributables
INSTALLED = 4  # bit « StateInstalled » de StateFlags
PAIR = re.compile(r'"([^"]+)"\s+"([^"]*)"')


def libraries(roots=ROOTS) -> list[Path]:
    """Dossiers ``steamapps`` des bibliothèques connues (dossier de Steam + ``libraryfolders.vdf``), sans doublon."""
    found: list[Path] = []

    def add(path: Path) -> None:
        steamapps = path / "steamapps"
        resolved = steamapps.resolve() if steamapps.is_dir() else None
        if resolved is not None and resolved not in found:
            found.append(resolved)

    for root in roots:
        base = Path(root).expanduser()
        add(base)
        vdf = base / "steamapps" / "libraryfolders.vdf"
        try:
            text = vdf.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for key, value in PAIR.findall(text):
            if key == "path":
                add(Path(value.replace("\\\\", "\\")))
    return found


def parse_manifest(text: str) -> tuple[str, str] | None:
    """(appid, nom) d'un ``appmanifest`` installé, sinon None."""
    values: dict[str, str] = {}
    for key, value in PAIR.findall(text):
        values.setdefault(key.lower(), value)
    appid, name = values.get("appid", ""), values.get("name", "")
    try:
        installed = int(values.get("stateflags", "0")) & INSTALLED
    except ValueError:
        installed = 0
    if not (appid.isdigit() and name and installed) or appid in TOOL_IDS or name.startswith(TOOL_PREFIXES):
        return None
    return appid, name


def installed_games(directories: list[Path] | None = None) -> list[tuple[str, str]]:
    games: dict[str, str] = {}
    for steamapps in libraries() if directories is None else directories:
        for manifest in sorted(steamapps.glob("appmanifest_*.acf")):
            try:
                game = parse_manifest(manifest.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
            if game:
                games.setdefault(game[0], game[1])
    return sorted(((appid, name) for appid, name in games.items()), key=lambda item: item[1].lower())


def file_name(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "-", name).strip(" .")
    return f"{cleaned or 'jeu'}.steam"


def seed(roms: Path, games: list[tuple[str, str]] | None = None) -> list[str]:
    """Crée ``<roms>/steam/<Nom>.steam`` pour chaque jeu installé qui n'a pas encore de fichier. Renvoie les noms créés."""
    games = installed_games() if games is None else games
    if not games:
        return []
    folder = roms / "steam"
    known = set()
    if folder.is_dir():
        for existing in folder.glob("*.steam"):
            try:
                known.add(existing.read_text(encoding="utf-8", errors="ignore").strip())
            except OSError:
                pass
    created = []
    for appid, name in games:
        target = folder / file_name(name)
        if appid in known or target.exists():
            continue
        folder.mkdir(parents=True, exist_ok=True)
        target.write_text(appid + "\n", encoding="utf-8")
        created.append(target.name)
    return created
