# SPDX-License-Identifier: GPL-3.0-or-later
"""Codes de sortie d'es-launcher.

ES (FileData::getMessageFromExitCode) affiche un message fixe pour 200-205. Pour 250 et 299 il
affiche le contenu de /tmp/launch_error.log.
"""
from __future__ import annotations

import os
from pathlib import Path

EMULATOR_EXITED = 200      # l'émulateur s'est terminé anormalement
BAD_ARGUMENTS = 201        # ligne de commande invalide
INVALID_CONFIG = 202       # configuration invalide
UNKNOWN_EMULATOR = 203
EMULATOR_MISSING = 204
CORE_MISSING = 205
OTHER_ERROR = 299          # message libre dans LAUNCH_ERROR_FILE


def launch_error_file() -> Path:
    # ES lit ce chemin en dur (FileData.cpp)
    return Path(os.environ.get("ESNE_LAUNCH_ERROR_FILE") or "/tmp/launch_error.log")


class LaunchError(Exception):
    """Erreur de lancement: ``code`` est renvoyé à ES, ``message`` va dans le journal."""

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
