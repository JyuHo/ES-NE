#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Diagnostic des bezels installés: zone de jeu détectée, centrage, placement en 16:9 et 16:10 (sans lancer de jeu)."""
from esne import bezels, paths
for image in sorted((paths.data_dir() / "decorations" / "thebezelproject" / "systems").glob("*.png")):
    area = bezels.game_area(image)
    if area is None:
        print(f"{image.stem:14} zone de jeu introuvable")
        continue
    cx = (area.x + area.width / 2) / area.image_width
    cy = (area.y + area.height / 2) / area.image_height
    row = f"{image.stem:12} image {area.image_width}x{area.image_height} jeu {area.width}x{area.height} ratio {area.width/area.height:.2f} centre {cx:.2f},{cy:.2f}"
    for screen in ((1920, 1080), (1920, 1200)):
        row += f" | {screen[0]}x{screen[1]}: {bezels.layout(area, screen)}"
    print(row)
