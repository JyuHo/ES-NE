# SPDX-License-Identifier: GPL-3.0-or-later
"""Catalogue des systèmes et des émulateurs (systems.yml, emulators.yml).

Les fichiers livrés avec le paquet sont complétés, système par système, par ceux de
``<config>/systems.yml`` et ``<config>/emulators.yml`` (l'utilisateur gagne).
"""
from __future__ import annotations

import copy
import functools
from pathlib import Path

import yaml

from . import paths
from .errors import INVALID_CONFIG, LaunchError

DEFAULT_PRIORITY = 100
DATA_DIR = Path(__file__).resolve().parent / "data"


_YamlLoader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)  # l'analyseur en C est ~10 fois plus rapide


@functools.lru_cache(maxsize=16)
def _parse(path: str, stamp: tuple[int, int]) -> object:
    """Contenu d'un fichier YAML; ``stamp`` (taille, date) invalide le cache quand le fichier change."""
    with open(path, encoding="utf-8") as handle:
        return yaml.load(handle, Loader=_YamlLoader) or {}  # noqa: S506 (SafeLoader)


def _read(path: Path) -> object:
    info = path.stat()
    return copy.deepcopy(_parse(str(path), (info.st_size, info.st_mtime_ns)))


def _load(name: str, user_dir: Path | None = None) -> dict:
    try:
        data = _read(DATA_DIR / name)
    except (OSError, ModuleNotFoundError, yaml.YAMLError):
        data = {}
    if not isinstance(data, dict):
        data = {}

    user = (user_dir or paths.config_dir()) / name
    if user.exists():
        try:
            override = _read(user)
        except (OSError, yaml.YAMLError) as exc:
            raise LaunchError(INVALID_CONFIG, f"{user}: {exc}") from exc
        if not isinstance(override, dict):
            raise LaunchError(INVALID_CONFIG, f"{user}: un dictionnaire est attendu")
        data.update(override)

    return data


def load_data(name: str, user_dir: Path | None = None) -> dict:
    """Fichier de données du paquet complété par celui de ``<config>`` (clé par clé)."""
    return _load(name, user_dir)


def systems(user_dir: Path | None = None) -> dict:
    return _load("systems.yml", user_dir)


def emulators(user_dir: Path | None = None) -> dict:
    return _load("emulators.yml", user_dir)


def choices(entry: dict) -> list[tuple[str, str | None, int]]:
    """[(émulateur, core, priorité)] d'un système, dans l'ordre du fichier.

    Émulateur à cores (libretro): ``libretro: {snes9x: {priority: 1}, bsnes: {}}``.
    Émulateur autonome (sans core): ``dolphin: {}`` ou ``eden: {_priority: 1}``.
    """
    found = []
    for emulator, cores in (entry.get("emulators") or {}).items():
        if not cores or "_priority" in cores:
            found.append((emulator, None, int((cores or {}).get("_priority", DEFAULT_PRIORITY))))
            continue
        for core, opts in cores.items():
            found.append((emulator, core, int((opts or {}).get("priority", DEFAULT_PRIORITY))))
    return found


def default_choice(system: str, user_dir: Path | None = None) -> tuple[str | None, str | None]:
    """(émulateur, core) par défaut d'un système: la plus petite priorité, puis l'ordre du fichier."""
    entry = systems(user_dir).get(system)
    if not isinstance(entry, dict):
        return None, None

    best = None
    for emulator, core, priority in choices(entry):
        if best is None or priority < best[0]:
            best = (priority, emulator, core)
    return (best[1], best[2]) if best else (None, None)


def emulator_info(emulator: str, user_dir: Path | None = None) -> dict | None:
    info = emulators(user_dir).get(emulator)
    return info if isinstance(info, dict) else None
