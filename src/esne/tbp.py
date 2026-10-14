# SPDX-License-Identifier: GPL-3.0-or-later
"""Bezels par jeu de The Bezel Project, téléchargés à la demande.

Chaque dépôt ``bezelproject-<Système>`` contient ``retroarch/overlay/GameBezels/<Système>/<nom de la ROM>.png`` (plus d'un millier
d'images par système: on ne télécharge que celles des jeux lancés). La liste des noms est mise en cache (30 jours); une image
téléchargée est rangée sous le nom de la ROM locale: ``<data>/decorations/thebezelproject/games/<système>/<ROM>.png``.
Bibliothèque standard uniquement. Sans réseau, rien n'est bloquant: on garde le bezel du système.
"""
from __future__ import annotations

import json
import logging
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from . import bezels, paths

log = logging.getLogger("es-launcher")

TREE_API = "https://api.github.com/repos/thebezelproject/{repo}/git/trees/master:retroarch/overlay/GameBezels/{folder}"
RAW = "https://raw.githubusercontent.com/thebezelproject/{repo}/master/retroarch/overlay/GameBezels/{folder}/{name}"
INDEX_MAX_AGE = 30 * 86400
RETRY_AFTER = 3600  # après un échec réseau, on ne réessaie pas la liste avant une heure
TIMEOUT = 5
REGION_ORDER = ("usa", "europe", "world", "japan")


def fetch(url: str, timeout: float = TIMEOUT) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "es-ne"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 (adresses https fixes)
        return response.read()


def games_root(base: Path | None = None) -> Path:
    return (base or paths.data_dir() / "decorations" / bezels.TBP_SET) / "games"


def game_file(system: str, rom_stem: str, base: Path | None = None) -> Path:
    return games_root(base) / system / f"{rom_stem}.png"


def _folder(repo: str) -> str:
    return repo.removeprefix("bezelproject-")


def _index_file(system: str) -> Path:
    return paths.cache_dir() / "thebezelproject" / f"{system}.json"


def load_index(system: str, get=None, now=time.time) -> list[str] | None:
    """Noms (sans ``.png``) des bezels du dépôt du système; None si inconnus et non téléchargeables."""
    get = get or fetch
    repo = bezels.TBP_REPOS.get(system)
    if repo is None:
        return None
    cache = _index_file(system)
    data = {}
    try:
        data = json.loads(cache.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    names = data.get("names") if isinstance(data.get("names"), list) else None
    fresh = names is not None and now() - float(data.get("fetched", 0)) < INDEX_MAX_AGE
    recent_failure = data.get("failed") is not None and now() - float(data["failed"]) < RETRY_AFTER
    if fresh or recent_failure:
        return names
    try:
        tree = json.loads(get(TREE_API.format(repo=repo, folder=_folder(repo))))
        names = sorted(entry["path"][:-4] for entry in tree["tree"] if entry.get("type") == "blob" and entry["path"].endswith(".png"))
        data = {"fetched": now(), "names": names}
    except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError) as exc:
        log.info("bezels par jeu %s: liste indisponible (%s)", system, exc)
        data = {**data, "failed": now()}
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass
    return data.get("names")


def _tags(name: str) -> list[str]:
    return [tag.lower() for tag in re.findall(r"\(([^)]*)\)", name)]


def _title(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\([^)]*\)|\[[^\]]*\]", "", name).lower())


def match(names: list[str], rom_stem: str) -> str | None:
    """Nom du bezel pour la ROM: nom identique, puis même titre (région identique si possible, sinon USA/Europe/World...)."""
    if rom_stem in names:
        return rom_stem
    lowered = {name.lower(): name for name in names}
    if rom_stem.lower() in lowered:
        return lowered[rom_stem.lower()]
    title = _title(rom_stem)
    if not title:
        return None
    candidates = [name for name in names if _title(name) == title]
    if not candidates:
        return None
    rom_tags = _tags(rom_stem)
    first_region = rom_tags[0] if rom_tags else None

    def rank(name: str):
        tags = _tags(name)
        same_region = bool(first_region and tags and tags[0] == first_region)
        region = tags[0] if tags else ""
        order = REGION_ORDER.index(region) if region in REGION_ORDER else len(REGION_ORDER)
        return (not same_region, len(tags) > 1, order, len(name), name)  # sans variantes (Alt, Rev...) de préférence

    return sorted(candidates, key=rank)[0]


def ensure_game(system: str, rom_stem: str, get=None, base: Path | None = None) -> Path | None:
    """Bezel du jeu, téléchargé au besoin. None s'il n'existe pas ou si le réseau est indisponible."""
    get = get or fetch
    destination = game_file(system, rom_stem, base)
    if destination.is_file():
        return destination
    names = load_index(system, get)
    if not names:
        return None
    name = match(names, rom_stem)
    if name is None:
        return None
    repo = bezels.TBP_REPOS[system]
    try:
        data = get(RAW.format(repo=repo, folder=_folder(repo), name=urllib.parse.quote(name + ".png")))
    except (urllib.error.URLError, OSError) as exc:
        log.info("bezel %s/%s: téléchargement impossible (%s)", system, name, exc)
        return None
    if not data.startswith(b"\x89PNG"):
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    temporary.write_bytes(data)
    temporary.replace(destination)
    log.info("bezel du jeu téléchargé: %s", destination)
    return destination
