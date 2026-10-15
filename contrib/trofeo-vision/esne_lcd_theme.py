#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Thème ES-NE pour l'écran Thermalright Trofeo Vision 6,86" (1280x480), avec trcc-linux.

    esne_lcd_theme.py build              dessine le fond (PNG) dans ~/.trcc-user/esne-lcd/
    esne_lcd_theme.py apply              pose le fond et les éléments CPU/GPU dans les réglages de trcc (trcc fermé)
    esne_lcd_theme.py restore            remet les réglages d'avant

Le fond contient tout ce qui est fixe (cadres, titres, légendes, logo); trcc-linux ajoute par-dessus les valeurs vivantes
(température, utilisation, fréquence du CPU et du GPU) à partir de ses capteurs, comme dans ton thème actuel.
Dépendance: Pillow (``pacman -S python-pillow``).
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

WIDTH, HEIGHT = 1280, 480
DEVICE = "0416:5302"
SETTINGS = Path.home() / ".trcc" / "trcc.json"
OUT_DIR = Path.home() / ".trcc-user" / "esne-lcd"
BACKUP = SETTINGS.with_name("trcc.json.esne-bak")
LOGO = Path(__file__).resolve().parents[2] / "assets" / "es-ne-logo.png"

# palette ES-NE (logo)
INK, PANEL, WHITE, CYAN, VIOLET = (11, 14, 34), (26, 31, 61), (244, 247, 255), (39, 227, 255), (176, 92, 255)
MUTED = (140, 150, 190)

# (clé du capteur, format, x relatif au panneau, y, taille, couleur)
PANELS = {
    "CPU": {"x": 40, "accent": CYAN, "temp": "cpu:temp", "usage": "cpu:usage", "clock": "cpu:freq"},
    "GPU": {"x": 680, "accent": VIOLET, "temp": "gpu:primary:temp", "usage": "gpu:primary:usage", "clock": "gpu:primary:clock"},
}
PANEL_W, PANEL_Y, PANEL_H = 560, 105, 345


def layout(font: str = "DejaVu Sans", anchor: str = "left", measure=None) -> list[dict]:
    """Éléments de texte (au format de ``user_overlay_elements`` de trcc) posés sur le fond."""
    def width(text: str, size: int) -> int:
        return measure(text, size) if (anchor == "center" and measure) else 0

    elements = []
    for name, panel in PANELS.items():
        x0 = panel["x"]
        spec = [
            (panel["temp"], "{value:.0f}°C", x0 + 40, 222, 88, "#ffffff", "88°C"),
            (panel["usage"], "{value:.0f}%", x0 + 40, 378, 44, "#ffffff", "100%"),
            (panel["clock"], "{value:.0f} MHz", x0 + 270, 378, 44, "#ffffff", "3500 MHz"),
        ]
        for sensor, fmt, x, y, size, color, sample in spec:
            elements.append({
                "id": f"esne_{sensor.replace(':', '_')}", "type": "metric",
                "x": x - width(sample, size) // 2, "y": y, "color": color, "size": size, "bold": True, "italic": False,
                "font": font, "text": "", "metric": sensor, "format": fmt, "show_unit": True, "source": "time",
            })
    return elements


def draw_background(logo: Path | None = LOGO):
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (WIDTH, HEIGHT), INK)
    pixels = ImageDraw.Draw(image)
    for y in range(HEIGHT):  # léger dégradé vertical
        t = y / HEIGHT
        pixels.line([(0, y), (WIDTH, y)], fill=tuple(int(INK[i] + (PANEL[i] - INK[i]) * 0.35 * t) for i in range(3)))

    def font(size: int, bold: bool = True):
        for candidate in ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", "DejaVuSans.ttf"):
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
        return ImageFont.load_default()

    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    layer = ImageDraw.Draw(glow)
    draw = ImageDraw.Draw(image)
    for name, panel in PANELS.items():
        box = (panel["x"], PANEL_Y, panel["x"] + PANEL_W, PANEL_Y + PANEL_H)
        layer.rounded_rectangle(box, 28, outline=panel["accent"] + (110,), width=10)
    from PIL import ImageFilter
    image.paste(glow.filter(ImageFilter.GaussianBlur(8)), (0, 0), glow.filter(ImageFilter.GaussianBlur(8)))
    for name, panel in PANELS.items():
        x0 = panel["x"]
        box = (x0, PANEL_Y, x0 + PANEL_W, PANEL_Y + PANEL_H)
        draw.rounded_rectangle(box, 28, fill=PANEL, outline=panel["accent"], width=3)
        draw.text((x0 + 40, PANEL_Y + 18), name, font=font(44), fill=panel["accent"])
        draw.line([(x0 + 40, PANEL_Y + 78), (x0 + PANEL_W - 40, PANEL_Y + 78)], fill=panel["accent"], width=2)
        draw.text((x0 + 40, 192), "TEMP", font=font(22, False), fill=MUTED)
        draw.text((x0 + 40, 348), "USAGE", font=font(22, False), fill=MUTED)
        draw.text((x0 + 270, 348), "CLOCK", font=font(22, False), fill=MUTED)

    if logo and Path(logo).is_file():  # logo ES-NE au centre, entre les deux panneaux et en haut
        mark = Image.open(logo).convert("RGBA")
        height = 70
        mark = mark.resize((round(mark.width * height / mark.height), height), Image.LANCZOS)
        image.paste(mark, ((WIDTH - mark.width) // 2, 18), mark)
    return image


def measure(text: str, size: int) -> int:
    from PIL import ImageFont
    try:
        return round(ImageFont.truetype("DejaVuSans-Bold.ttf", size).getlength(text))
    except OSError:
        return len(text) * size // 2


def trcc_running() -> bool:
    return subprocess.run(["pgrep", "-f", r"bin/trcc|trcc\.cli|trcc gui|trcc-linux"], capture_output=True).returncode == 0


def apply_settings(data: dict, background: Path, elements: list[dict], device: str = DEVICE) -> dict:
    """Réglages de trcc avec le fond et les éléments ES-NE pour ``device`` (le reste est conservé)."""
    devices = data.setdefault("devices", {})
    if device not in devices:
        raise KeyError(f"écran {device} absent des réglages de trcc: lance trcc une fois avec l'écran branché")
    entry = devices[device]
    entry.update({
        "background_path": str(background), "mask_visible": False, "overlay_enabled": True,
        "user_overlay_elements": elements,
    })
    return data


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["build", "apply", "restore"])
    parser.add_argument("--font", default="DejaVu Sans", help="nom de la police des valeurs (installée sur le système)")
    parser.add_argument("--anchor", choices=["left", "center"], default="left",
                        help="repère des éléments de trcc: coin haut-gauche (défaut) ou centre du texte")
    parser.add_argument("--force", action="store_true", help="ne pas vérifier que trcc est fermé")
    options = parser.parse_args(argv)

    if options.action == "restore":
        if not BACKUP.is_file():
            print("aucune sauvegarde à restaurer", file=sys.stderr)
            return 1
        if not options.force and trcc_running():
            print("ferme trcc (menu de la zone de notification) avant de restaurer", file=sys.stderr)
            return 1
        shutil.copy2(BACKUP, SETTINGS)
        print(f"réglages restaurés depuis {BACKUP}")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    background = OUT_DIR / "background-1280x480.png"
    draw_background().save(background)
    print(f"fond écrit: {background}")
    if options.action == "build":
        return 0

    if not options.force and trcc_running():
        print("ferme trcc (menu de la zone de notification) avant `apply`: il réécrirait ses réglages en quittant", file=sys.stderr)
        return 1
    if not SETTINGS.is_file():
        print(f"{SETTINGS} introuvable: lance trcc une fois avec l'écran branché", file=sys.stderr)
        return 1
    if not BACKUP.is_file():
        shutil.copy2(SETTINGS, BACKUP)
    data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    try:
        apply_settings(data, background, layout(options.font, options.anchor, measure))
    except KeyError as exc:
        print(exc.args[0], file=sys.stderr)
        return 1
    temporary = SETTINGS.with_name(SETTINGS.name + ".esne-tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(SETTINGS)
    print(f"thème appliqué dans {SETTINGS} (sauvegarde: {BACKUP}); relance trcc")
    return 0


if __name__ == "__main__":
    sys.exit(main())
