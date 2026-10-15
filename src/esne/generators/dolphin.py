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
* ``GCPadNew.ini`` (GameCube seulement): ``dolphin_gc_pad`` = ``sdl`` mappe jusqu'à 4 manettes SDL sur les ports 1 à 4
  (et règle ``SIDevice`` de ``Dolphin.ini``). Sans ce réglage les fichiers ne sont pas touchés.
* ``WiimoteNew.ini`` (Wii seulement): ``dolphin_wii_pad`` = ``classic`` (Classic Controller émulé), ``nunchuk`` (Wiimote + Nunchuk
  émulés, pointeur au stick droit) ou ``real`` (vraies Wiimotes). Sans ce réglage le fichier n'est pas touché.
* ``SYSCONF`` (NAND de la Wii, binaire): ``dolphin_wii_language`` (0 à 9), ``dolphin_wii_tv`` (0 4:3, 1 16:9),
  ``dolphin_sensorbar`` (position de la barre capteur: 0 en bas, 1 en haut).
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

GAMECUBE_SYSTEMS = frozenset({"gc", "gamecube"})  # "gc" dans systems.yml d'ES-NE
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

# Mappages SDL de Dolphin (noms de ``SDL/<n>/<manette>``), alignés sur la disposition « Nintendo » comme Batocera:
# les boutons suivent la position (A à droite, B en bas, X en haut, Y à gauche), pas l'étiquette de la manette.
SDL_STICKS = {
    "Left Stick": ("Left Y+", "Left Y-", "Left X-", "Left X+"),
    "Right Stick": ("Right Y+", "Right Y-", "Right X-", "Right X+"),
}
SDL_DPAD = ("Pad N", "Pad S", "Pad W", "Pad E")
WII_PAD_MODES = frozenset({"classic", "nunchuk", "real"})


def _four(prefix: str, names: tuple[str, str, str, str]) -> dict[str, str]:
    return {f"{prefix}/{way}": f"`{name}`" for way, name in zip(("Up", "Down", "Left", "Right"), names)}


def wiimote_mapping(mode: str) -> dict[str, str]:
    """Clés de ``[WiimoteN]`` pour la manette SDL, selon le mode (classic ou nunchuk)."""
    if mode == "classic":
        mapping = {
            "Extension": "Classic",
            "Classic/Buttons/A": "`Button B`", "Classic/Buttons/B": "`Button A`",
            "Classic/Buttons/X": "`Button Y`", "Classic/Buttons/Y": "`Button X`",
            "Classic/Buttons/ZL": "`Shoulder L`", "Classic/Buttons/ZR": "`Shoulder R`",
            "Classic/Buttons/-": "`Back`", "Classic/Buttons/+": "`Start`", "Classic/Buttons/Home": "`Guide`",
            "Classic/Triggers/L": "`Trigger L`", "Classic/Triggers/R": "`Trigger R`",
            "Classic/Triggers/L-Analog": "`Trigger L`", "Classic/Triggers/R-Analog": "`Trigger R`",
        }
        mapping.update(_four("Classic/D-Pad", SDL_DPAD))
        mapping.update(_four("Classic/Left Stick", SDL_STICKS["Left Stick"]))
        mapping.update(_four("Classic/Right Stick", SDL_STICKS["Right Stick"]))
        return mapping
    mapping = {
        "Extension": "Nunchuk",
        "Buttons/A": "`Button A`", "Buttons/B": "`Button B`",
        "Buttons/1": "`Button X`", "Buttons/2": "`Button Y`",
        "Buttons/-": "`Shoulder L`", "Buttons/+": "`Shoulder R`", "Buttons/Home": "`Back`",
        "Nunchuk/Buttons/C": "`Trigger L`", "Nunchuk/Buttons/Z": "`Trigger R`",
    }
    mapping.update(_four("D-Pad", SDL_DPAD))
    mapping.update(_four("Nunchuk/Stick", SDL_STICKS["Left Stick"]))
    mapping.update(_four("IR", SDL_STICKS["Right Stick"]))  # pointeur: stick droit
    return mapping


def gamecube_mapping() -> dict[str, str]:
    """Clés de ``[GCPadN]``: la disposition que Dolphin propose lui-même pour une manette SDL (A = Button A...)."""
    mapping = {
        "Buttons/A": "`Button A`", "Buttons/B": "`Button B`", "Buttons/X": "`Button X`", "Buttons/Y": "`Button Y`",
        "Buttons/Z": "`Shoulder R`", "Buttons/Start": "`Start`",
        "Triggers/L": "`Trigger L`", "Triggers/R": "`Trigger R`",
        "Triggers/L-Analog": "`Trigger L`", "Triggers/R-Analog": "`Trigger R`",
        "Rumble/Motor": "`Motor L` | `Motor R`",
    }
    mapping.update(_four("D-Pad", SDL_DPAD))
    mapping.update(_four("Main Stick", SDL_STICKS["Left Stick"]))
    mapping.update(_four("C-Stick", SDL_STICKS["Right Stick"]))
    return mapping


def write_gcpads(path: Path, pads: list) -> int:
    """Réécrit ``GCPadNew.ini`` (jusqu'à 4 manettes SDL). Renvoie le nombre de manettes mappées."""
    mapping = gamecube_mapping()
    lines: list[str] = []
    seen: dict[str, int] = {}
    for number in range(1, 5):
        lines.append(f"[GCPad{number}]")
        if number <= len(pads):
            name = (pads[number - 1].name or "").strip() or "Controller"
            same = seen.get(name, 0)
            seen[name] = same + 1
            lines.append(f"Device = SDL/{same}/{name}")
            lines += [f"{key} = {value}" for key, value in mapping.items()]
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".esne-tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temporary.replace(path)
    return min(len(pads), 4)


def write_wiimotes(path: Path, mode: str, pads: list) -> int:
    """Réécrit ``WiimoteNew.ini``. ``real``: vraies Wiimotes (Source = 2). Renvoie le nombre de manettes mappées."""
    lines: list[str] = []
    done = 0
    if mode == "real":
        for number in range(1, 5):
            lines += [f"[Wiimote{number}]", "Source = 2"]
        lines += ["[BalanceBoard]", "Source = 2"]
    else:
        mapping = wiimote_mapping(mode)
        seen: dict[str, int] = {}
        for number, pad in enumerate(pads[:4], start=1):
            name = (pad.name or "").strip() or "Controller"
            same = seen.get(name, 0)
            seen[name] = same + 1
            lines += [f"[Wiimote{number}]", f"Device = SDL/{same}/{name}", "Source = 1"]
            lines += [f"{key} = {value}" for key, value in mapping.items()]
            done += 1
        for number in range(len(pads[:4]) + 1, 5):
            lines += [f"[Wiimote{number}]", "Source = 0"]
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".esne-tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temporary.replace(path)
    return done


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
    for setting, key, allowed in (("dolphin_wii_language", "IPL.LNG", SYSCONF_LANGUAGE), ("dolphin_wii_tv", "IPL.AR", SYSCONF_TV),
                                 ("dolphin_sensorbar", "BT.BAR", SYSCONF_TV)):
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
        if ctx.system in GAMECUBE_SYSTEMS and str(ctx.setting("dolphin_gc_pad", "") or "").strip().lower() == "sdl":
            count = write_gcpads(folder / "GCPadNew.ini", ctx.controllers)
            log.info("dolphin: %d manette(s) GameCube configurée(s)", count)
            ports = {f"SIDevice{port}": "6" if port < count else "0" for port in range(4)}  # 6 = manette standard
            update_ini(folder / "Dolphin.ini", {"Core": ports})
        mode = str(ctx.setting("dolphin_wii_pad", "") or "").strip().lower()
        if ctx.system == "wii" and mode:
            if mode in WII_PAD_MODES:
                log.info("dolphin: %d manette(s) configurée(s) pour la Wii (%s)", write_wiimotes(folder / "WiimoteNew.ini", mode, ctx.controllers), mode)
            else:
                log.warning("valeur inconnue pour dolphin_wii_pad ignorée: %s", mode)
        values = sysconf_values(ctx)
        if values:
            patch_sysconf(data_dir(command.argv) / "Wii/shared2/sys/SYSCONF", values)
        return command


GENERATOR = Dolphin
