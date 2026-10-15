# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur Snes9x autonome (SNES): ligne de commande de ``emulators.yml`` + réglages dans ``snes9x.conf``.

Snes9x (AppImage 1.63, paquet ``snes9x-gtk`` ou Flatpak) démarre avec le chemin du jeu; ES-NE force ``FullscreenOnOpen``
pour le plein écran. Le fichier n'est modifié que s'il existe (Snes9x le crée à son premier lancement).

Réglages ES (``snes9x_*``), écrits seulement quand ils sont choisis: moteur graphique, format d'image, filtre bilinéaire,
VSync, effet haute résolution, lignes de balayage, compteur d'images, son coupé, rewind (Mo), suppression de la limite de
sprites, surcadençage du CPU. Clés et valeurs relevées sur un ``snes9x.conf`` réel (version 1.63).

Manettes: non gérées. Dans le fichier réel, tous les ``[Joypad N]`` sont ``Unset``: le format des liaisons n'a pas été
relevé, donc configure la manette une fois dans Snes9x (Préférences).
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from . import iniedit
from .base import Command, Context
from .standalone import Standalone

log = logging.getLogger(__name__)

# clé ES -> (section, clé de snes9x.conf, valeurs permises)
SETTINGS: dict[str, tuple[str, str, frozenset[str]]] = {
    "snes9x_renderer": ("Display", "HardwareAcceleration", frozenset({"none", "opengl", "vulkan"})),
    "snes9x_aspect": ("Display", "AspectRatio", frozenset({"0", "1", "2", "3", "4", "5"})),
    "snes9x_bilinear": ("Display", "BilinearFilter", frozenset({"0", "1"})),
    "snes9x_vsync": ("OpenGL", "VSync", frozenset({"0", "1"})),
    "snes9x_hires": ("Display", "HiresEffect", frozenset({"0", "1", "2"})),
    "snes9x_scanlines": ("Display", "ScanlineFilterIntensity", frozenset({"0", "1", "2", "3", "4"})),
    "snes9x_fps": ("Emulation", "DisplayFrameRate", frozenset({"0", "1"})),
    "snes9x_mute": ("Sound", "MuteSound", frozenset({"0", "1"})),
    "snes9x_rewind": ("Behavior", "RewindBufferSize", frozenset({"0", "10", "20", "50", "100", "200"})),
    "snes9x_sprites": ("Hacks", "RemoveSpriteLimit", frozenset({"0", "1"})),
    "snes9x_overclock": ("Hacks", "OverclockCPU", frozenset({"0", "1"})),
}
BOOLEAN = {"snes9x_bilinear", "snes9x_vsync", "snes9x_fps", "snes9x_mute", "snes9x_sprites", "snes9x_overclock"}


def config_candidates(argv: list[str] | None = None) -> list[Path]:
    home = Path.home()
    config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    flatpak = home / ".var/app/com.snes9x.Snes9x/config/snes9x/snes9x.conf"
    if argv and any("flatpak" in part for part in argv[:2]):
        return [flatpak]
    return [config / "snes9x" / "snes9x.conf", flatpak]


def chosen(ctx: Context) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    for name, (section, key, allowed) in SETTINGS.items():
        value = str(ctx.setting(name, "") or "").strip()
        if not value:
            continue
        if value not in allowed:
            log.warning("valeur inconnue pour %s ignorée: %s", name, value)
            continue
        sections.setdefault(section, {})[key] = ("true" if value == "1" else "false") if name in BOOLEAN else value
    sections.setdefault("Display", {})["FullscreenOnOpen"] = "true"
    return sections


class Snes9x(Standalone):
    name = "snes9x"

    def generate(self, ctx: Context) -> Command:
        command = super().generate(ctx)
        conf = next((path for path in config_candidates(command.argv) if path.is_file()), None)
        if conf is None:
            log.info("snes9x: snes9x.conf introuvable, lance Snes9x une fois à la main pour le créer")
        else:
            values = chosen(ctx)
            if iniedit.patch_ini(conf, values, spaced=True):
                log.info("snes9x: %s", ", ".join(f"{k}={v}" for d in values.values() for k, v in d.items()))
        return command


GENERATOR = Snes9x
