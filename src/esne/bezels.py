# SPDX-License-Identifier: GPL-3.0-or-later
"""Bezels (décorations): choix de l'image, zone de jeu, fichier d'overlay RetroArch.

Disposition d'un jeu de décorations (identique à ES/Batocera), dans ``<data>/decorations`` puis ``<share>/decorations``::

    <jeu>/games/<système>/<rom>.png      bezel d'un jeu précis
    <jeu>/systems/<système>.png          bezel du système
    <jeu>/default.png                    bezel par défaut

Une image ``<nom>.png.info`` (JSON: width, height, top, left, bottom, right) donne la zone de jeu; sinon on la
déduit de la zone transparente de l'image (Pillow, optionnel).
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from . import paths

log = logging.getLogger("es-launcher")

TBP_SET = "thebezelproject"
ALPHA_LIMIT = 32  # un pixel est « transparent » en dessous de cette opacité (0-255)

# système ES-NE -> dépôt GitHub de The Bezel Project (https://github.com/thebezelproject/<dépôt>)
TBP_REPOS = {
    "nes": "bezelproject-NES",
    "snes": "bezelproject-SNES",
    "gb": "bezelproject-GB",
    "gbc": "bezelproject-GBC",
    "gba": "bezelproject-GBA",
    "mastersystem": "bezelproject-MasterSystem",
    "megadrive": "bezelproject-MegaDrive",
    "gamegear": "bezelproject-GameGear",
    "n64": "bezelproject-N64",
    "psx": "bezelproject-PSX",
    "pcengine": "bezelproject-PCEngine",
    "atari2600": "bezelproject-Atari2600",
    "nds": "bezelproject-NDS",
    "arcade": "bezelproject-MAME",
}


def decoration_dirs() -> list[Path]:
    return [paths.data_dir() / "decorations", paths.share_dir() / "decorations"]


def tbp_installed(system: str, directories=None) -> bool:
    return any((Path(d) / TBP_SET / "games" / system).is_dir() for d in directories or decoration_dirs())


def _tags_removed(name: str) -> str:
    return re.sub(r"\s*[\(\[][^\)\]]*[\)\]]", "", name).strip().lower()


def find_image(set_name: str, system: str, rom_stem: str, directories=None) -> Path | None:
    for directory in directories or decoration_dirs():
        base = Path(directory) / set_name
        games = base / "games" / system
        exact = games / f"{rom_stem}.png"
        if exact.is_file():
            return exact
        if games.is_dir():
            # même titre sans les étiquettes de région/révision: « Zelda (Europe) » -> « Zelda (USA) »
            wanted = _tags_removed(rom_stem)
            if wanted:
                for candidate in sorted(games.glob("*.png")):
                    if _tags_removed(candidate.stem) == wanted:
                        return candidate
        for fallback in (base / "systems" / f"{system}.png", base / "default.png"):
            if fallback.is_file():
                return fallback
    return None


@dataclass(frozen=True)
class Area:
    """Zone de jeu dans l'image, en pixels de l'image."""
    x: int
    y: int
    width: int
    height: int
    image_width: int
    image_height: int


def read_info(image: Path) -> Area | None:
    info = image.with_name(image.name + ".info")
    if not info.is_file():
        return None
    try:
        data = json.loads(info.read_text(encoding="utf-8"))
        width, height = int(data["width"]), int(data["height"])
        left, top = int(data.get("left", 0)), int(data.get("top", 0))
        right, bottom = int(data.get("right", 0)), int(data.get("bottom", 0))
    except (OSError, ValueError, KeyError, TypeError):
        log.warning("fichier .info de bezel illisible: %s", info)
        return None
    if width - left - right <= 0 or height - top - bottom <= 0:
        return None
    return Area(left, top, width - left - right, height - top - bottom, width, height)


def detect_area(image: Path) -> Area | None:
    """Zone transparente autour du centre de l'image (lignes et colonnes médianes). Nécessite Pillow."""
    try:
        from PIL import Image
    except ImportError:
        log.warning("Pillow absent (paquet python-pillow): zone de jeu des bezels non détectable")
        return None
    try:
        with Image.open(image) as source:
            if "A" not in source.getbands() and source.mode != "P":
                return None
            alpha = source.convert("RGBA").getchannel("A")
            width, height = alpha.size
            data = alpha.tobytes()
    except (OSError, ValueError) as exc:
        log.warning("bezel illisible %s: %s", image, exc)
        return None

    cx, cy = width // 2, height // 2
    if data[cy * width + cx] >= ALPHA_LIMIT:
        return None  # le centre est opaque: pas de fenêtre de jeu
    left = cx
    while left > 0 and data[cy * width + left - 1] < ALPHA_LIMIT:
        left -= 1
    right = cx
    while right < width - 1 and data[cy * width + right + 1] < ALPHA_LIMIT:
        right += 1
    top = cy
    while top > 0 and data[(top - 1) * width + cx] < ALPHA_LIMIT:
        top -= 1
    bottom = cy
    while bottom < height - 1 and data[(bottom + 1) * width + cx] < ALPHA_LIMIT:
        bottom += 1
    return Area(left, top, right - left + 1, bottom - top + 1, width, height)


def game_area(image: Path) -> Area | None:
    return read_info(image) or detect_area(image)


def viewport(area: Area, screen: tuple[int, int], stretch: bool = False, tolerance: float = 0.02):
    """Zone de jeu en pixels d'écran (x, y, largeur, hauteur), ou None si l'image ne convient pas à l'écran."""
    screen_w, screen_h = screen
    scale_x, scale_y = screen_w / area.image_width, screen_h / area.image_height
    if not stretch and abs(scale_x - scale_y) / max(scale_x, scale_y) > tolerance:
        return None
    return (round(area.x * scale_x), round(area.y * scale_y), round(area.width * scale_x), round(area.height * scale_y))


def write_overlay(image: Path, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "overlays = 1\n"
        f'overlay0_overlay = "{image}"\n'
        "overlay0_full_screen = true\n"
        "overlay0_descs = 0\n",
        encoding="utf-8",
    )
    return target
