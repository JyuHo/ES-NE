# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur Dolphin (GameCube, Wii): ligne de commande de ``emulators.yml`` + réglages d'ES.

Valeurs et noms de clés alignés sur le générateur Dolphin de Batocera (même format de fichiers).
Chaque réglage n'est écrit que s'il est choisi dans ES (sinon Dolphin garde sa valeur) et seulement si le fichier existe
(Dolphin le crée à son premier lancement). Valeur inconnue: ignorée avec un avertissement.

* ``Dolphin.ini``: ``dolphin_backend`` (Vulkan, OGL), ``dolphin_cheats``, ``dolphin_dualcore``, ``dolphin_fastdisc``,
  ``dolphin_mmu``, ``dolphin_gc_language`` (langue de la GameCube).
* ``GFX.ini``: ``dolphin_resolution`` (1 à 8), ``dolphin_msaa`` (0, 2, 4, 8), ``dolphin_af`` (-1 à 4), ``dolphin_ratio``
  (0 auto, 1 16:9, 2 4:3, 3 étiré), ``dolphin_vsync``, ``dolphin_fps``, ``dolphin_widescreen`` (hack 16:9),
  ``dolphin_hires``, ``dolphin_shaders`` (ubershaders 0 à 3), ``dolphin_waitshaders``.
* ``SYSCONF`` (NAND de la Wii, binaire): ``dolphin_wii_language`` (0 à 9), ``dolphin_wii_tv`` (0 4:3, 1 16:9).
"""
from __future__ import annotations

import configparser
import logging
import os
import struct
from pathlib import Path

from .base import Command, Context
from .standalone import Standalone

log = logging.getLogger(__name__)

FLATPAK = "org.DolphinEmu.dolphin-emu"
BOOL = frozenset({"true", "false"})

# clé ES -> (fichier, section, clé, valeurs permises)
SETTINGS = {
    "dolphin_backend": ("Dolphin.ini", "Core", "GFXBackend", frozenset({"Vulkan", "OGL"})),
    "dolphin_cheats": ("Dolphin.ini", "Core", "EnableCheats", BOOL),
    "dolphin_dualcore": ("Dolphin.ini", "Core", "CPUThread", BOOL),
    "dolphin_fastdisc": ("Dolphin.ini", "Core", "FastDiscSpeed", BOOL),
    "dolphin_mmu": ("Dolphin.ini", "Core", "MMU", BOOL),
    "dolphin_gc_language": ("Dolphin.ini", "Core", "SelectedLanguage", frozenset(map(str, range(6)))),
    "dolphin_resolution": ("GFX.ini", "Settings", "InternalResolution", frozenset(map(str, range(1, 9)))),
    "dolphin_msaa": ("GFX.ini", "Settings", "MSAA", frozenset({"0", "2", "4", "8"})),
    "dolphin_af": ("GFX.ini", "Enhancements", "MaxAnisotropy", frozenset({"-1", "0", "1", "2", "3", "4"})),
    "dolphin_ratio": ("GFX.ini", "Settings", "AspectRatio", frozenset({"0", "1", "2", "3"})),
    "dolphin_vsync": ("GFX.ini", "Hardware", "VSync", BOOL),
    "dolphin_fps": ("GFX.ini", "Settings", "ShowFPS", BOOL),
    "dolphin_widescreen": ("GFX.ini", "Settings", "wideScreenHack", BOOL),
    "dolphin_hires": ("GFX.ini", "Settings", "HiresTextures", BOOL),
    "dolphin_shaders": ("GFX.ini", "Settings", "ShaderCompilationMode", frozenset({"0", "1", "2", "3"})),
    "dolphin_waitshaders": ("GFX.ini", "Settings", "WaitForShadersBeforeStarting", BOOL),
}
# Dolphin écrit les booléens en « True/False » (initiale majuscule)
BOOL_KEYS = {key for key, (_, _, _, allowed) in SETTINGS.items() if allowed is BOOL}

SYSCONF_LANGUAGE = frozenset(range(10))
SYSCONF_TV = frozenset({0, 1})


def _parser() -> configparser.RawConfigParser:
    parser = configparser.RawConfigParser(interpolation=None, delimiters=("=",), strict=False)
    parser.optionxform = str  # clés sensibles à la casse
    return parser


def config_dir(argv: list[str] | None = None) -> Path:
    if argv and any(FLATPAK in part for part in argv[:2]):
        return Path.home() / ".var/app" / FLATPAK / "config/dolphin-emu"
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "dolphin-emu"


def data_dir(argv: list[str] | None = None) -> Path:
    if argv and any(FLATPAK in part for part in argv[:2]):
        return Path.home() / ".var/app" / FLATPAK / "data/dolphin-emu"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share") / "dolphin-emu"


def chosen(ctx: Context) -> dict[str, dict[str, dict[str, str]]]:
    """{fichier: {section: {clé: valeur}}} des réglages choisis et valides."""
    result: dict[str, dict[str, dict[str, str]]] = {}
    for setting, (name, section, key, allowed) in SETTINGS.items():
        raw = str(ctx.setting(setting, "") or "").strip()
        if not raw:
            continue
        value = raw.lower() if allowed is BOOL else raw
        if value not in allowed:
            log.warning("valeur inconnue pour %s ignorée: %s", setting, raw)
            continue
        if setting in BOOL_KEYS:
            value = value.capitalize()
        result.setdefault(name, {}).setdefault(section, {})[key] = value
    return result


def update_ini(path: Path, sections: dict[str, dict[str, str]]) -> bool:
    if not path.is_file():
        return False
    parser = _parser()
    try:
        parser.read(path, encoding="utf-8")
    except (configparser.Error, OSError) as exc:
        log.warning("dolphin: %s illisible (%s), rien n'a été modifié", path.name, exc)
        return False
    for section, values in sections.items():
        if not parser.has_section(section):
            parser.add_section(section)
        for key, value in values.items():
            parser.set(section, key, value)
    temporary = path.with_suffix(".ini.esne-tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        parser.write(handle)
    temporary.replace(path)
    return True


def patch_sysconf(path: Path, values: dict[str, int]) -> bool:
    """Écrit des octets simples de la SYSCONF (format SCv0: entrées nommées, big-endian). False si rien n'a changé."""
    if not values or not path.is_file():
        return False
    try:
        data = bytearray(path.read_bytes())
        if data[:4] != b"SCv0":
            return False
        count = struct.unpack(">H", data[4:6])[0]
        pos = 6 + (count + 1) * 2
        wanted = dict(values)
        for _ in range(count):
            header = data[pos]
            kind = (header & 0xE0) >> 5
            length = (header & 0x1F) + 1
            name = bytes(data[pos + 1:pos + 1 + length]).decode("ascii", "replace")
            pos += 1 + length
            if kind == 3:
                if name in wanted:
                    data[pos] = wanted.pop(name)
                size = 1
            elif kind == 1:
                size = struct.unpack(">H", data[pos:pos + 2])[0] + 1 + 2
            elif kind == 2:
                size = data[pos] + 1 + 1
            elif kind == 4:
                size = 2
            elif kind == 5:
                size = 4
            elif kind == 6:
                size = 8
            elif kind == 7:
                size = 1
            else:
                return False
            pos += size
        if wanted:
            log.warning("dolphin: entrées SYSCONF introuvables: %s", ", ".join(wanted))
        temporary = path.with_name(path.name + ".esne-tmp")
        temporary.write_bytes(bytes(data))
        temporary.replace(path)
        return True
    except (OSError, IndexError, struct.error) as exc:
        log.warning("dolphin: SYSCONF non modifiée (%s)", exc)
        return False


def sysconf_values(ctx: Context) -> dict[str, int]:
    result: dict[str, int] = {}
    for setting, key, allowed in (("dolphin_wii_language", "IPL.LNG", SYSCONF_LANGUAGE), ("dolphin_wii_tv", "IPL.AR", SYSCONF_TV)):
        raw = str(ctx.setting(setting, "") or "").strip()
        if not raw:
            continue
        if not raw.isdigit() or int(raw) not in allowed:
            log.warning("valeur inconnue pour %s ignorée: %s", setting, raw)
            continue
        result[key] = int(raw)
    return result


class Dolphin(Standalone):
    name = "dolphin"

    def generate(self, ctx: Context) -> Command:
        command = super().generate(ctx)
        folder = config_dir(command.argv)
        for name, sections in chosen(ctx).items():
            if not update_ini(folder / name, sections):
                log.info("dolphin: %s introuvable, lance Dolphin une fois à la main pour le créer", name)
        values = sysconf_values(ctx)
        if values:
            patch_sysconf(data_dir(command.argv) / "Wii/shared2/sys/SYSCONF", values)
        return command


GENERATOR = Dolphin
