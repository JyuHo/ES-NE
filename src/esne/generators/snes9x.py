# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur Snes9x autonome (SNES): ligne de commande de ``emulators.yml`` + réglages dans ``snes9x.conf``.

Snes9x (AppImage 1.63, paquet ``snes9x-gtk`` ou Flatpak) démarre avec le chemin du jeu; ES-NE force ``FullscreenOnOpen``
pour le plein écran. Le fichier n'est modifié que s'il existe (Snes9x le crée à son premier lancement).

Réglages ES (``snes9x_*``), écrits seulement quand ils sont choisis: moteur graphique, format d'image, filtre bilinéaire,
VSync, effet haute résolution, lignes de balayage, compteur d'images, son coupé, rewind (Mo), suppression de la limite de
sprites, surcadençage du CPU. Clés et valeurs relevées sur un ``snes9x.conf`` réel (version 1.63).

Manettes: Snes9x enregistre ``Bouton = Joystick <n> Button <b>`` ou ``Joystick <n> Axis <a> +/- 40%`` (``n`` commence à 1,
``n = index SDL + 1``). Les numéros dépendent du modèle: ES-NE a un profil intégré pour les manettes Sony (relevé sur une
PS4); pour un autre modèle il recopie le mappage fait une fois dans Snes9x pour le joueur 1 (``[Joypad 0]`` complet).
Option ``AUTOCONFIGURE CONTROLLERS`` pour garder son propre mappage.
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path

from . import evdev, iniedit
from .base import Command, Context, Controller
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


MAX_PADS = 5  # 5 manettes: le jeu de Snes9x au multitap
BUTTONS = ("A", "B", "X", "Y", "L", "R", "Select", "Start", "Up", "Down", "Left", "Right")
_JOYSTICK = re.compile(r"^Joystick \d+ ")


def template(path: Path) -> dict[str, str] | None:
    """Liaisons du joueur 1 (``[Joypad 0]``) faites dans Snes9x, sans le numéro de manette; None si incomplètes."""
    section = iniedit.read_section(path, "Joypad 0")
    binding = {}
    for button in BUTTONS:
        value = section.get(button, "")
        if not _JOYSTICK.match(value):
            return None
        binding[button] = _JOYSTICK.sub("", value)
    return binding


# Manettes Sony (PS4 « Wireless Controller », relevé sur un snes9x.conf réel; DualSense a les mêmes numéros, non vérifié):
# disposition SNES (A à droite = rond, B en bas = croix), croix directionnelle vue comme les axes 6 et 7.
SONY = {
    "A": "Button 1", "B": "Button 0", "X": "Button 3", "Y": "Button 2", "L": "Button 4", "R": "Button 5",
    "Select": "Button 8", "Start": "Button 9",
    "Up": "Axis 6 + 40%", "Down": "Axis 6 - 40%", "Left": "Axis 7 - 40%", "Right": "Axis 7 + 40%",
}
SONY_VENDOR = 0x054C


def builtin(pad: Controller) -> dict[str, str] | None:
    ids = evdev.guid_ids(pad.guid)
    sony = (ids is not None and ids[0] == SONY_VENDOR) or any(word in pad.name.lower() for word in ("wireless controller", "dualshock", "dualsense", "playstation"))
    return SONY if sony else None


def pad_sections(binding: dict[str, str] | None, pads: list[Controller]) -> dict[str, dict[str, str]]:
    """Profil intégré du modèle de chaque manette; à défaut, ``binding`` (mappage fait dans Snes9x pour le joueur 1)."""
    sections = {}
    for n, pad in enumerate(pads[:MAX_PADS]):
        own = builtin(pad) or binding
        if pad.index is None or own is None:
            log.info("snes9x: modèle de manette inconnu (%s), configure-la dans Snes9x", pad.name or pad.guid)
            continue
        sections[f"Joypad {n}"] = {button: f"Joystick {pad.index + 1} {value}" for button, value in own.items()}
    return sections


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
            shown = ", ".join(f"{k}={v}" for d in values.values() for k, v in d.items())
            if str(ctx.setting("snes9x_autoconfig", "1")) != "0" and ctx.controllers:
                pads = pad_sections(template(conf), ctx.controllers)
                values.update(pads)
                shown += f"; {len(pads)} manette(s)"
            if iniedit.patch_ini(conf, values, spaced=True):
                log.info("snes9x: %s", shown)
        return command


GENERATOR = Snes9x
