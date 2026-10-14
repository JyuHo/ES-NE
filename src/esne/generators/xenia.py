# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur Xenia Canary (Xbox 360): ligne de commande de ``emulators.yml`` + réglages vidéo choisis dans ES.

Les réglages sont passés en options de ligne de commande (``--nom=valeur``, mêmes noms que dans
``~/.local/share/Xenia/xenia-canary.config.toml``): le fichier de l'utilisateur n'est pas modifié, et un réglage non choisi
dans ES garde la valeur de ce fichier. Valeurs permises relevées dans les commentaires de ce fichier.

Options ES (``<système>.<clé>``): ``xenia_resolution`` (échelle de rendu 1 à 4), ``xenia_vsync`` (true, false),
``xenia_aa`` (none, fxaa, fxaa_extreme), ``xenia_scaling`` (bilinear, cas, fsr), ``xenia_af`` (filtrage anisotrope: 0, 2 à 5),
``xenia_fps`` (limite d'images par seconde, 0 = illimité), ``xenia_mute`` (true, false), ``xenia_apu`` (système audio:
any, alsa, sdl).

Langue de la console (``xenia_language``): Xenia la garde dans ``<données>/Xenia/xconfig.settings``, fichier binaire (réglages
internes de la Xbox 360), pas dans le fichier de configuration. L'octet de la langue est au décalage 2325: comparer deux
enregistrements (français puis anglais) montre ce seul octet qui change, de 4 à 1, sans somme de contrôle. Numéros des langues
de la Xbox 360: 1 anglais, 2 japonais, 3 allemand, 4 français, 5 espagnol, 6 italien, 7 coréen, 8 chinois traditionnel,
9 portugais, 10 chinois simplifié, 11 polonais, 12 russe (1, 2, 3 et 4 relevés sur le fichier, les autres suivent cet ordre).
L'octet n'est écrit que s'il contient déjà un numéro de langue valide.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from .base import Command, Context
from .standalone import Standalone

log = logging.getLogger(__name__)

# clé ES -> (valeurs permises, options de ligne de commande produites à partir de la valeur)
CHOICES: dict[str, tuple[frozenset[str], tuple[str, ...]]] = {
    "xenia_resolution": (frozenset({"1", "2", "3", "4"}), ("draw_resolution_scale_x", "draw_resolution_scale_y")),
    "xenia_vsync": (frozenset({"true", "false"}), ("vsync",)),
    "xenia_aa": (frozenset({"none", "fxaa", "fxaa_extreme"}), ("postprocess_antialiasing",)),
    "xenia_scaling": (frozenset({"bilinear", "cas", "fsr"}), ("postprocess_scaling_and_sharpening",)),
    "xenia_af": (frozenset({"0", "2", "3", "4", "5"}), ("anisotropic_override",)),
    "xenia_fps": (frozenset({"0", "30", "60"}), ("framerate_limit",)),
    "xenia_mute": (frozenset({"true", "false"}), ("mute",)),
    "xenia_apu": (frozenset({"any", "alsa", "sdl"}), ("apu",)),
}


LANGUAGE_OFFSET = 2325
LANGUAGES = frozenset(str(n) for n in range(1, 13))


def xconfig_file() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share") / "Xenia" / "xconfig.settings"


def set_console_language(path: Path, language: str) -> bool:
    """Écrit la langue dans ``xconfig.settings``; False quand le fichier ne convient pas ou que rien ne change."""
    if language not in LANGUAGES or not path.is_file():
        return False
    data = bytearray(path.read_bytes())
    if len(data) <= LANGUAGE_OFFSET or not 1 <= data[LANGUAGE_OFFSET] <= 12:
        log.warning("xenia: %s n'a pas la forme attendue, langue inchangée", path)
        return False
    if data[LANGUAGE_OFFSET] == int(language):
        return False
    data[LANGUAGE_OFFSET] = int(language)
    temporary = path.with_name(path.name + ".esne-tmp")
    temporary.write_bytes(bytes(data))
    temporary.chmod(path.stat().st_mode & 0o777)
    temporary.replace(path)
    return True


def video_options(ctx: Context) -> list[str]:
    options: list[str] = []
    for key, (allowed, names) in CHOICES.items():
        value = str(ctx.setting(key, "") or "").strip().lower()
        if not value:
            continue
        if value not in allowed:
            log.warning("valeur inconnue pour %s ignorée: %s", key, value)
            continue
        options += [f"--{name}={value}" for name in names]
    return options


class Xenia(Standalone):
    name = "xenia"

    def generate(self, ctx: Context) -> Command:
        command = super().generate(ctx)
        language = str(ctx.setting("xenia_language", "") or "").strip()
        if language and set_console_language(xconfig_file(), language):
            log.info("xenia: langue de la console %s", language)
        options = video_options(ctx)
        if options and command.argv:
            # le chemin du jeu reste le dernier argument
            command.argv[:] = [*command.argv[:-1], *options, command.argv[-1]]
        return command


GENERATOR = Xenia
