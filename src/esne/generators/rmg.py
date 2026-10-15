# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur RMG (Rosalie's Mupen GUI, N64): ligne de commande de ``emulators.yml`` + manettes + réglages vidéo.

Lancement: ``-f`` (plein écran), ``-n`` (sans barre de menus), ``-q`` (quitte RMG quand la partie se termine).

* Manettes: les profils ``[Rosalie's Mupen GUI - Input Plugin Profile N]`` de ``mupen64plus.cfg`` sont réécrits pour les manettes
  qu'ES transmet (4 joueurs au plus; les profils restants sont débranchés). Le mappage reprend les numéros de boutons et d'axes
  SDL (A en bas, B à gauche, boutons C sur le stick droit, L/R sur les gâchettes hautes, Z sur la gâchette gauche), relevés sur un
  profil réel. RMG retrouve la manette par son chemin evdev; si un profil existant désigne déjà ce chemin, son nom (celui que voit
  RMG, SDL3) est conservé, sinon on écrit le nom d'ES. ``rmg_autoconfig=0`` laisse tes propres profils.
* Vidéo (plugin GLideN64): ``GLideN64.ini``, section ``[User]``, quand le réglage ES est choisi: ``rmg_resolution``
  (``nativeResFactor``), ``rmg_msaa``, ``rmg_fxaa``, ``rmg_af``, ``rmg_filter``, ``rmg_vsync``, ``rmg_fps``, ``rmg_hires``,
  ``rmg_aspect`` (valeurs relevées sur un fichier réel: 16:9 = 2, résolution 6X = 6). Ces fichiers ne sont modifiés que s'ils existent (RMG les crée à son premier lancement).
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from . import iniedit
from .base import Command, Context, Controller
from .standalone import Standalone

log = logging.getLogger(__name__)

MAX_PLAYERS = 4
PROFILE = "Rosalie's Mupen GUI - Input Plugin Profile {}"

# (entrée N64, type 0 bouton / 1 axe, nom SDL, numéro SDL, sens pour un axe: 0 négatif, 1 positif)
MAPPING = [
    ("A", 0, "a", 0, 0), ("B", 0, "x", 2, 0), ("Start", 0, "start", 6, 0),
    ("DpadUp", 0, "dpup", 11, 0), ("DpadDown", 0, "dpdown", 12, 0), ("DpadLeft", 0, "dpleft", 13, 0), ("DpadRight", 0, "dpright", 14, 0),
    ("CButtonUp", 1, "righty-", 3, 0), ("CButtonDown", 1, "righty+", 3, 1),
    ("CButtonLeft", 1, "rightx-", 2, 0), ("CButtonRight", 1, "rightx+", 2, 1),
    ("LeftTrigger", 0, "leftshoulder", 9, 0), ("RightTrigger", 0, "rightshoulder", 10, 0), ("ZTrigger", 1, "lefttrigger+", 4, 1),
    ("AnalogStickUp", 1, "lefty-", 1, 0), ("AnalogStickDown", 1, "lefty+", 1, 1),
    ("AnalogStickLeft", 1, "leftx-", 0, 0), ("AnalogStickRight", 1, "leftx+", 0, 1),
]

# clé ES -> (clé de GLideN64.ini, valeurs permises)
VIDEO: dict[str, tuple[str, frozenset[str]]] = {
    "rmg_resolution": (r"frameBufferEmulation\nativeResFactor", frozenset(str(n) for n in range(0, 9))),  # 0 = taille de la fenêtre
    "rmg_msaa": (r"video\multisampling", frozenset({"0", "2", "4", "8"})),
    "rmg_fxaa": (r"video\fxaa", frozenset({"0", "1"})),
    "rmg_af": (r"texture\anisotropy", frozenset({"0", "2", "4", "8", "16"})),
    "rmg_filter": (r"texture\bilinearMode", frozenset({"0", "1"})),  # 0 standard, 1 à 3 points
    "rmg_vsync": (r"video\verticalSync", frozenset({"0", "1"})),
    "rmg_fps": (r"onScreenDisplay\showFPS", frozenset({"0", "1"})),
    "rmg_hires": (r"textureFilter\txHiresEnable", frozenset({"0", "1"})),
    "rmg_aspect": (r"frameBufferEmulation\aspect", frozenset({"0", "1", "2", "3"})),  # étiré, 4:3, 16:9 (2, relevé), ajusté
}


def config_dir(argv: list[str] | None = None) -> Path:
    if argv and any("flatpak" in part for part in argv[:2]):
        return Path.home() / ".var/app/com.github.Rosalie241.RMG/config/RMG"
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "RMG"


def video_values(ctx: Context) -> dict[str, str]:
    values: dict[str, str] = {}
    for name, (key, allowed) in VIDEO.items():
        value = str(ctx.setting(name, "") or "").strip()
        if not value:
            continue
        if value not in allowed:
            log.warning("valeur inconnue pour %s ignorée: %s", name, value)
            continue
        values[key] = value
    return values


def profile_values(pad: Controller | None, known_name: str = "") -> dict[str, str]:
    if pad is None:
        return {"PluggedIn": "False", "DeviceName": '"None"', "DeviceType": "0", "DevicePath": '""', "DeviceSerial": '""'}
    name = (known_name or pad.name or "Controller").replace('"', "'")
    values = {"PluggedIn": "True", "DeviceName": f'"{name}"', "DeviceType": "4", "DevicePath": f'"{pad.path}"'}
    for control, kind, label, number, extra in MAPPING:
        values[f"{control}_InputType"] = f'"{kind}"'
        values[f"{control}_Name"] = f'"{label}"'
        values[f"{control}_Data"] = f'"{number}"'
        values[f"{control}_ExtraData"] = f'"{extra}"'
    return values


def apply_pads(cfg: Path, pads: list[Controller]) -> int:
    """Réécrit les 4 profils d'entrée; renvoie le nombre de manettes configurées."""
    existing = {number: iniedit.read_section(cfg, PROFILE.format(number)) for number in range(MAX_PLAYERS)}
    sections: dict[str, dict[str, str]] = {}
    done = 0
    for number in range(MAX_PLAYERS):
        pad = pads[number] if number < len(pads) else None
        known = ""
        if pad is not None and pad.path:
            known = next((old["DeviceName"] for old in existing.values() if old.get("DevicePath") == pad.path and old.get("DeviceName")), "")
            done += 1
        elif pad is not None:
            pad = None  # sans chemin evdev, RMG ne pourrait pas retrouver la manette
        sections[PROFILE.format(number)] = profile_values(pad, known)
    iniedit.patch_ini(cfg, sections, spaced=True)
    return done


class Rmg(Standalone):
    name = "rmg"

    def generate(self, ctx: Context) -> Command:
        command = super().generate(ctx)
        folder = config_dir(command.argv)
        video = video_values(ctx)
        if video:
            ini = folder / "GLideN64.ini"
            if not ini.is_file():
                log.info("rmg: GLideN64.ini introuvable, lance RMG une fois à la main pour le créer")
            elif iniedit.patch_ini(ini, {"User": video}):
                log.info("rmg: réglages vidéo %s", ", ".join(f"{k}={v}" for k, v in video.items()))
        if str(ctx.setting("rmg_autoconfig", "1")) != "0" and ctx.controllers:
            cfg = folder / "mupen64plus.cfg"
            if cfg.is_file():
                log.info("rmg: %d manette(s) configurée(s)", apply_pads(cfg, ctx.controllers))
            else:
                log.info("rmg: mupen64plus.cfg introuvable, lance RMG une fois à la main pour le créer")
        return command


GENERATOR = Rmg
