# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur PCSX2 (PS2): ligne de commande de ``emulators.yml`` + manettes + réglages graphiques.

* Manettes: les sections ``[Pad1]``... de ``inis/PCSX2.ini`` sont réécrites (DualShock 2, source SDL). PCSX2 désigne une
  manette par son numéro SDL (``SDL-0``, ``SDL-1``...), le même que celui d'ES: aucun GUID à faire correspondre.
  ``pcsx2_autoconfig=0`` laisse tes propres réglages.
* Réglages (liste « features » d'ES): ``pcsx2_gfxbackend`` (vulkan, opengl, software), ``pcsx2_ratio``, ``pcsx2_resolution``,
  ``pcsx2_vsync``, ``pcsx2_fxaa``.
* Le fichier n'est modifié que s'il existe: PCSX2 le crée à son premier lancement (assistant, BIOS), à faire une fois à la main.

Noms de sections et de clés alignés sur ceux qu'écrit PCSX2 (vérifiés sur le générateur de Batocera, qui cible la même version).
"""
from __future__ import annotations

import configparser
import logging
import os
from pathlib import Path

from .. import paths
from .base import Command, Context, Controller
from .standalone import Standalone

log = logging.getLogger(__name__)

RENDERER = {"auto": "-1", "opengl": "12", "software": "13", "vulkan": "14"}  # GSRendererType
MAX_PLAYERS = 2  # sans multitap

# (clé PCSX2, entrée SDL de PCSX2)
PAD_MAPPING = [
    ("Up", "DPadUp"), ("Right", "DPadRight"), ("Down", "DPadDown"), ("Left", "DPadLeft"),
    ("Triangle", "FaceNorth"), ("Circle", "FaceEast"), ("Cross", "FaceSouth"), ("Square", "FaceWest"),
    ("Select", "Back"), ("Start", "Start"),
    ("L1", "LeftShoulder"), ("L2", "+LeftTrigger"), ("R1", "RightShoulder"), ("R2", "+RightTrigger"),
    ("L3", "LeftStick"), ("R3", "RightStick"),
    ("LUp", "-LeftY"), ("LRight", "+LeftX"), ("LDown", "+LeftY"), ("LLeft", "-LeftX"),
    ("RUp", "-RightY"), ("RRight", "+RightX"), ("RDown", "+RightY"), ("RLeft", "-RightX"),
    ("Analog", "Guide"), ("LargeMotor", "LargeMotor"), ("SmallMotor", "SmallMotor"),
]
PAD_DEFAULTS = {
    "Type": "DualShock2", "InvertL": "0", "InvertR": "0", "Deadzone": "0", "AxisScale": "1.33",
    "TriggerDeadzone": "0", "TriggerScale": "1", "LargeMotorScale": "1", "SmallMotorScale": "1",
    "ButtonDeadzone": "0", "PressureModifier": "0.5",
}


def config_dir(argv: list[str] | None = None) -> Path:
    if argv and any("flatpak" in part for part in argv[:2]):
        return Path.home() / ".var/app/net.pcsx2.PCSX2/config/PCSX2"
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "PCSX2"


def _parser() -> configparser.RawConfigParser:
    parser = configparser.RawConfigParser(interpolation=None, delimiters=("=",))
    parser.optionxform = str  # les clés de PCSX2 sont sensibles à la casse
    return parser


def apply_pads(parser: configparser.RawConfigParser, pads: list[Controller]) -> int:
    """Réécrit ``[Pad1]``, ``[Pad2]``; renvoie le nombre de manettes configurées."""
    for number in range(1, 9):
        parser.remove_section(f"Pad{number}")
    if not parser.has_section("InputSources"):
        parser.add_section("InputSources")
    parser.set("InputSources", "SDL", "true")
    done = 0
    for player, pad in enumerate(pads[:MAX_PLAYERS], start=1):
        index = pad.index if pad.index is not None else player - 1
        section = f"Pad{player}"
        parser.add_section(section)
        for key, value in PAD_DEFAULTS.items():
            parser.set(section, key, value)
        for key, name in PAD_MAPPING:
            parser.set(section, key, f"SDL-{index}/{name}")
        done += 1
    return done


def apply_settings(parser: configparser.RawConfigParser, ctx: Context) -> None:
    def section(name: str) -> str:
        if not parser.has_section(name):
            parser.add_section(name)
        return name

    ui = section("UI")
    parser.set(ui, "StartFullscreen", "true")
    parser.set(ui, "ConfirmShutdown", "false")
    parser.set(ui, "HideMouseCursor", "true")
    gs = section("EmuCore/GS")
    renderer = RENDERER.get(str(ctx.setting("pcsx2_gfxbackend", "") or "").lower())
    if renderer:
        parser.set(gs, "Renderer", renderer)
    for setting, key in (("pcsx2_ratio", "AspectRatio"), ("pcsx2_resolution", "upscale_multiplier"),
                         ("pcsx2_vsync", "VsyncEnable"), ("pcsx2_fxaa", "fxaa")):
        value = ctx.setting(setting, "")
        if value not in (None, ""):
            parser.set(gs, key, str(value))
    bios = paths.bios_dir() / "ps2"
    if bios.is_dir():  # le dossier de BIOS d'ES-NE, s'il existe
        parser.set(section("Folders"), "Bios", str(bios))


def configure(ini: Path, ctx: Context) -> bool:
    """Met ``PCSX2.ini`` à jour s'il existe. False si le fichier est absent ou illisible."""
    if not ini.is_file():
        return False
    parser = _parser()
    try:
        parser.read(ini, encoding="utf-8")
    except (configparser.Error, OSError) as exc:
        log.warning("pcsx2: PCSX2.ini illisible (%s), rien n'a été modifié", exc)
        return False
    apply_settings(parser, ctx)
    if str(ctx.setting("pcsx2_autoconfig", "1")) != "0":
        log.info("pcsx2: %d manette(s) configurée(s)", apply_pads(parser, ctx.controllers))
    temporary = ini.with_suffix(".ini.esne-tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        parser.write(handle)
    temporary.replace(ini)
    return True


class Pcsx2(Standalone):
    name = "pcsx2"

    def generate(self, ctx: Context) -> Command:
        command = super().generate(ctx)
        if not configure(config_dir(command.argv) / "inis" / "PCSX2.ini", ctx):
            log.info("pcsx2: PCSX2.ini introuvable, lance PCSX2 une fois à la main pour le créer")
        return command


GENERATOR = Pcsx2
