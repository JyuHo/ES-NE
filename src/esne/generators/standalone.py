# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur générique pour les émulateurs autonomes (Dolphin, PCSX2, RPCS3, Cemu...).

Tout est décrit dans ``emulators.yml``::

    dolphin:
      binary: [dolphin-emu, "flatpak run org.DolphinEmu.dolphin-emu"]
      args: [-b, -e, "{rom}"]
      package: dolphin-emu          # indice affiché si le programme est introuvable
      env: {KEY: value}             # facultatif
      cwd: rom_dir                  # facultatif: lancer depuis le dossier de la rom

Variables d'``args`` et d'``env``: ``{rom}``, ``{rom_dir}``, ``{rom_name}``, ``{rom_text}`` (contenu du
fichier, ex. l'identifiant d'un jeu Steam), ``{system}``.
"""
from __future__ import annotations

import logging
import shlex
import shutil
from pathlib import Path

from .. import catalog
from ..errors import EMULATOR_MISSING, INVALID_CONFIG, UNKNOWN_EMULATOR, LaunchError
from .base import Command, Context, Generator

log = logging.getLogger(__name__)


def find_program(candidates, which=None) -> list[str] | None:
    which = which or shutil.which
    for candidate in candidates or []:
        parts = shlex.split(candidate)
        if parts and which(parts[0]):
            return [which(parts[0]), *parts[1:]]
    return None


def is_installed(emulator: str, user_dir: Path | None = None, which=None) -> bool:
    spec = catalog.emulator_info(emulator, user_dir)
    return bool(spec and "args" in spec and find_program(spec.get("binary"), which))


def _variables(ctx: Context) -> dict[str, str]:
    rom = Path(ctx.rom)
    text = ""
    try:
        if rom.is_file() and rom.stat().st_size < 4096:
            text = rom.read_text(encoding="utf-8", errors="ignore").strip()
    except OSError:
        pass
    return {"rom": str(rom), "rom_dir": str(rom.parent), "rom_name": rom.stem, "rom_text": text, "system": ctx.system}


def _expand(value, variables: dict[str, str]) -> str:
    try:
        return str(value).format(**variables)
    except (KeyError, IndexError, ValueError) as exc:
        raise LaunchError(INVALID_CONFIG, f"variable inconnue dans emulators.yml: {exc}") from exc


class Standalone(Generator):
    name = "standalone"
    external_hotkey = True  # ces émulateurs n'ont pas de raccourci manette: es-launcher le fournit

    def generate(self, ctx: Context) -> Command:
        spec = catalog.emulator_info(ctx.emulator)
        if not spec or "args" not in spec:
            raise LaunchError(UNKNOWN_EMULATOR, f"émulateur inconnu: '{ctx.emulator}'")

        binary = find_program(spec.get("binary"))
        if binary is None:
            hint = f" (installez {spec['package']})" if spec.get("package") else ""
            raise LaunchError(EMULATOR_MISSING, f"{ctx.emulator} est introuvable{hint}")

        variables = _variables(ctx)
        argv = [*binary, *(_expand(arg, variables) for arg in spec.get("args") or [])]
        env = {str(k): _expand(v, variables) for k, v in (spec.get("env") or {}).items()}
        cwd = variables["rom_dir"] if spec.get("cwd") == "rom_dir" else None
        return Command(argv=argv, env=env, cwd=cwd)


GENERATOR = Standalone
