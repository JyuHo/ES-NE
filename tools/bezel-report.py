#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Diagnostic des bezels installés: zone de jeu détectée, centrage, placement en 16:9 et 16:10 (sans lancer de jeu).

Un bezel de système par ligne, puis pour chaque système un résumé des bezels de jeu téléchargés (``games/<système>/``) et
la liste de ceux dont la zone de jeu est décentrée (écart > 0,03), de ratio inhabituel ou introuvable.
Option ``-v``: une ligne par bezel de jeu.
"""
import sys

from esne import bezels, paths

SCREENS = ((1920, 1080), (1920, 1200))
OFF_CENTRE = 0.03


def describe(image, name):
    area = bezels.game_area(image)
    if area is None:
        return None, f"{name:44} zone de jeu introuvable"
    cx = (area.x + area.width / 2) / area.image_width
    cy = (area.y + area.height / 2) / area.image_height
    row = f"{name:44} image {area.image_width}x{area.image_height} jeu {area.width}x{area.height} ratio {area.width / area.height:.2f} centre {cx:.2f},{cy:.2f}"
    for screen in SCREENS:
        row += f" | {screen[0]}x{screen[1]}: {bezels.layout(area, screen)}"
    return (area, cx, cy), row


def main(verbose):
    root = paths.data_dir() / "decorations" / bezels.TBP_SET
    for image in sorted((root / "systems").glob("*.png")):
        print(describe(image, image.stem)[1])
    for folder in sorted((root / "games").glob("*")):
        images = sorted(folder.glob("*.png"))
        problems = []
        ratios = {}
        for image in images:
            info, row = describe(image, f"{image.stem[:44]}")
            if info is None:
                problems.append(row)
                continue
            area, cx, cy = info
            ratios[round(area.width / area.height, 2)] = ratios.get(round(area.width / area.height, 2), 0) + 1
            if abs(cx - 0.5) > OFF_CENTRE or abs(cy - 0.5) > OFF_CENTRE:
                problems.append(row)
            if verbose:
                print(f"  {row}")
        common = ", ".join(f"{ratio} ({count})" for ratio, count in sorted(ratios.items(), key=lambda item: -item[1])[:4])
        print(f"\n{folder.name}: {len(images)} bezels de jeu; ratios de la zone de jeu: {common or '-'}")
        for row in problems:
            print(f"  à voir: {row}")


if __name__ == "__main__":
    main("-v" in sys.argv[1:])
