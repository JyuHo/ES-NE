# SPDX-License-Identifier: GPL-3.0-or-later
"""Cores libretro: paquet Arch correspondant, installation en un clic.

Seuls les cores des dépôts officiels (liste blanche ci-dessous) sont installables automatiquement; les cores de l'AUR
sont signalés avec le nom du paquet à construire soi-même. Lorsqu'un lancement échoue faute de core, ``es-launcher``
écrit un fichier d'indice que le frontend lit pour proposer l'installation.
"""
from __future__ import annotations

import os
from pathlib import Path

# nom du core (fichier <core>_libretro.so) -> paquet des dépôts officiels
OFFICIAL = {
    "nestopia": "libretro-nestopia",
    "snes9x": "libretro-snes9x",
    "bsnes": "libretro-bsnes",
    "gambatte": "libretro-gambatte",
    "mgba": "libretro-mgba",
    "genesis_plus_gx": "libretro-genesis-plus-gx",
    "picodrive": "libretro-picodrive",
    "mupen64plus_next": "libretro-mupen64plus-next",
    "parallel_n64": "libretro-parallel-n64",
    "mednafen_psx": "libretro-beetle-psx",
    "mednafen_pce_fast": "libretro-beetle-pce-fast",
    "melonds": "libretro-melonds",
    "desmume": "libretro-desmume",
    "ppsspp": "libretro-ppsspp",
    "mame": "libretro-mame",
}

# cores absents des dépôts officiels -> noms possibles du paquet de l'AUR (le premier existant est utilisé)
AUR = {
    "fceumm": ["libretro-fceumm", "libretro-fceumm-git"],
    "fbneo": ["libretro-fbneo", "libretro-fbneo-git"],
    "pcsx_rearmed": ["libretro-pcsx-rearmed", "libretro-pcsx-rearmed-git"],
    "stella": ["libretro-stella", "libretro-stella-git"],
    "gpsp": ["libretro-gpsp", "libretro-gpsp-git"],
    "swanstation": ["libretro-swanstation", "libretro-swanstation-git"],
}


def aur_names() -> set[str]:
    return {name for names in AUR.values() for name in names}


POLKIT_ACTION = "org.esne.install-core"
HELPER = "/usr/lib/esne/install-core"
AUR_HELPER = "/usr/lib/esne/install-aur-core"
AUR_GIT = "https://aur.archlinux.org/{package}.git"


def hint_file() -> Path:
    # ES lit ce chemin en dur (FileData.cpp)
    return Path(os.environ.get("ESNE_MISSING_CORE_FILE") or "/tmp/esne-missing-core")


def classify(core: str) -> tuple[str, str]:
    """(source, paquet): source vaut ``official``, ``aur`` ou ``unknown`` (paquet vide)."""
    if core in OFFICIAL:
        return "official", OFFICIAL[core]
    if core in AUR:
        return "aur", AUR[core][0]
    return "unknown", ""


def write_hint(core: str) -> None:
    """Trois lignes: core, paquet, source. Facultatif: une erreur d'écriture est ignorée."""
    source, package = classify(core)
    try:
        hint_file().write_text(f"{core}\n{package}\n{source}\n", encoding="utf-8")
    except OSError:
        pass


def clear_hint() -> None:
    try:
        hint_file().unlink()
    except OSError:
        pass
