# SPDX-License-Identifier: GPL-3.0-or-later
"""es-launcher: lance un jeu à la demande d'EmulationStation.

Ligne de commande (celle de Batocera, ES la construit à partir de la balise <command>):

  es-launcher [-p1index N -p1guid G -p1path P -p1name NOM -p1nbbuttons N -p1nbhats N -p1nbaxes N ...]
              -system SYSTÈME -rom CHEMIN [-emulator E] [-core C] [-gameinfoxml F] [-systemname NOM]
              [-netplaymode ...] [-state_slot N] [-state_filename F] [-autosave 0|1] [-monitor N]

Code de sortie: 0 si le jeu s'est terminé normalement, sinon un code 2xx compris d'ES (voir errors.py).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import paths
from .config import Config
from .errors import BAD_ARGUMENTS, LaunchError
from .generators.base import Context, Controller
from .launcher import launch, report, setup_logging

MAX_PLAYERS = 8
_PLAYER_FIELDS = ("index", "guid", "path", "name", "nbbuttons", "nbhats", "nbaxes")
_INT_FIELDS = {"index", "nbbuttons", "nbhats", "nbaxes"}

# Options d'ES acceptées mais pas encore interprétées: conservées dans Context.extras
_EXTRA_OPTIONS = (
    "netplaymode", "netplayport", "netplayip", "netplaypass", "netplaysession",
    "state_slot", "state_filename", "state_file", "autosave", "monitor", "lightgun",
)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise LaunchError(BAD_ARGUMENTS, f"arguments invalides: {message}")


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="es-launcher", allow_abbrev=False)

    # nargs="?": ES remplace une variable inconnue par une chaîne vide (-emulator -core X, -gameinfoxml "")
    def option(name):
        parser.add_argument(f"-{name}", nargs="?", const="", default=None)

    for name in ("system", "rom", "emulator", "core", "gameinfoxml", "systemname", *_EXTRA_OPTIONS):
        option(name)

    for player in range(1, MAX_PLAYERS + 1):
        for field_name in _PLAYER_FIELDS:
            option(f"p{player}{field_name}")

    return parser


def parse_controllers(values: dict) -> list[Controller]:
    controllers = []
    for player in range(1, MAX_PLAYERS + 1):
        raw = {f: values.get(f"p{player}{f}") for f in _PLAYER_FIELDS}
        if all(v in (None, "") for v in raw.values()):
            continue
        data = {}
        for field_name, value in raw.items():
            if value in (None, ""):
                continue
            if field_name in _INT_FIELDS:
                try:
                    value = int(value)
                except ValueError as exc:
                    raise LaunchError(BAD_ARGUMENTS, f"-p{player}{field_name}: entier attendu, reçu '{value}'") from exc
            data[field_name] = value
        controllers.append(Controller(player=player, **data))
    return controllers


def build_context(argv: list[str], cfg: Config | None = None) -> Context:
    values = vars(build_parser().parse_args(argv))

    system, rom = values.get("system"), values.get("rom")
    if not system or not rom:
        raise LaunchError(BAD_ARGUMENTS, "-system et -rom sont obligatoires")

    cfg = cfg if cfg is not None else Config.load(paths.conf_file())
    # même nettoyage qu'ES (FileData::getConfigurationName): "=" et "#" sont retirés du nom du fichier
    rom_name = Path(rom).name.replace("=", "").replace("#", "")

    return Context(
        system=system,
        rom=rom,
        config=_Scoped(cfg, system, rom_name),
        emulator=values.get("emulator") or "",   # résolu par le lanceur (config, puis catalogue)
        core=values.get("core") or None,
        system_name=values.get("systemname") or system,
        controllers=parse_controllers(values),
        extras={k: values[k] for k in _EXTRA_OPTIONS if values.get(k) not in (None, "")},
    )


def main(argv=None) -> int:
    setup_logging()
    try:
        return launch(build_context(argv if argv is not None else sys.argv[1:]))
    except LaunchError as error:
        return report(error)


class _Scoped:
    """Configuration liée à un système et à une ROM."""

    def __init__(self, cfg: Config, system: str, rom: str):
        self.cfg, self.system, self.rom = cfg, system, rom

    def get(self, key, system=None, default=None):
        return self.cfg.get(key, self.system, self.rom, default)


if __name__ == "__main__":
    sys.exit(main())
