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
    '<feature name="AUTOCONFIGURE CONTROLLERS" value="pcsx2_autoconfig" '
    'description="Map the pads ES sees to DualShock 2 ports. Turn off to keep your own mapping.">'
    '<choice name="ON" value="1" /><choice name="OFF" value="0" /></feature>'
)


EDEN_FEATURES = (
    '<feature name="AUTOCONFIGURE CONTROLLERS" value="eden_autoconfig" '
    'description="Copy the player 1 mapping you set in Eden to the other pads of the same model. Turn off to keep your own mapping.">'
    '<choice name="ON" value="1" /><choice name="OFF" value="0" /></feature>'
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
