# SPDX-License-Identifier: GPL-3.0-or-later
"""Génère ``es_features.cfg`` (options par système et par jeu affichées par ES) et les jeux de shaders.

On ne déclare que ce que ``es-launcher`` sait appliquer.
"""
from __future__ import annotations

from pathlib import Path

from . import paths
from .generators import retroarch

# Fonctions d'ES (voir EmulatorFeatures::parseFeatures) prises en charge par le générateur libretro.
LIBRETRO_FEATURES = ["autosave", "ratio", "rewind", "smooth", "shaders", "pixel_perfect", "decoration"]

# Presets libretro proposés dans « SHADER SET » s'ils sont installés (nom du fichier sans extension).
SHADER_SETS = [
    "crt-geom", "crt-easymode", "crt-aperture", "crt-lottes", "crt-royale", "zfast_crt",
    "scanlines", "sharp-bilinear", "lcd-grid-v2", "gameboy",
]


# Option personnalisée « pilote vidéo » (ES enregistre <système>.video_driver; « AUTO » = valeur vide).
VIDEO_DRIVER_FEATURE = (
    '<feature name="VIDEO DRIVER" value="video_driver" '
    'description="Graphics API used by RetroArch. Vulkan is usually the most efficient with shaders; Auto picks Vulkan when available.">'
    '<choice name="VULKAN" value="vulkan" />'
    '<choice name="OPENGL (GLCORE)" value="glcore" />'
    '<choice name="OPENGL (LEGACY, NO SLANG SHADERS)" value="gl" />'
    "</feature>"
)


# Options Cemu (ES enregistre <système>.cemu_api et <système>.cemu_autoconfig).
CEMU_FEATURES = (
    '<feature name="GRAPHICS API" value="cemu_api" '
    'description="Applied to Cemu\'s settings.xml. Cemu must have been started once so the file exists.">'
    '<choice name="VULKAN" value="vulkan" /><choice name="OPENGL" value="opengl" /></feature>'
    '<feature name="AUTOCONFIGURE CONTROLLERS" value="cemu_autoconfig" '
    'description="Write Wii U Pro Controller profiles for the pads ES sees. Turn off to keep your own mapping.">'
    '<choice name="ON" value="1" /><choice name="OFF" value="0" /></feature>'
    '<feature name="CONSOLE LANGUAGE" value="cemu_language" description="Wii U system language. Applied to settings.xml.">'
    '<choice name="JAPANESE" value="0" /><choice name="ENGLISH" value="1" /><choice name="FRENCH" value="2" />'
    '<choice name="GERMAN" value="3" /><choice name="ITALIAN" value="4" /><choice name="SPANISH" value="5" />'
    '<choice name="CHINESE" value="6" /><choice name="KOREAN" value="7" /><choice name="DUTCH" value="8" />'
    '<choice name="PORTUGUESE" value="9" /><choice name="RUSSIAN" value="10" /><choice name="TAIWANESE" value="11" /></feature>'
    '<feature name="VSYNC" value="cemu_vsync" description="Fix screen tearing.">'
    '<choice name="OFF" value="0" /><choice name="ON" value="1" /></feature>'
    '<feature name="UPSCALE FILTER" value="cemu_upscale" description="Filter used when the image is enlarged.">'
    '<choice name="BILINEAR" value="0" /><choice name="BICUBIC" value="1" /><choice name="HERMITE" value="2" />'
    '<choice name="NEAREST NEIGHBOR" value="3" /></feature>'
    '<feature name="FULLSCREEN SCALING" value="cemu_scaling" description="Keep the aspect ratio or stretch to the screen.">'
    '<choice name="KEEP ASPECT RATIO" value="0" /><choice name="STRETCH" value="1" /></feature>'
    '<feature name="TV VOLUME" value="cemu_volume" description="Game volume.">'
    '<choice name="0%" value="0" /><choice name="25%" value="25" /><choice name="50%" value="50" />'
    '<choice name="75%" value="75" /><choice name="100%" value="100" /></feature>'
    '<feature name="SHOW FPS" value="cemu_fps" description="Frame counter overlay.">'
    '<choice name="OFF" value="false" /><choice name="ON" value="true" /></feature>'
)


# Options PCSX2 (ES enregistre <système>.<clé>).
PCSX2_FEATURES = (
    '<feature name="GRAPHICS API" value="pcsx2_gfxbackend" description="Renderer used by PCSX2. Applied to PCSX2.ini, which PCSX2 creates at its first launch.">'
    '<choice name="VULKAN" value="vulkan" /><choice name="OPENGL" value="opengl" /><choice name="SOFTWARE" value="software" /></feature>'
    '<feature name="RENDERING RESOLUTION" value="pcsx2_resolution" description="Increase the internal resolution.">'
    '<choice name="NATIVE (PS2)" value="1" /><choice name="2X (~720P)" value="2" /><choice name="3X (~1080P)" value="3" />'
    '<choice name="4X (~1440P)" value="4" /><choice name="6X (~4K)" value="6" /></feature>'
    '<feature name="GAME ASPECT RATIO" value="pcsx2_ratio" description="Force the aspect ratio.">'
    '<choice name="AUTO 4:3 / 3:2" value="Auto 4:3/3:2" /><choice name="4:3" value="4:3" />'
    '<choice name="16:9" value="16:9" /><choice name="STRETCH" value="Stretch" /></feature>'
    '<feature name="VSYNC" value="pcsx2_vsync" description="Fix screen tearing.">'
    '<choice name="OFF" value="false" /><choice name="ON" value="true" /></feature>'
    '<feature name="FXAA" value="pcsx2_fxaa" description="FXAA anti-aliasing.">'
    '<choice name="OFF" value="false" /><choice name="ON" value="true" /></feature>'
    '<feature name="ANISOTROPIC FILTERING" value="pcsx2_af" description="Texture sharpness at oblique angles.">'
    '<choice name="OFF" value="0" /><choice name="2X" value="2" /><choice name="4X" value="4" />'
    '<choice name="8X" value="8" /><choice name="16X" value="16" /></feature>'
    '<feature name="TEXTURE FILTERING" value="pcsx2_filter" description="How textures are smoothed.">'
    '<choice name="NEAREST" value="0" /><choice name="BILINEAR (FORCED)" value="1" />'
    '<choice name="BILINEAR (PS2)" value="2" /><choice name="BILINEAR (FORCED EXCLUDING SPRITES)" value="3" /></feature>'
    '<feature name="CAS SHARPENING" value="pcsx2_cas" description="AMD contrast adaptive sharpening.">'
    '<choice name="OFF" value="0" /><choice name="SHARPEN ONLY" value="1" /><choice name="SHARPEN AND RESIZE" value="2" /></feature>'
    '<feature name="DITHERING" value="pcsx2_dither" description="PS2 dithering emulation.">'
    '<choice name="OFF" value="0" /><choice name="SCALED" value="1" /><choice name="UNSCALED" value="2" /></feature>'
    '<feature name="WIDESCREEN PATCHES" value="pcsx2_widescreen" description="Apply 16:9 patches shipped with PCSX2, for games that have one.">'
    '<choice name="OFF" value="false" /><choice name="ON" value="true" /></feature>'
    '<feature name="NO-INTERLACING PATCHES" value="pcsx2_nointerlace" description="Apply patches that remove interlacing, for games that have one.">'
    '<choice name="OFF" value="false" /><choice name="ON" value="true" /></feature>'
    '<feature name="SHOW FPS" value="pcsx2_fps" description="Frame counter overlay.">'
    '<choice name="OFF" value="false" /><choice name="ON" value="true" /></feature>'
    '<feature name="VOLUME" value="pcsx2_volume" description="Game volume.">'
    '<choice name="0%" value="0" /><choice name="25%" value="25" /><choice name="50%" value="50" />'
    '<choice name="75%" value="75" /><choice name="100%" value="100" /></feature>'
    '<feature name="MUTE AUDIO" value="pcsx2_mute" description="Turn the sound off.">'
    '<choice name="OFF" value="false" /><choice name="ON" value="true" /></feature>'
    '<feature name="RETROACHIEVEMENTS" value="pcsx2_achievements" description="Enable achievements. Log in once in PCSX2.">'
    '<choice name="OFF" value="false" /><choice name="ON" value="true" /></feature>'
    '<feature name="AUTOCONFIGURE CONTROLLERS" value="pcsx2_autoconfig" '
    'description="Map the pads ES sees to DualShock 2 ports. Turn off to keep your own mapping.">'
    '<choice name="ON" value="1" /><choice name="OFF" value="0" /></feature>'
)


EDEN_FEATURES = (
    '<feature name="AUTOCONFIGURE CONTROLLERS" value="eden_autoconfig" '
    'description="Copy the player 1 mapping you set in Eden to the other pads of the same model. Turn off to keep your own mapping.">'
    '<choice name="ON" value="1" /><choice name="OFF" value="0" /></feature>'
    '<feature name="CONSOLE MODE" value="eden_docked" description="Docked uses the TV resolution, handheld is lighter. Applied to qt-config.ini.">'
    '<choice name="DOCKED" value="1" /><choice name="HANDHELD" value="0" /></feature>'
    '<feature name="RESOLUTION" value="eden_resolution" description="Internal resolution scale.">'
    '<choice name="1X (720P/1080P)" value="3" /><choice name="2X (1440P/2160P)" value="6" /><choice name="3X" value="7" /><choice name="4X" value="8" /></feature>'
    '<feature name="ANISOTROPIC FILTERING" value="eden_af" description="Texture sharpness at oblique angles.">'
    '<choice name="2X" value="2" /><choice name="4X" value="3" /><choice name="8X" value="4" /><choice name="16X" value="5" /></feature>'
    '<feature name="VSYNC MODE" value="eden_vsync" description="Synchronization with the screen.">'
    '<choice name="MAILBOX (RECOMMENDED)" value="1" /><choice name="FIFO" value="2" />'
    '<choice name="FIFO RELAXED" value="3" /><choice name="IMMEDIATE (NO VSYNC)" value="0" /></feature>'
    '<feature name="ANTI-ALIASING" value="eden_aa" description="Post-processing anti-aliasing.">'
    '<choice name="NONE" value="0" /><choice name="FXAA" value="1" /><choice name="SMAA" value="2" /></feature>'
    '<feature name="SCALING FILTER" value="eden_filter" description="Filter used to resize the image.">'
    '<choice name="NEAREST" value="0" /><choice name="BILINEAR" value="1" /><choice name="BICUBIC" value="2" />'
    '<choice name="GAUSSIAN" value="3" /><choice name="SCALEFORCE" value="4" /><choice name="FSR" value="5" /></feature>'
    '<feature name="ASPECT RATIO" value="eden_ratio" description="Screen aspect ratio.">'
    '<choice name="DEFAULT (16:9)" value="0" /><choice name="FORCE 4:3" value="1" /><choice name="FORCE 21:9" value="2" />'
    '<choice name="FORCE 16:10" value="3" /><choice name="STRETCH" value="4" /></feature>'
    '<feature name="CONSOLE LANGUAGE" value="eden_language" description="Switch system language used by games.">'
    '<choice name="JAPANESE" value="0" /><choice name="ENGLISH (US)" value="1" /><choice name="FRENCH" value="2" />'
    '<choice name="GERMAN" value="3" /><choice name="ITALIAN" value="4" /><choice name="SPANISH" value="5" />'
    '<choice name="KOREAN" value="7" /><choice name="DUTCH" value="8" /><choice name="PORTUGUESE" value="9" />'
    '<choice name="RUSSIAN" value="10" /><choice name="ENGLISH (UK)" value="12" /><choice name="CANADIAN FRENCH" value="13" />'
    '<choice name="LATIN AMERICAN SPANISH" value="14" /><choice name="SIMPLIFIED CHINESE" value="15" />'
    '<choice name="TRADITIONAL CHINESE" value="16" /><choice name="BRAZILIAN PORTUGUESE" value="17" /></feature>'
    '<feature name="CONSOLE REGION" value="eden_region" description="Switch region.">'
    '<choice name="JAPAN" value="0" /><choice name="USA" value="1" /><choice name="EUROPE" value="2" />'
    '<choice name="AUSTRALIA" value="3" /><choice name="CHINA" value="4" /><choice name="KOREA" value="5" />'
    '<choice name="TAIWAN" value="6" /></feature>'
)


RPCS3_FEATURES = (
    '<feature name="GRAPHICS API" value="rpcs3_gfxbackend" description="Backend used by RPCS3. Vulkan is strongly recommended.">'
    '<choice name="VULKAN" value="vulkan" /><choice name="OPENGL" value="opengl" /></feature>'
    '<feature name="RENDER RESOLUTION (SCALING)" value="rpcs3_resolution_scale" description="Internal resolution relative to 720p.">'
    '<choice name="1280X720 (100%)" value="100" /><choice name="1920X1080 (150%)" value="150" />'
    '<choice name="2560X1440 (200%)" value="200" /><choice name="3840X2160 (300%)" value="300" /></feature>'
    '<feature name="ASPECT RATIO" value="rpcs3_ratio" description="PS3 internal aspect ratio.">'
    '<choice name="16:9" value="16:9" /><choice name="4:3" value="4:3" /></feature>'
    '<feature name="VSYNC MODE" value="rpcs3_vsync" description="Synchronize frames with the monitor.">'
    '<choice name="DISABLED" value="Disabled" /><choice name="FULL" value="Full" /><choice name="ADAPTIVE" value="Adaptive" /></feature>'
    '<feature name="AUTOCONFIGURE CONTROLLERS" value="rpcs3_autoconfig" '
    'description="Write the SDL pad mapping for the pads ES sees. Turn off to keep your own mapping.">'
    '<choice name="ON" value="1" /><choice name="OFF" value="0" /></feature>'
)


XEMU_FEATURES = (
    '<feature name="AUTOCONFIGURE CONTROLLERS" value="xemu_autoconfig" '
    'description="Assign the pads ES sees to the Xbox controller ports. Turn off to keep your own mapping.">'
    '<choice name="ON" value="1" /><choice name="OFF" value="0" /></feature>'
    '<feature name="RENDER RESOLUTION" value="xemu_scale" description="Internal resolution scale. Applied to xemu.toml.">'
    '<choice name="1X (NATIVE)" value="1" /><choice name="2X" value="2" /><choice name="3X" value="3" /><choice name="4X" value="4" /></feature>'
    '<feature name="ASPECT RATIO" value="xemu_aspect" description="Screen aspect ratio.">'
    '<choice name="NATIVE" value="native" /><choice name="AUTO" value="auto" /><choice name="4:3" value="4x3" /><choice name="16:9" value="16x9" /></feature>'
)


# Options Xenia (ES enregistre <système>.<clé>); passées en ligne de commande, la configuration de Xenia n'est pas modifiée.
XENIA_FEATURES = (
    '<feature name="RENDERING RESOLUTION" value="xenia_resolution" description="Internal resolution scale (Xbox 360 is 720p).">'
    '<choice name="NATIVE (720P)" value="1" /><choice name="2X (~1440P)" value="2" />'
    '<choice name="3X (~2160P)" value="3" /><choice name="4X" value="4" /></feature>'
    '<feature name="VSYNC" value="xenia_vsync" description="Fix screen tearing.">'
    '<choice name="OFF" value="false" /><choice name="ON" value="true" /></feature>'
    '<feature name="ANTI-ALIASING" value="xenia_aa" description="Post-processing anti-aliasing.">'
    '<choice name="NONE" value="none" /><choice name="FXAA" value="fxaa" /><choice name="FXAA (EXTREME)" value="fxaa_extreme" /></feature>'
    '<feature name="UPSCALING / SHARPENING" value="xenia_scaling" description="Resampling of the final image. CAS sharpens, FSR upscales (AMD FidelityFX).">'
    '<choice name="BILINEAR" value="bilinear" /><choice name="CAS" value="cas" /><choice name="FSR" value="fsr" /></feature>'
    '<feature name="ANISOTROPIC FILTERING" value="xenia_af" description="Force anisotropic filtering on textures. Leave on default to keep the game\'s own setting.">'
    '<choice name="OFF" value="0" /><choice name="2X" value="2" /><choice name="4X" value="3" />'
    '<choice name="8X" value="4" /><choice name="16X" value="5" /></feature>'
    '<feature name="FRAME RATE LIMIT" value="xenia_fps" description="Maximum frames per second.">'
    '<choice name="30 FPS" value="30" /><choice name="60 FPS" value="60" /><choice name="UNLIMITED" value="0" /></feature>'
    '<feature name="CONSOLE LANGUAGE" value="xenia_language" description="Xbox 360 system language, stored in Xenia\'s xconfig.settings. Xenia must have been started once.">'
    '<choice name="ENGLISH" value="1" /><choice name="FRENCH" value="4" /><choice name="GERMAN" value="3" />'
    '<choice name="SPANISH" value="5" /><choice name="ITALIAN" value="6" /><choice name="JAPANESE" value="2" />'
    '<choice name="KOREAN" value="7" /><choice name="TRADITIONAL CHINESE" value="8" /><choice name="SIMPLIFIED CHINESE" value="10" />'
    '<choice name="PORTUGUESE" value="9" /><choice name="POLISH" value="11" /><choice name="RUSSIAN" value="12" /></feature>'
    '<feature name="CONSOLE REGION" value="xenia_region" description="Xbox 360 country, stored in Xenia\'s xconfig.settings. Xenia must have been started once.">'
    '<choice name="FRANCE" value="34" /><choice name="GERMANY" value="24" /><choice name="SPAIN" value="31" />'
    '<choice name="ITALY" value="50" /><choice name="UNITED KINGDOM" value="35" /><choice name="UNITED STATES" value="103" />'
    '<choice name="JAPAN" value="53" /></feature>'
    '<feature name="MUTE AUDIO" value="xenia_mute" description="Turn the sound off.">'
    '<choice name="OFF" value="false" /><choice name="ON" value="true" /></feature>'
    '<feature name="AUDIO SYSTEM" value="xenia_apu" description="Audio backend.">'
    '<choice name="AUTO" value="any" /><choice name="ALSA" value="alsa" /><choice name="SDL" value="sdl" /></feature>'
)


# Options Redream (ES enregistre <système>.<clé>); écrites dans redream.cfg quand elles sont choisies.
REDREAM_FEATURES = (
    '<feature name="REGION" value="redream_region" description="Dreamcast region. Applied to redream.cfg, which Redream creates at its first launch.">'
    '<choice name="EUROPE" value="europe" /><choice name="USA" value="usa" /><choice name="JAPAN" value="japan" /></feature>'
    '<feature name="CONSOLE LANGUAGE" value="redream_language" description="Dreamcast system language.">'
    '<choice name="ENGLISH" value="english" /><choice name="FRENCH" value="french" /><choice name="GERMAN" value="german" />'
    '<choice name="SPANISH" value="spanish" /><choice name="ITALIAN" value="italian" /><choice name="JAPANESE" value="japanese" /></feature>'
    '<feature name="BROADCAST" value="redream_broadcast" description="TV standard. PAL for Europe, NTSC for USA and Japan.">'
    '<choice name="PAL" value="pal" /><choice name="NTSC" value="ntsc" /></feature>'
    '<feature name="CABLE" value="redream_cable" description="Video cable. VGA gives a progressive image in games that support it.">'
    '<choice name="VGA" value="vga" /><choice name="COMPOSITE" value="composite" /></feature>'
    '<feature name="ASPECT RATIO" value="redream_aspect" description="Screen aspect ratio.">'
    '<choice name="16:9" value="16:9" /><choice name="4:3" value="4:3" /><choice name="STRETCH" value="stretch" /></feature>'
    '<feature name="RENDERING RESOLUTION" value="redream_res" description="Internal resolution scale.">'
    '<choice name="1X" value="1" /><choice name="2X" value="2" /><choice name="3X" value="3" /><choice name="4X" value="4" /></feature>'
    '<feature name="VSYNC" value="redream_vsync" description="Fix screen tearing.">'
    '<choice name="OFF" value="0" /><choice name="ON" value="1" /></feature>'
)


STEAM_FEATURES = (
    '<feature name="KEEP STEAM OPEN" value="steam_keep_open" '
    'description="Keep the Steam client running after the game (faster next launch). Off: close it when ES-NE had to open it.">'
    '<choice name="OFF" value="0" /><choice name="ON" value="1" /></feature>'
)


def render() -> str:
    return (
        '<?xml version="1.0"?>\n'
        "<features>\n"
        f"  <globalFeatures>{VIDEO_DRIVER_FEATURE}</globalFeatures>\n"
        f'  <emulator name="libretro" features="{",".join(LIBRETRO_FEATURES)}">{VIDEO_DRIVER_FEATURE}</emulator>\n'
        f'  <emulator name="cemu" features="">{CEMU_FEATURES}</emulator>\n'
        f'  <emulator name="pcsx2" features="">{PCSX2_FEATURES}</emulator>\n'
        f'  <emulator name="eden" features="">{EDEN_FEATURES}</emulator>\n'
        f'  <emulator name="rpcs3" features="">{RPCS3_FEATURES}</emulator>\n'
        f'  <emulator name="xemu" features="">{XEMU_FEATURES}</emulator>\n'
        f'  <emulator name="xenia" features="">{XENIA_FEATURES}</emulator>\n'
        f'  <emulator name="redream" features="">{REDREAM_FEATURES}</emulator>\n'
        f'  <emulator name="steam" features="">{STEAM_FEATURES}</emulator>\n'
        "</features>\n"
    )


def installed_shader_sets(names=SHADER_SETS, directories=None) -> list[str]:
    return [name for name in names if retroarch.find_shader(name, directories) is not None]


def write_shader_sets(target: Path, names: list[str]) -> list[Path]:
    """ES liste les dossiers <data>/shaders/configs/<jeu>/ qui contiennent rendering-defaults.yml."""
    written = []
    for name in names:
        file = target / name / "rendering-defaults.yml"
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(f"# jeu de shaders ES-NE: preset libretro '{name}'\nshader: {name}\n", encoding="utf-8")
        written.append(file)
    return written


def shaders_root() -> Path:
    return paths.data_dir() / "shaders" / "configs"
