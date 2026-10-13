# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur RPCS3 (PS3): ligne de commande de ``emulators.yml`` + manettes + réglages vidéo.

* Manettes: ``input_configs/global/Default.yml`` est réécrit (gestionnaire SDL, une entrée par manette ES: appareil
  ``<nom SDL> <n>``, ``n`` comptant les manettes de même nom). ``rpcs3_autoconfig=0`` laisse tes propres réglages.
* Réglages (liste « features » d'ES): ``rpcs3_gfxbackend`` (Vulkan, OpenGL), ``rpcs3_resolution_scale``, ``rpcs3_ratio``,
  ``rpcs3_vsync``, écrits dans ``config.yml`` (section Video) s'il existe déjà.
* Un jeu au format dossier (``Nom.ps3``) est lancé par son ``PS3_GAME/USRDIR/EBOOT.BIN``.
* RPCS3 doit avoir été lancé une fois à la main (installation du firmware, création de la configuration): le dossier de
  configuration n'est pas créé ici.

Noms de sections, de clés et valeurs relevés dans le générateur RPCS3 de Batocera (même version de RPCS3).
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

from .base import Command, Context, Controller
from .standalone import Standalone

log = logging.getLogger(__name__)

MAX_PLAYERS = 7
BACKENDS = {"vulkan": "Vulkan", "opengl": "OpenGL"}

# Réglages de la manette pour le gestionnaire SDL, dans l'ordre où RPCS3 les écrit.
SDL_CONFIG: dict[str, Any] = {
    "Left Stick Left": "LS X-", "Left Stick Down": "LS Y-", "Left Stick Right": "LS X+", "Left Stick Up": "LS Y+",
    "Right Stick Left": "RS X-", "Right Stick Down": "RS Y-", "Right Stick Right": "RS X+", "Right Stick Up": "RS Y+",
    "Start": "Start", "Select": "Back", "PS Button": "Guide",
    "Square": "West", "Cross": "South", "Circle": "East", "Triangle": "North",
    "Left": "Left", "Down": "Down", "Right": "Right", "Up": "Up",
    "R1": "RB", "R2": "RT", "R3": "RS", "L1": "LB", "L2": "LT", "L3": "LS",
    "IR Nose": "", "IR Tail": "", "IR Left": "", "IR Right": "", "Tilt Left": "", "Tilt Right": "",
    "Motion Sensor X": {"Axis": "X", "Mirrored": False, "Shift": 0},
    "Motion Sensor Y": {"Axis": "Y", "Mirrored": False, "Shift": 0},
    "Motion Sensor Z": {"Axis": "Z", "Mirrored": False, "Shift": 0},
    "Motion Sensor G": {"Axis": "RY", "Mirrored": False, "Shift": 0},
    "Orientation Reset Button": "", "Orientation Enabled": False,
    "Pressure Intensity Button": "", "Pressure Intensity Percent": 50, "Pressure Intensity Toggle Mode": False,
    "Pressure Intensity Deadzone": 0, "Analog Limiter Button": "", "Analog Limiter Toggle Mode": False,
    "Left Stick Multiplier": 100, "Right Stick Multiplier": 100,
    "Left Stick Deadzone": 8000, "Right Stick Deadzone": 8000,
    "Left Stick Anti-Deadzone": 4259, "Right Stick Anti-Deadzone": 4259,
    "Left Trigger Threshold": 0, "Right Trigger Threshold": 0,
    "Left Pad Squircling Factor": 8000, "Right Pad Squircling Factor": 8000,
    "Color Value R": 0, "Color Value G": 0, "Color Value B": 20,
    "Blink LED when battery is below 20%": True, "Use LED as a battery indicator": False,
    "LED battery indicator brightness": 10, "Player LED enabled": True,
    "Large Vibration Motor Multiplier": 100, "Small Vibration Motor Multiplier": 100, "Switch Vibration Motors": False,
    "Mouse Movement Mode": "Relative", "Mouse Deadzone X Axis": 60, "Mouse Deadzone Y Axis": 60,
    "Mouse Acceleration X Axis": 200, "Mouse Acceleration Y Axis": 250,
    "Left Stick Lerp Factor": 100, "Right Stick Lerp Factor": 100, "Analog Button Lerp Factor": 100,
    "Trigger Lerp Factor": 100, "Device Class Type": 0, "Vendor ID": 1356, "Product ID": 616,
}


def config_dir(argv: list[str] | None = None) -> Path:
    if argv and any("flatpak" in part for part in argv[:2]):
        return Path.home() / ".var/app/net.rpcs3.RPCS3/config/rpcs3"
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "rpcs3"


def controllers_config(pads: list[Controller]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    result: dict[str, Any] = {}
    for player, pad in enumerate(pads[:MAX_PLAYERS], start=1):
        name = (pad.name or "Controller").replace(",", ".")  # RPCS3 n'aime pas les virgules dans le nom
        counts[name] = counts.get(name, 0) + 1
        result[f"Player {player} Input"] = {
            "Handler": "SDL", "Device": f"{name} {counts[name]}", "Config": dict(SDL_CONFIG), "Buddy Device": "",
        }
    return result


def write_controllers(config: Path, pads: list[Controller]) -> Path | None:
    if not pads:
        return None
    target = config / "input_configs" / "global" / "Default.yml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(controllers_config(pads), sort_keys=False, width=1000, allow_unicode=True),
                      encoding="utf-8")
    return target


def apply_video(config_file: Path, ctx: Context) -> bool:
    """Met à jour la section Video de ``config.yml`` s'il existe et qu'un réglage est défini."""
    wanted: dict[str, str] = {}
    backend = BACKENDS.get(str(ctx.setting("rpcs3_gfxbackend", "") or "").lower())
    if backend:
        wanted["Renderer"] = backend
    for setting, key in (("rpcs3_ratio", "Aspect ratio"), ("rpcs3_vsync", "VSync Mode")):
        value = ctx.setting(setting, "")
        if value not in (None, ""):
            wanted[key] = str(value)
    scale = ctx.setting("rpcs3_resolution_scale", "")
    if scale not in (None, ""):
        wanted["Resolution Scale"] = int(scale) if str(scale).isdigit() else scale
    if not wanted or not config_file.is_file():
        return False
    try:
        data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
    except (yaml.YAMLError, OSError) as exc:
        log.warning("rpcs3: config.yml illisible (%s), réglages vidéo inchangés", exc)
        return False
    video = data.setdefault("Video", {})
    if all(video.get(k) == v for k, v in wanted.items()):
        return False
    video.update(wanted)
    temporary = config_file.with_suffix(".yml.esne-tmp")
    temporary.write_text(yaml.safe_dump(data, sort_keys=False, width=1000, allow_unicode=True), encoding="utf-8")
    temporary.replace(config_file)
    return True


def game_target(rom: str) -> str:
    """Un dossier de jeu (``Nom.ps3``) se lance par son EBOOT.BIN."""
    path = Path(rom)
    eboot = path / "PS3_GAME" / "USRDIR" / "EBOOT.BIN"
    return str(eboot) if path.is_dir() and eboot.is_file() else rom


class Rpcs3(Standalone):
    name = "rpcs3"

    def generate(self, ctx: Context) -> Command:
        command = super().generate(ctx)
        if command.argv and command.argv[-1] == ctx.rom:
            command.argv[-1] = game_target(ctx.rom)
        config = config_dir(command.argv)
        if not config.is_dir():
            log.info("rpcs3: %s absent, lance RPCS3 une fois à la main (firmware, configuration)", config)
            return command
        if str(ctx.setting("rpcs3_autoconfig", "1")) != "0":
            target = write_controllers(config, ctx.controllers)
            if target:
                log.info("rpcs3: manettes écrites dans %s", target)
        if apply_video(config / "config.yml", ctx):
            log.info("rpcs3: réglages vidéo appliqués")
        return command


GENERATOR = Rpcs3
