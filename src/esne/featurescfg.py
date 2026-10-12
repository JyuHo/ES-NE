# SPDX-License-Identifier: GPL-3.0-or-later
"""Génère ``es_features.cfg`` (options par système et par jeu affichées par ES) et les jeux de shaders.

On ne déclare que ce que ``es-launcher`` sait appliquer.
"""
from __future__ import annotations

from pathlib import Path

from . import paths
from .generators import retroarch

# Fonctions d'ES (voir EmulatorFeatures::parseFeatures) prises en charge par le générateur libretro.
LIBRETRO_FEATURES = ["autosave", "ratio", "rewind", "smooth", "shaders", "pixel_perfect"]

# Presets libretro proposés dans « SHADER SET » s'ils sont installés (nom du fichier sans extension).
SHADER_SETS = [
    "crt-geom", "crt-easymode", "crt-aperture", "crt-lottes", "crt-royale", "zfast_crt",
    "scanlines", "sharp-bilinear", "lcd-grid-v2", "gameboy",
]


def render() -> str:
    return (
        '<?xml version="1.0"?>\n'
        "<features>\n"
        f'  <emulator name="libretro" features="{",".join(LIBRETRO_FEATURES)}" />\n'
        "</features>\n"
    )


def installed_shader_sets(names=SHADER_SETS, directories=None) -> list[str]:
    return [name for name in names if retroarch.find_shader(name, directories) is not None]


def write_shader_sets(target: Path, names: list[str]) -> list[Path]:
    """ES liste les dossiers <data>/shaders/configs/<jeu>/ qui contiennent rendering-defaults.yml."""
    written = []
    for name in names:
        file = target / name / "rendering-defaults.yml"
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(f"# jeu de shaders ES-NE: preset libretro '{name}'\nshader: {name}\n", encoding="utf-8")
        written.append(file)
    return written


def shaders_root() -> Path:
    return paths.data_dir() / "shaders" / "configs"
