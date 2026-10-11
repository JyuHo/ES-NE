# SPDX-License-Identifier: GPL-3.0-or-later
"""Catalogue des systèmes et des émulateurs (systems.yml, emulators.yml).

Les fichiers livrés avec le paquet sont complétés, système par système, par ceux de
``<config>/systems.yml`` et ``<config>/emulators.yml`` (l'utilisateur gagne).
"""
from __future__ import annotations

from importlib import resources
from pathlib import Path

import yaml

from . import paths
from .errors import INVALID_CONFIG, LaunchError

DEFAULT_PRIORITY = 100


def _load(name: str, user_dir: Path | None = None) -> dict:
    try:
        data = yaml.safe_load((resources.files("esne") / "data" / name).read_text(encoding="utf-8")) or {}
    except (OSError, ModuleNotFoundError, yaml.YAMLError):
        data = {}

    user = (user_dir or paths.config_dir()) / name
    if user.exists():
        try:
            override = yaml.safe_load(user.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError) as exc:
            raise LaunchError(INVALID_CONFIG, f"{user}: {exc}") from exc
        if not isinstance(override, dict):
            raise LaunchError(INVALID_CONFIG, f"{user}: un dictionnaire est attendu")
        data.update(override)

    return data


def systems(user_dir: Path | None = None) -> dict:
    return _load("systems.yml", user_dir)


def emulators(user_dir: Path | None = None) -> dict:
    return _load("emulators.yml", user_dir)


def default_choice(system: str, user_dir: Path | None = None) -> tuple[str | None, str | None]:
    """(émulateur, core) par défaut d'un système: la plus petite priorité, puis l'ordre du fichier."""
    entry = systems(user_dir).get(system)
    if not isinstance(entry, dict):
        return None, None

    best: tuple[int, str, str | None] | None = None
    for emulator, cores in (entry.get("emulators") or {}).items():
        if not cores:
            candidates = [(DEFAULT_PRIORITY, None)]
        else:
            candidates = [(int((opts or {}).get("priority", DEFAULT_PRIORITY)), core) for core, opts in cores.items()]
        for priority, core in candidates:
            if best is None or priority < best[0]:
                best = (priority, emulator, core)

    return (best[1], best[2]) if best else (None, None)


def emulator_info(emulator: str, user_dir: Path | None = None) -> dict | None:
    info = emulators(user_dir).get(emulator)
    return info if isinstance(info, dict) else None
