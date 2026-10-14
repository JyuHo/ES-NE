# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur Xenia Canary (Xbox 360): ligne de commande de ``emulators.yml`` + réglages vidéo choisis dans ES.

Les réglages sont passés en options de ligne de commande (``--nom=valeur``, mêmes noms que dans
``~/.local/share/Xenia/xenia-canary.config.toml``): le fichier de l'utilisateur n'est pas modifié, et un réglage non choisi
dans ES garde la valeur de ce fichier. Valeurs permises relevées dans les commentaires de ce fichier.

Options ES (``<système>.<clé>``): ``xenia_resolution`` (échelle de rendu 1 à 4), ``xenia_vsync`` (true, false),
``xenia_aa`` (none, fxaa, fxaa_extreme), ``xenia_scaling`` (bilinear, cas, fsr), ``xenia_af`` (filtrage anisotrope: 0, 2 à 5),
``xenia_fps`` (limite d'images par seconde, 0 = illimité).
"""
from __future__ import annotations

import logging

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
}


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
        options = video_options(ctx)
        if options and command.argv:
            # le chemin du jeu reste le dernier argument
            command.argv[:] = [*command.argv[:-1], *options, command.argv[-1]]
        return command


GENERATOR = Xenia
