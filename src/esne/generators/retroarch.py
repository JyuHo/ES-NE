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

from .. import archives, bezels, catalog, paths, tbp
from ..errors import CORE_MISSING, EMULATOR_MISSING, OTHER_ERROR, LaunchError
from .base import Command, Context, Generator

log = logging.getLogger("es-launcher")

DEFAULT_BINARIES = ["retroarch", "flatpak run org.libretro.RetroArch"]
DEFAULT_CORE_DIRS = ["/usr/lib/libretro", "~/.config/retroarch/cores"]
DEFAULT_INFO_DIRS = ["/usr/share/libretro/info", "~/.config/retroarch/cores"]

# Ordre de l'énumération ASPECT_RATIO_* de RetroArch (valeur de aspect_ratio_index): « custom » vaut 23, comme dans Batocera.
# Les indices sont repris de la source de RetroArch; ils ont déjà été confirmés pour 4/3, 16/9 et custom (bezels).
RATIOS = [
    "4/3", "16/9", "16/10", "16/15", "21/9", "1/1", "2/1", "3/2", "3/4", "4/1", "9/16", "5/4",
    "6/5", "7/9", "8/3", "8/7", "19/12", "19/14", "30/17", "32/9", "config", "squarepixel", "core", "custom",
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
    # les presets libretro sont rangés par thème (crt/, scanlines/...): on cherche par nom dans l'arborescence.
    # Plusieurs presets portent le même nom (variantes avec cadre sous bezel/...): on prend le moins profond,
    # et on évite les variantes de cadre tant qu'une autre existe.
    for directory in directories if directories is not None else _shader_dirs():
        root = Path(directory)
        if not root.is_dir():
            continue
        found = [c for ext in SHADER_EXTENSIONS for c in root.rglob(f"{name}{ext}") if c.is_file()]
        if found:
            def rank(candidate: Path):
                parts = candidate.relative_to(root).parts[:-1]
                framed = any(("bezel" in part.lower() or "border" in part.lower()) for part in parts)
                return (framed, len(parts), str(candidate))
            return min(found, key=rank)
    return None


def _shader_dirs() -> list[Path]:
    return [
        paths.data_dir() / "shaders",
        paths.share_dir() / "shaders",
        Path("/usr/share/libretro/shaders"),
    ]


def vulkan_available(directories=("/usr/share/vulkan/icd.d", "/etc/vulkan/icd.d")) -> bool:
    """Vrai si un pilote Vulkan (fichier ICD) est installé. Ne garantit pas que RetroArch soit compilé avec Vulkan."""
    return any(any(Path(d).glob("*.json")) for d in directories if Path(d).is_dir())


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

    # États: ES choisit le slot (-state_slot) et copie l'état à charger en <jeu>.state.auto (chargé grâce à -autosave 1)
    if truthy(ctx.setting("incrementalsavestates", "1")):
        settings["savestate_auto_index"] = "true"
        settings["savestate_max_keep"] = "0"
    else:
        settings["savestate_auto_index"] = "false"
        settings["savestate_max_keep"] = "50"
    slot = ctx.extras.get("state_slot")
    if slot is not None:
        if slot.lstrip("-").isdigit() and int(slot) >= 0:
            settings["state_slot"] = slot
        else:
            log.warning("slot d'état invalide ignoré: %s", slot)
    state_file = ctx.extras.get("state_file") or ctx.extras.get("state_filename") or ""
    if state_file.endswith(".auto"):
        settings["savestate_auto_load"] = "true"

    monitor = ctx.extras.get("monitor")
    if monitor is not None:
        if monitor.isdigit():
            settings["video_monitor_index"] = str(int(monitor) + 1)  # RetroArch: 0 = automatique, 1 = premier écran
        else:
            log.warning("écran invalide ignoré: %s", monitor)

    settings.update(netplay_settings(ctx))

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
                settings["video_driver"] = "vulkan" if vulkan_available() else "glcore"

    settings.update(bezel_settings(ctx))

    video_driver = ctx.setting("video_driver")
    if video_driver and video_driver != "auto":
        settings["video_driver"] = str(video_driver)

    return settings


NETPLAY_MODES = ("host", "client", "spectator")


def netplay_settings(ctx: Context) -> dict[str, str]:
    """Réglages RetroArch du netplay d'après les options d'ES (-netplaymode...) et ``netplay.*`` (menu NETPLAY SETTINGS)."""
    mode = ctx.extras.get("netplaymode")
    if mode not in NETPLAY_MODES:
        return {}
    result = {"netplay_start_as_spectator": "true" if mode == "spectator" else "false"}

    def copy(key, name, source=None):
        value = (ctx.extras.get(source) if source else None) or ctx.setting(name)
        if value not in (None, ""):
            result[key] = str(value)

    copy("netplay_nickname", "netplay.nickname")
    copy("netplay_input_latency_frames_min", "netplay.frames")
    if mode == "host":
        copy("netplay_ip_port", "netplay.port")
        copy("netplay_password", "netplay.password")
        copy("netplay_spectate_password", "netplay.spectatepassword")
    else:
        copy("netplay_ip_address", "", "netplayip")
        copy("netplay_ip_port", "netplay.server.port", "netplayport")
        copy("netplay_spectate_password" if mode == "spectator" else "netplay_password", "netplay.password", "netplaypass")
    result["netplay_public_announce"] = "true" if truthy(ctx.setting("netplay_public_announce", "1")) else "false"
    relay = ctx.setting("netplay.relay")
    if relay and relay != "none":
        result["netplay_use_mitm_server"] = "true"
        result["netplay_mitm_server"] = str(relay)
        custom = ctx.setting("netplay.customserver")
        if relay == "custom" and custom:
            result["netplay_custom_mitm_server"] = str(custom)
    else:
        result["netplay_use_mitm_server"] = "false"
    return result


def netplay_args(ctx: Context) -> list[str]:
    """Arguments de ligne de commande RetroArch (--host, --connect...)."""
    mode = ctx.extras.get("netplaymode")
    if mode not in NETPLAY_MODES:
        return []
    args = ["--host"] if mode == "host" else ["--connect", ctx.extras.get("netplayip", "")]
    port = ctx.extras.get("netplayport") if mode != "host" else ctx.setting("netplay.port")
    if port:
        args += ["--port", str(port)]
    if ctx.extras.get("netplaysession"):
        args += ["--mitm-session", ctx.extras["netplaysession"]]
    nick = ctx.setting("netplay.nickname")
    if nick:
        args += ["--nick", str(nick)]
    return args


def find_core_info(core: str, directories=None) -> Path | None:
    for directory in directories or DEFAULT_INFO_DIRS:
        candidate = Path(directory).expanduser() / f"{core}_libretro.info"
        if candidate.is_file():
            return candidate
    return None


def screen_size() -> tuple[int, int] | None:
    """Résolution actuelle de l'écran principal (outils de esctl resolution), None si inconnue."""
    try:
        from ..esctl.commands import resolution
        _backend, outputs = resolution.read_outputs()
        output = resolution.pick_output(outputs, None)
        mode = output.current_mode() if output else None
        return (mode.width, mode.height) if mode else None
    except Exception as exc:  # outil absent, sortie illisible...
        log.debug("résolution de l'écran inconnue: %s", exc)
        return None


def bezel_settings(ctx: Context) -> dict[str, str]:
    """Overlay + zone de jeu pour le jeu de décorations choisi (``<système>.bezel``). Vide si aucun bezel."""
    choice = str(ctx.setting("bezel", "") or "").strip()
    if choice.lower() in ("none", "off", "0"):
        return {}
    if choice in ("", "auto"):
        if not bezels.tbp_installed(ctx.system):
            return {}
        choice = bezels.TBP_SET
    rom_stem = Path(ctx.rom).stem if ctx.rom else None
    if str(ctx.setting("bezel_games", "1")).lower() in ("0", "false", "off", "none"):
        rom_stem = None  # réglage « bezel_games = 0 »: bezel du système seulement
    elif choice == bezels.TBP_SET and rom_stem:
        tbp.ensure_game(ctx.system, rom_stem)  # bezel du jeu à la demande; sans réseau ni bezel, celui du système reste utilisé
    image = bezels.find_image(choice, ctx.system, rom=rom_stem)
    if image is None:
        log.info("aucun bezel '%s' pour le système %s", choice, ctx.system)
        return {}

    settings = {"input_overlay_enable": "true", "input_overlay_opacity": "1.000000"}
    area = bezels.game_area(image)
    screen = screen_size()
    if area is None or screen is None:
        log.warning("bezel %s: zone de jeu ou écran inconnus, le jeu reste plein écran sous l'image", image.name)
    else:
        stretch = str(ctx.setting("bezel_stretch", "auto")).lower()
        stretch = {"true": "1", "false": "0"}.get(stretch, stretch)
        box = bezels.layout(area, screen, stretch)
        if box is None:
            log.warning("bezel %s ignoré: son ratio est trop éloigné de l'écran %dx%d (option STRETCH BEZELS)", image.name, *screen)
            return {}
        # RetroArch ajoute la position de la zone personnalisée à celle de la zone centrée sur l'écran: on envoie l'écart
        # entre la position voulue et la position centrée (0 pour une zone de jeu centrée).
        driver = str(ctx.setting("video_driver", "auto") or "auto")
        if driver == "auto":
            driver = "vulkan" if vulkan_available() else "glcore"
        settings["video_driver"] = driver
        settings.update({
            "aspect_ratio_index": str(RATIOS.index("custom")),
            "video_aspect_ratio_auto": "false",
            "video_scale_integer": "false",
            "custom_viewport_x": str(box[0] - (screen[0] - box[2]) // 2),
            "custom_viewport_y": str(box[1] - (screen[1] - box[3]) // 2),
            "custom_viewport_width": str(box[2]), "custom_viewport_height": str(box[3]),
        })
    overlay = bezels.write_overlay(image, paths.cache_dir() / "retroarch" / "overlays" / f"{ctx.system}.cfg")
    settings["input_overlay"] = str(overlay)
    log.info("bezel: %s (zone de jeu %sx%s)", image, settings.get("custom_viewport_width", "?"), settings.get("custom_viewport_height", "?"))
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
                                                                   if k.startswith(("video_", "aspect_", "custom_viewport", "input_overlay", "rewind", "savestate_auto", "input_joypad"))))
        argv = [*binary, "-L", str(core), "--appendconfig", str(config)]
        if settings.get("video_shader_enable") == "true" and settings.get("video_shader"):
            # la clé video_shader du fichier n'est pas chargée au démarrage par RetroArch: --set-shader l'impose
            argv += ["--set-shader", settings["video_shader"]]
        argv += netplay_args(ctx)
        state_file = ctx.extras.get("state_file") or ctx.extras.get("state_filename") or ""
        if state_file and not state_file.endswith(".auto") and ctx.extras.get("state_slot"):
            argv += ["-e", ctx.extras["state_slot"]]  # charge cet état au démarrage
        rom = archives.prepare(ctx.rom, ctx.system, find_core_info(ctx.core, info.get("info_dirs")))
        return Command(argv=[*argv, rom])


GENERATOR = RetroArch
