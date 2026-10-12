# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur Cemu (Wii U): ligne de commande de ``emulators.yml`` + profils de manette + API graphique.

* Manettes: pour chaque manette transmise par ES (``-p<N>guid``), ``controllerProfiles/controller<N-1>.xml`` est réécrit
  (type « Wii U Pro Controller », API ``SDLController``) avec la disposition Nintendo: A à droite, B en bas, X en haut, Y à gauche.
  ``cemu_autoconfig=0`` laisse tes propres profils intacts.
* ``cemu_api`` (``vulkan`` ou ``opengl``): écrit ``Graphic/api`` dans ``settings.xml`` s'il existe déjà (Cemu le crée à son
  premier lancement: lance-le une fois à la main pour son assistant de configuration, clés de la console et dossier MLC).

Format des fichiers lu dans le code de Cemu (``InputManager.cpp``, ``ProController.cpp``, ``Controller.h``).
"""
from __future__ import annotations

import logging
import os
import xml.etree.ElementTree as ET
from pathlib import Path

from .base import Command, Context, Controller
from .standalone import Standalone

log = logging.getLogger(__name__)

# Identifiants des boutons de la manette émulée (ProController::ButtonId)
A, B, X, Y, L, R, ZL, ZR, PLUS, MINUS, HOME = 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
UP, DOWN, LEFT, RIGHT, STICK_L, STICK_R = 12, 13, 14, 15, 16, 17
LSTICK_UP, LSTICK_DOWN, LSTICK_LEFT, LSTICK_RIGHT = 18, 19, 20, 21
RSTICK_UP, RSTICK_DOWN, RSTICK_LEFT, RSTICK_RIGHT = 22, 23, 24, 25

# Boutons de la manette physique SDL (Buttons2 de Cemu): 0-31 = boutons SDL, puis gâchettes, croix et axes
K_AXIS_XP, K_AXIS_YP, K_ROT_XP, K_ROT_YP, K_TRIG_XP, K_TRIG_YP = 38, 39, 40, 41, 42, 43
K_AXIS_XN, K_AXIS_YN, K_ROT_XN, K_ROT_YN = 44, 45, 46, 47

# (bouton émulé, bouton physique): disposition par défaut de Cemu pour une manette SDL (ProController::set_default_mapping)
SDL_PRO_MAPPING = [
    (A, 1), (B, 0), (X, 3), (Y, 2),
    (L, 9), (R, 10), (ZL, K_TRIG_XP), (ZR, K_TRIG_YP),
    (PLUS, 6), (MINUS, 4),
    (UP, 11), (DOWN, 12), (LEFT, 13), (RIGHT, 14),
    (STICK_L, 7), (STICK_R, 8),
    (LSTICK_UP, K_AXIS_YN), (LSTICK_DOWN, K_AXIS_YP), (LSTICK_LEFT, K_AXIS_XN), (LSTICK_RIGHT, K_AXIS_XP),
    (RSTICK_UP, K_ROT_YN), (RSTICK_DOWN, K_ROT_YP), (RSTICK_LEFT, K_ROT_XN), (RSTICK_RIGHT, K_ROT_XP),
]

GRAPHIC_API = {"opengl": "0", "vulkan": "1"}  # CemuConfig: GraphicAPI::kOpenGL = 0, kVulkan = 1
MAX_PLAYERS = 4


def config_dir(argv: list[str] | None = None) -> Path:
    """Dossier de configuration de Cemu (``settings.xml``, ``controllerProfiles``)."""
    if argv and any("flatpak" in part for part in argv[:2]):
        return Path.home() / ".var/app/info.cemu.Cemu/config/Cemu"
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "Cemu"


def pad_uuid(pads: list[Controller], position: int) -> str:
    """Identifiant SDL de Cemu: ``<n>_<guid>`` où n compte les manettes de même GUID qui précèdent."""
    guid = pads[position].guid
    return f"{sum(1 for pad in pads[:position] if pad.guid == guid)}_{guid}"


def profile_xml(pad: Controller, uuid: str) -> str:
    root = ET.Element("emulated_controller")
    ET.SubElement(root, "type").text = "Wii U Pro Controller"
    controller = ET.SubElement(root, "controller")
    ET.SubElement(controller, "api").text = "SDLController"
    ET.SubElement(controller, "uuid").text = uuid
    ET.SubElement(controller, "display_name").text = pad.name or "Controller"
    ET.SubElement(controller, "rumble").text = "0"
    for name in ("axis", "rotation", "trigger"):
        node = ET.SubElement(controller, name)
        ET.SubElement(node, "deadzone").text = "0.25"
        ET.SubElement(node, "range").text = "1"
    mappings = ET.SubElement(controller, "mappings")
    for emulated, physical in SDL_PRO_MAPPING:
        entry = ET.SubElement(mappings, "entry")
        ET.SubElement(entry, "mapping").text = str(emulated)
        ET.SubElement(entry, "button").text = str(physical)
    ET.indent(root)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def write_profiles(pads: list[Controller], config: Path) -> list[Path]:
    pads = [pad for pad in pads if pad.guid][:MAX_PLAYERS]
    written = []
    for position, pad in enumerate(pads):
        target = config / "controllerProfiles" / f"controller{position}.xml"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(profile_xml(pad, pad_uuid(pads, position)), encoding="utf-8")
        written.append(target)
    return written


def set_graphic_api(settings: Path, api: str) -> bool:
    """Met ``Graphic/api`` à jour dans un ``settings.xml`` existant. False si rien n'a été changé."""
    value = GRAPHIC_API.get(api.lower())
    if value is None or not settings.is_file():
        return False
    try:
        tree = ET.parse(settings)
    except (ET.ParseError, OSError) as exc:
        log.warning("cemu: settings.xml illisible (%s), API graphique inchangée", exc)
        return False
    root = tree.getroot()
    content = root if root.tag == "content" else root.find("content")
    if content is None:
        return False
    graphic = content.find("Graphic")
    if graphic is None:
        graphic = ET.SubElement(content, "Graphic")
    node = graphic.find("api")
    if node is None:
        node = ET.SubElement(graphic, "api")
    if node.text == value:
        return False
    node.text = value
    temporary = settings.with_suffix(".xml.esne-tmp")
    tree.write(temporary, encoding="utf-8", xml_declaration=True)
    temporary.replace(settings)
    return True


class Cemu(Standalone):
    name = "cemu"

    def generate(self, ctx: Context) -> Command:
        command = super().generate(ctx)
        config = config_dir(command.argv)
        if str(ctx.setting("cemu_autoconfig", "1")) != "0":
            for target in write_profiles(ctx.controllers, config):
                log.info("cemu: profil de manette %s", target)
        api = str(ctx.setting("cemu_api", "") or "")
        if api and set_graphic_api(config / "settings.xml", api):
            log.info("cemu: API graphique %s", api)
        return command


GENERATOR = Cemu
