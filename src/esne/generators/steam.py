# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur Steam: ligne de commande de ``emulators.yml`` (``esne-steam-run`` autour de ``steam``).

Par défaut, le client Steam que ES-NE a ouvert pour lancer le jeu est refermé à la fin de la partie (il ne reste pas en
arrière-plan et ne repasse pas au premier plan); un Steam déjà ouvert avant le lancement n'est jamais fermé.
``steam_keep_open=1`` garde le client ouvert (lancements suivants plus rapides).
"""
from __future__ import annotations

from .base import Command, Context
from .standalone import Standalone


class Steam(Standalone):
    name = "steam"

    def generate(self, ctx: Context) -> Command:
        command = super().generate(ctx)
        if str(ctx.setting("steam_keep_open", "0")) != "1" and command.argv and command.argv[0] == "esne-steam-run":
            command.argv.insert(1, "--close")
        return command


GENERATOR = Steam
