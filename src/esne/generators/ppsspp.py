# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur PPSSPP (PSP): ligne de commande de ``emulators.yml`` + réglages choisis dans ES dans ``ppsspp.ini``.

Lancement en plein écran (``--fullscreen``); ``--pause-menu-exit`` remplace « retour au menu » par « quitter » dans le menu pause.
Manettes: PPSSPP reconnaît seul les manettes SDL (mappage par défaut de ``controls.ini``), rien à écrire.

Réglages ES (``ppsspp_*``), écrits dans ``ppsspp.ini`` seulement quand ils sont choisis (un réglage non choisi garde la valeur de
PPSSPP; le fichier n'est modifié que s'il existe, PPSSPP le crée à son premier lancement): moteur graphique, résolution
interne, filtrage anisotrope, filtrage des textures, VSync, saut d'images, son coupé, langue de la console.
Clés relevées sur un ``ppsspp.ini`` réel (PPSSPP 1.20.4); le moteur OpenGL (« 1 (OPENGL) ») et les langues autres que le
français suivent l'ordre du système de la PSP, non vérifiés dans le fichier.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from . import iniedit
from .base import Command, Context
from .standalone import Standalone

log = logging.getLogger(__name__)

# clé ES -> (section, clé de ppsspp.ini, {valeur ES: valeur écrite})
SETTINGS: dict[str, tuple[str, str, dict[str, str]]] = {
    "ppsspp_backend": ("Graphics", "GraphicsBackend", {"vulkan": "3 (VULKAN)", "opengl": "1 (OPENGL)"}),
    "ppsspp_resolution": ("Graphics", "InternalResolution", {str(n): str(n) for n in range(0, 11)}),  # 0 auto, 1 = 1x...
    "ppsspp_af": ("Graphics", "AnisotropyLevel", {str(n): str(n) for n in range(0, 5)}),  # 0 off, 1 = 2x ... 4 = 16x
    "ppsspp_filter": ("Graphics", "TextureFiltering", {"1": "1", "2": "2", "3": "3", "4": "4"}),  # auto, nearest, linear, auto max
    "ppsspp_vsync": ("Graphics", "VerticalSync", {"0": "False", "1": "True"}),
    "ppsspp_mute": ("Sound", "Enable", {"0": "True", "1": "False"}),  # la clé dit « son activé »
    "ppsspp_language": ("SystemParam", "GameLanguage", {str(n): str(n) for n in range(0, 12)}),
}


def config_candidates(argv: list[str] | None = None) -> list[Path]:
    home = Path.home()
    config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    flatpak = home / ".var/app/org.ppsspp.PPSSPP/config/ppsspp/PSP/SYSTEM/ppsspp.ini"
    if argv and any("flatpak" in part for part in argv[:2]):
        return [flatpak]
    return [config / "ppsspp" / "PSP" / "SYSTEM" / "ppsspp.ini", flatpak]


def chosen(ctx: Context) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    for name, (section, key, allowed) in SETTINGS.items():
        value = str(ctx.setting(name, "") or "").strip().lower()
        if not value:
            continue
        if value not in allowed:
            log.warning("valeur inconnue pour %s ignorée: %s", name, value)
            continue
        sections.setdefault(section, {})[key] = allowed[value]
    skip = str(ctx.setting("ppsspp_frameskip", "") or "").strip().lower()
    if skip in ("0", "auto"):
        graphics = sections.setdefault("Graphics", {})
        graphics["FrameSkip"] = "0"
        graphics["AutoFrameSkip"] = "True" if skip == "auto" else "False"
    elif skip:
        log.warning("valeur inconnue pour ppsspp_frameskip ignorée: %s", skip)
    return sections


class Ppsspp(Standalone):
    name = "ppsspp"

    def generate(self, ctx: Context) -> Command:
        command = super().generate(ctx)
        values = chosen(ctx)
        if values:
            ini = next((path for path in config_candidates(command.argv) if path.is_file()), None)
            if ini is None:
                log.info("ppsspp: ppsspp.ini introuvable, lance PPSSPP une fois à la main pour le créer")
            elif iniedit.patch_ini(ini, values, spaced=True):
                log.info("ppsspp: réglages %s", ", ".join(f"{k}={v}" for s in values.values() for k, v in s.items()))
        return command


GENERATOR = Ppsspp
