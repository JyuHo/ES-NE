# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur DuckStation (PS1): ligne de commande de ``emulators.yml`` + réglages et manettes dans ``settings.ini``.

Lancement: ``-batch`` (DuckStation se ferme avec le jeu), ``-fullscreen``, puis ``--`` et le chemin du jeu.

Réglages ES (``duckstation_*``), écrits dans ``settings.ini`` seulement quand ils sont choisis; le fichier n'est modifié que
s'il existe (DuckStation le crée à son premier lancement): moteur graphique, résolution interne, MSAA, filtrage des textures,
PGXP, hack écran large, format d'image, VSync, compteur d'images, son coupé, question et sauvegarde automatique à la fermeture
(``ConfirmPowerOff``, ``SaveStateOnExit``). Clés et valeurs relevées sur un ``settings.ini`` réel;
seuls le moteur « Automatic », le filtre « MMPXAdvanced » et le format « 16:9 » y figuraient: les autres noms (Vulkan, OpenGL,
Nearest, Bilinear, JINC2, xBR, 4:3) sont ceux de DuckStation, non revérifiés.

Manettes: ``Pad1``/``Pad2`` (``AnalogController``, entrées ``SDL-<index>/...`` comme dans le fichier réel). L'index est celui que
donne ES (SDL); sans manette pour le joueur 2, ``Pad2`` passe à ``Type = None``. Le multitap (3 à 8 joueurs) n'est pas géré.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from . import iniedit
from .base import Command, Context, Controller
from .standalone import Standalone

log = logging.getLogger(__name__)

MAX_PADS = 2

# clé ES -> (section, clé de settings.ini, valeurs permises)
SETTINGS: dict[str, tuple[str, str, frozenset[str]]] = {
    "duckstation_renderer": ("GPU", "Renderer", frozenset({"Automatic", "Vulkan", "OpenGL", "Software"})),
    "duckstation_resolution": ("GPU", "ResolutionScale", frozenset({"0", "1", "2", "3", "4", "5", "6", "8", "10", "12", "16"})),
    "duckstation_msaa": ("GPU", "Multisamples", frozenset({"1", "2", "4", "8"})),
    "duckstation_filter": ("GPU", "TextureFilter", frozenset({"Nearest", "Bilinear", "JINC2", "xBR", "MMPXAdvanced"})),
    "duckstation_pgxp": ("GPU", "PGXPEnable", frozenset({"0", "1"})),
    "duckstation_widescreen": ("GPU", "WidescreenHack", frozenset({"0", "1"})),
    "duckstation_aspect": ("Display", "AspectRatio", frozenset({"4:3", "16:9"})),
    "duckstation_vsync": ("Display", "VSync", frozenset({"0", "1"})),
    "duckstation_fps": ("Display", "ShowFPS", frozenset({"0", "1"})),
    "duckstation_mute": ("Audio", "OutputMuted", frozenset({"0", "1"})),
    "duckstation_confirm_exit": ("Main", "ConfirmPowerOff", frozenset({"0", "1"})),  # question à la fermeture
    "duckstation_save_on_exit": ("Main", "SaveStateOnExit", frozenset({"0", "1"})),  # sauvegarde automatique à la fermeture
}
BOOLEAN = {"duckstation_confirm_exit", "duckstation_save_on_exit", "duckstation_pgxp", "duckstation_widescreen", "duckstation_vsync", "duckstation_fps", "duckstation_mute"}

# bouton de la PS1 -> entrée SDL (relevé sur le fichier réel)
MAPPING = {
    "Analog": "Guide", "Circle": "B", "Cross": "A", "Square": "X", "Triangle": "Y",
    "Up": "DPadUp", "Down": "DPadDown", "Left": "DPadLeft", "Right": "DPadRight",
    "L1": "LeftShoulder", "R1": "RightShoulder", "L2": "+LeftTrigger", "R2": "+RightTrigger",
    "L3": "LeftStick", "R3": "RightStick", "Select": "Back", "Start": "Start",
    "LUp": "-LeftY", "LDown": "+LeftY", "LLeft": "-LeftX", "LRight": "+LeftX",
    "RUp": "-RightY", "RDown": "+RightY", "RLeft": "-RightX", "RRight": "+RightX",
    "LargeMotor": "LargeMotor", "SmallMotor": "SmallMotor",
}


def config_candidates(argv: list[str] | None = None) -> list[Path]:
    home = Path.home()
    data = Path(os.environ.get("XDG_DATA_HOME") or home / ".local/share")
    flatpak = home / ".var/app/org.duckstation.DuckStation/data/duckstation/settings.ini"
    if argv and any("flatpak" in part for part in argv[:2]):
        return [flatpak]
    return [data / "duckstation" / "settings.ini", flatpak]


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
    return sections


def pad_values(pad: Controller | None) -> dict[str, str]:
    if pad is None or pad.index is None:
        return {"Type": "None"}
    values = {"Type": "AnalogController"}
    values.update({button: f"SDL-{pad.index}/{source}" for button, source in MAPPING.items()})
    return values


def pad_sections(pads: list[Controller]) -> dict[str, dict[str, str]]:
    return {f"Pad{n + 1}": pad_values(pads[n] if n < len(pads) else None) for n in range(MAX_PADS)}


class Duckstation(Standalone):
    name = "duckstation"

    def generate(self, ctx: Context) -> Command:
        command = super().generate(ctx)
        values = chosen(ctx)
        pads = str(ctx.setting("duckstation_autoconfig", "1")) != "0" and bool(ctx.controllers)
        if pads:
            if len(ctx.controllers) > MAX_PADS:
                log.info("duckstation: %d manettes, seules les %d premières sont configurées (pas de multitap)", len(ctx.controllers), MAX_PADS)
            values.update(pad_sections(ctx.controllers))
        if values:
            ini = next((path for path in config_candidates(command.argv) if path.is_file()), None)
            if ini is None:
                log.info("duckstation: settings.ini introuvable, lance DuckStation une fois à la main pour le créer")
            elif iniedit.patch_ini(ini, values, spaced=True):
                shown = ", ".join(f"{k}={v}" for s, d in values.items() if not s.startswith("Pad") for k, v in d.items())
                log.info("duckstation: %s%s", shown or "réglages inchangés", f"; {min(len(ctx.controllers), MAX_PADS)} manette(s)" if pads else "")
        return command


GENERATOR = Duckstation
