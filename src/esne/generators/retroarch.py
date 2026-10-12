# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur RetroArch (cores libretro).

RetroArch est lancé avec un fichier de configuration complémentaire (--appendconfig) écrit à chaque
lancement dans <cache>/retroarch/<système>.cfg: le retroarch.cfg de l'utilisateur n'est jamais modifié.
"""
from __future__ import annotations

import logging
import shlex
import shutil
from pathlib import Path

from .. import catalog, paths
from ..errors import CORE_MISSING, EMULATOR_MISSING, OTHER_ERROR, LaunchError
from .base import Command, Context, Generator

log = logging.getLogger("es-launcher")

DEFAULT_BINARIES = ["retroarch", "flatpak run org.libretro.RetroArch"]
DEFAULT_CORE_DIRS = ["/usr/lib/libretro", "~/.config/retroarch/cores"]

# Ordre de l'énumération ASPECT_RATIO_* de RetroArch (valeur de aspect_ratio_index).
# Non validé sur une installation réelle: l'ordre peut changer d'une version de RetroArch à l'autre.
RATIOS = [
    "4/3", "16/9", "16/10", "16/15", "21/9", "1/1", "2/1", "3/2", "3/4", "4/1", "9/16", "5/4",
    "6/5", "7/9", "8/7", "19/12", "19/14", "30/17", "32/9", "config", "squarepixel", "core", "custom", "full",
]

SHADER_EXTENSIONS = (".slangp", ".glslp", ".cgp")


def truthy(value) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def quote(value) -> str:
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def find_binary(candidates=None, which=shutil.which) -> list[str]:
    """Préfixe de commande de RetroArch: le premier candidat dont le programme existe."""
    for candidate in candidates or DEFAULT_BINARIES:
        parts = shlex.split(candidate)
        if parts and which(parts[0]):
            return [which(parts[0]), *parts[1:]]
    raise LaunchError(EMULATOR_MISSING, "RetroArch est introuvable (installez le paquet retroarch)")


def find_core(core: str, directories=None) -> Path:
    for directory in directories or DEFAULT_CORE_DIRS:
        candidate = Path(directory).expanduser() / f"{core}_libretro.so"
        if candidate.is_file():
            return candidate
    raise LaunchError(CORE_MISSING, f"core libretro introuvable: {core}_libretro.so")


def find_shader(name: str, directories=None) -> Path | None:
    """Nom de shader (ou chemin) -> fichier de preset."""
    direct = Path(name).expanduser()
    if direct.is_absolute() and direct.is_file():
        return direct
    for directory in directories if directories is not None else _shader_dirs():
        for extension in SHADER_EXTENSIONS:
            candidate = Path(directory) / f"{name}{extension}"
            if candidate.is_file():
                return candidate
    # les presets libretro sont rangés par thème (crt/, scanlines/...): on cherche par nom dans l'arborescence
    for directory in directories if directories is not None else _shader_dirs():
        root = Path(directory)
        if not root.is_dir():
            continue
        for extension in SHADER_EXTENSIONS:
            for candidate in sorted(root.rglob(f"{name}{extension}")):
                if candidate.is_file():
                    return candidate
    return None


def _shader_dirs() -> list[Path]:
    return [
        paths.data_dir() / "shaders",
        paths.share_dir() / "shaders",
        Path("/usr/share/libretro/shaders"),
    ]


def shader_dirs() -> list[Path]:
    return _shader_dirs()


# Indices des boutons côté SDL (ordre SDL_GameControllerButton, identique à celui d'ES et du pilote sdl2).
PAD_BUTTONS = {
    "south": 0, "east": 1, "west": 2, "north": 3,
    "select": 4, "guide": 5, "start": 6, "l3": 7, "r3": 8, "l1": 9, "r1": 10,
}

# réglage ES-NE -> (clé RetroArch, valeur par défaut)
HOTKEYS = {
    "hotkey_enable": ("input_enable_hotkey_btn", "select"),  # touche à maintenir
    "hotkey_exit": ("input_exit_emulator_btn", "start"),     # Select + Start: retour à ES
    "hotkey_menu": ("input_menu_toggle_btn", "r3"),          # Select + R3: menu RetroArch (cores, options)
}


def hotkey_settings(ctx: Context) -> dict[str, str]:
    result: dict[str, str] = {}
    for name, (key, default) in HOTKEYS.items():
        button = str(ctx.setting(name, default)).lower()
        if button in ("none", "off", ""):
            continue
        if button not in PAD_BUTTONS:
            log.warning("bouton inconnu pour %s ignoré: %s", name, button)
            continue
        result[key] = str(PAD_BUTTONS[button])
    # sans touche à maintenir, un bouton seul quitterait le jeu à chaque pression
    if "input_enable_hotkey_btn" not in result:
        result.pop("input_exit_emulator_btn", None)
        result.pop("input_menu_toggle_btn", None)
    return result


def build_settings(ctx: Context) -> dict[str, str]:
    """Réglages RetroArch déduits de la configuration d'ES-NE et du contexte."""
    saves = paths.data_dir() / "saves" / ctx.system

    settings: dict[str, str] = {
        "video_fullscreen": "true",
        "config_save_on_exit": "false",
        "input_autodetect_enable": "true",
        "system_directory": str(paths.bios_dir()),
        "savefile_directory": str(saves),
        "savestate_directory": str(saves),
        "screenshot_directory": str(paths.data_dir() / "screenshots"),
    }

    # Pas de paquet autoconfig sur Arch: le pilote udev laisse les manettes "non configurées".
    # Le pilote sdl2 s'appuie sur la base de mappings SDL (DS4, DualSense, Xbox...) sans fichier de profil.
    joypad = ctx.setting("joypad_driver", "sdl2")
    if joypad and joypad != "auto":
        settings["input_joypad_driver"] = str(joypad)

    settings.update(hotkey_settings(ctx))

    smooth = ctx.setting("smooth")
    if smooth is not None:
        settings["video_smooth"] = "true" if truthy(smooth) else "false"

    ratio = ctx.setting("ratio")
    if ratio is not None:
        if ratio in RATIOS:
            settings["aspect_ratio_index"] = str(RATIOS.index(ratio))
            # sans cela RetroArch garde le ratio fourni par le core et ignore aspect_ratio_index
            settings["video_aspect_ratio_auto"] = "false"
        else:
            log.warning("ratio inconnu ignoré: %s", ratio)

    rewind = ctx.setting("rewind")
    if rewind is not None:
        settings["rewind_enable"] = "true" if truthy(rewind) else "false"

    autosave = ctx.extras.get("autosave", ctx.setting("autosave"))
    if autosave is not None:
        enabled = "true" if truthy(autosave) else "false"
        settings["savestate_auto_save"] = enabled
        settings["savestate_auto_load"] = enabled

    integer = ctx.setting("integerscale")
    if integer is not None:
        settings["video_scale_integer"] = "true" if truthy(integer) else "false"

    shader = ctx.setting("shaderset")
    if shader and shader != "none":
        preset = find_shader(shader)
        if preset is None:
            log.warning("shader introuvable ignoré: %s", shader)
        else:
            settings["video_shader_enable"] = "true"
            settings["video_shader"] = str(preset)
            # les presets slang (.slangp) exigent glcore ou vulkan; le pilote "gl" classique ne sait charger que du GLSL
            if preset.suffix == ".slangp":
                settings["video_driver"] = "glcore"

    video_driver = ctx.setting("video_driver")
    if video_driver and video_driver != "auto":
        settings["video_driver"] = str(video_driver)

    return settings


def write_config(ctx: Context, settings: dict[str, str]) -> Path:
    target = paths.cache_dir() / "retroarch" / f"{ctx.system}.cfg"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("".join(f"{key} = {quote(value)}\n" for key, value in sorted(settings.items())), encoding="utf-8")
        # RetroArch crée les dossiers de sauvegarde lui-même s'il le peut; on le fait pour les erreurs de droits
        for key in ("savefile_directory", "savestate_directory", "screenshot_directory", "system_directory"):
            Path(settings[key]).mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise LaunchError(OTHER_ERROR, f"impossible d'écrire la configuration RetroArch: {exc}") from exc
    return target


class RetroArch(Generator):
    name = "libretro"

    def generate(self, ctx: Context) -> Command:
        if not ctx.core:
            raise LaunchError(CORE_MISSING, f"aucun core défini pour le système '{ctx.system}'")

        info = catalog.emulator_info("libretro") or {}
        binary = find_binary(info.get("binary"))
        core = find_core(ctx.core, info.get("core_dirs"))

        for controller in ctx.controllers:
            log.debug("manette %d: %s (%s)", controller.player, controller.name, controller.path)

        settings = build_settings(ctx)
        config = write_config(ctx, settings)
        log.info("réglages RetroArch (%s): %s", config, ", ".join(f"{k}={v}" for k, v in sorted(settings.items())
                                                                   if k.startswith(("video_", "aspect_", "rewind", "savestate_auto", "input_joypad"))))
        return Command(argv=[*binary, "-L", str(core), "--appendconfig", str(config), ctx.rom])


GENERATOR = RetroArch
