# SPDX-License-Identifier: GPL-3.0-or-later
"""Bezels (décorations): choix de l'image, zone de jeu, fichier d'overlay RetroArch.

Disposition d'un jeu de décorations (identique à ES/Batocera), dans ``<data>/decorations`` puis ``<share>/decorations``::

    <jeu>/systems/<système>.png          bezel du système
    <jeu>/default.png                    bezel par défaut

Une image ``<nom>.png.info`` (JSON: width, height, top, left, bottom, right) donne la zone de jeu; sinon on la
déduit de la zone transparente de l'image (décodeur PNG intégré; Pillow est utilisé s'il est installé).
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import logging
import struct
import zlib
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
    return any((Path(d) / TBP_SET / "systems" / f"{system}.png").is_file() for d in directories or decoration_dirs())


def find_image(set_name: str, system: str, directories=None) -> Path | None:
    """Bezel du système dans le jeu de décorations (``systems/<système>.png``), sinon ``default.png``."""
    for directory in directories or decoration_dirs():
        base = Path(directory) / set_name
        for candidate in (base / "systems" / f"{system}.png", base / "default.png"):
            if candidate.is_file():
                return candidate
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


def _png_alpha(image: Path) -> tuple[int, int, bytes] | None:
    """Plan alpha d'un PNG 8 bits RGBA ou gris+alpha, sans Pillow. Le défiltrage de chaque canal ne dépend que du même
    canal (octet à gauche, au-dessus): on ne traite donc que l'alpha. None si le format n'est pas pris en charge."""
    try:
        data = image.read_bytes()
    except OSError:
        return None
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    position, header, idat = 8, None, []
    while position + 8 <= len(data):
        length, kind = struct.unpack(">I4s", data[position:position + 8])
        body = data[position + 8:position + 8 + length]
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat.append(body)
        elif kind == b"IEND":
            break
        position += 12 + length
    if header is None:
        return None
    width, height, depth, color, _compression, _filter, interlace = header
    if depth != 8 or interlace != 0 or color not in (4, 6):
        return None
    channels = 4 if color == 6 else 2
    stride = width * channels
    try:
        raw = zlib.decompress(b"".join(idat))
    except zlib.error:
        return None
    if len(raw) < height * (stride + 1):
        return None
    rows = []
    previous = bytearray(width)
    for y in range(height):
        base = y * (stride + 1)
        kind = raw[base]
        line = raw[base + 1:base + 1 + stride][channels - 1::channels]  # alpha seul
        current = bytearray(width)
        if kind == 0:
            current[:] = line
        elif kind == 1:  # Sub
            left = 0
            for x in range(width):
                left = current[x] = (line[x] + left) & 255
        elif kind == 2:  # Up
            current[:] = bytes((line[x] + previous[x]) & 255 for x in range(width))
        elif kind == 3:  # Average
            left = 0
            for x in range(width):
                left = current[x] = (line[x] + ((left + previous[x]) >> 1)) & 255
        elif kind == 4:  # Paeth
            left = upper_left = 0
            for x in range(width):
                up = previous[x]
                p = left + up - upper_left
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - upper_left)
                predictor = left if pa <= pb and pa <= pc else (up if pb <= pc else upper_left)
                left = current[x] = (line[x] + predictor) & 255
                upper_left = up
        else:
            return None
        rows.append(bytes(current))
        previous = current
    return width, height, b"".join(rows)


def _alpha_plane(image: Path) -> tuple[int, int, bytes] | None:
    try:
        from PIL import Image
    except ImportError:
        return _png_alpha(image)
    try:
        with Image.open(image) as source:
            alpha = source.convert("RGBA").getchannel("A")
            return alpha.size[0], alpha.size[1], alpha.tobytes()
    except (OSError, ValueError) as exc:
        log.warning("bezel illisible %s: %s", image, exc)
        return None


def _scan(width: int, height: int, data: bytes) -> Area | None:
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


def _cache_file(image: Path) -> Path | None:
    try:
        stat = image.stat()
    except OSError:
        return None
    key = hashlib.sha1(f"{image}|{stat.st_size}|{stat.st_mtime_ns}".encode()).hexdigest()[:20]
    return paths.cache_dir() / "bezels" / f"{key}.json"


def detect_area(image: Path) -> Area | None:
    """Zone transparente autour du centre de l'image (lignes et colonnes médianes). Résultat mis en cache."""
    cache = _cache_file(image)
    if cache is not None and cache.is_file():
        try:
            values = json.loads(cache.read_text(encoding="utf-8"))
            return Area(*values) if values else None
        except (OSError, ValueError, TypeError):
            pass
    plane = _alpha_plane(image)
    if plane is None:
        log.warning("bezel %s: format PNG non pris en charge (8 bits RGBA attendu), zone de jeu non détectable", image.name)
        return None
    area = _scan(*plane)
    if cache is not None:
        try:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(list(dataclasses.astuple(area)) if area else []), encoding="utf-8")
        except OSError:
            pass
    return area


def game_area(image: Path) -> Area | None:
    return read_info(image) or detect_area(image)


@dataclasses.dataclass(frozen=True)
class Layout:
    """Placement du bezel sur l'écran: zone de jeu en pixels (x, y, largeur, hauteur) et rectangle de l'image
    (normalisé, 0-1) ou None quand l'image remplit tout l'écran."""
    box: tuple[int, int, int, int]
    rect: tuple[float, float, float, float] | None


def layout(area: Area, screen: tuple[int, int], stretch: bool = False, tolerance: float = 0.02) -> Layout:
    """Même ratio: l'image remplit l'écran. Ratio différent: l'image entière est centrée avec des bandes noires
    (proportions conservées), ou étirée sur tout l'écran avec l'option « stretch »."""
    screen_w, screen_h = screen
    scale_x, scale_y = screen_w / area.image_width, screen_h / area.image_height
    if stretch or abs(scale_x - scale_y) / max(scale_x, scale_y) <= tolerance:
        box = (round(area.x * scale_x), round(area.y * scale_y), round(area.width * scale_x), round(area.height * scale_y))
        return Layout(box, None)
    scale = min(scale_x, scale_y)
    draw_w, draw_h = area.image_width * scale, area.image_height * scale
    offset_x, offset_y = (screen_w - draw_w) / 2, (screen_h - draw_h) / 2
    box = (round(offset_x + area.x * scale), round(offset_y + area.y * scale), round(area.width * scale), round(area.height * scale))
    return Layout(box, (offset_x / screen_w, offset_y / screen_h, draw_w / screen_w, draw_h / screen_h))


def write_overlay(image: Path, target: Path, rect: tuple[float, float, float, float] | None = None) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = ["overlays = 1", f'overlay0_overlay = "{image}"']
    if rect is None:
        lines.append("overlay0_full_screen = true")
    else:
        lines += ["overlay0_normalized = true", "overlay0_full_screen = false",
                  'overlay0_rect = "' + ",".join(f"{value:.6f}" for value in rect) + '"']
    lines.append("overlay0_descs = 0")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target
