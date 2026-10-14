# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur xemu (Xbox): ligne de commande de ``emulators.yml`` + fichiers système et plein écran dans ``xemu.toml``.

* Fichiers système: les fichiers du dossier ``<bios>/xbox`` sont reconnus à leur **taille**, pas à leur nom: MCPX boot ROM
  (512 octets), EEPROM (256 octets), flash/BIOS (256 Kio, 512 Kio ou 1 Mio), disque dur ``*.qcow2``. Seules les clés
  ``bootrom_path``, ``flashrom_path``, ``eeprom_path`` et ``hdd_path`` de ``[sys.files]`` sont réécrites, et seulement
  celles qui existent déjà dans ``xemu.toml``.
* Plein écran au démarrage, sans écran d'accueil ni vérification de mise à jour.
* Manettes (``xemu_autoconfig=0`` pour garder les tiennes): la n-ième manette d'ES va sur le port n (``port1``...).

Règle générale: ``xemu.toml`` n'est modifié que s'il existe (xemu l'écrit au premier lancement avec toutes ses clés), et
une clé absente du fichier est ignorée plutôt qu'inventée. Écrit de mémoire pour xemu 0.8, à valider sur une machine.
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

from .. import paths
from .base import Command, Context
from .standalone import Standalone

log = logging.getLogger(__name__)

MAX_PLAYERS = 4
FLASH_SIZES = (262144, 524288, 1048576)
SECTION = re.compile(r"^\s*\[([^\[\]]+)\]\s*(#.*)?$")
GUID = re.compile(r"^[0-9a-fA-F]{32}$")


def config_file(argv: list[str] | None = None) -> Path:
    if argv and any("flatpak" in part for part in argv[:2]):
        return Path.home() / ".var/app/app.xemu.xemu/data/xemu/xemu/xemu.toml"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share") / "xemu" / "xemu" / "xemu.toml"


def find_system_files(directory: Path) -> dict[str, str]:
    """{bootrom_path, flashrom_path, eeprom_path, hdd_path} reconnus dans ``directory`` (récursif d'un niveau)."""
    found: dict[str, str] = {}
    if not directory.is_dir():
        return found
    candidates = sorted(p for p in [*directory.iterdir(), *directory.glob("*/*")] if p.is_file())
    for path in candidates:
        if path.suffix.lower() == ".qcow2":
            found.setdefault("hdd_path", str(path))
            continue
        size = path.stat().st_size
        if size == 512:
            found.setdefault("bootrom_path", str(path))
        elif size == 256:
            found.setdefault("eeprom_path", str(path))
        elif size in FLASH_SIZES:
            found.setdefault("flashrom_path", str(path))
    return found


def toml_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)  # chaîne TOML « basique »: les guillemets et antislashs sont échappés


def set_existing(lines: list[str], section: str, key: str, value) -> bool:
    """Remplace ``key`` dans ``[section]`` s'il y existe déjà. Renvoie False si la clé est absente."""
    current = ""
    for index, line in enumerate(lines):
        header = SECTION.match(line)
        if header:
            current = header.group(1).strip()
            continue
        if current == section and re.match(rf"^\s*{re.escape(key)}\s*=", line):
            lines[index] = f"{key} = {toml_value(value)}\n"
            return True
    return False


def apply(lines: list[str], ctx: Context, bios: Path) -> list[str]:
    wanted = [("sys.files", key, value) for key, value in find_system_files(bios).items()]
    wanted += [("display.window", "fullscreen_on_startup", True), ("general", "show_welcome", False),
               ("general.updates", "check", False)]
    if str(ctx.setting("xemu_autoconfig", "1")) != "0":
        for number, pad in enumerate(ctx.controllers[:MAX_PLAYERS], start=1):
            if GUID.match(pad.guid or ""):
                wanted += [("input.bindings", f"port{number}", pad.guid), ("input.bindings", f"port{number}_driver", "usb-xbox-gamepad")]
    for section, key, value in wanted:
        if not set_existing(lines, section, key, value):
            log.info("xemu: clé %s.%s absente de xemu.toml, ignorée", section, key)
    return lines


def configure(toml: Path, ctx: Context, bios: Path | None = None) -> bool:
    if not toml.is_file():
        return False
    lines = toml.read_text(encoding="utf-8").splitlines(keepends=True)
    new = apply(list(lines), ctx, bios or paths.bios_dir() / "xbox")
    if new == lines:
        return True
    temporary = toml.with_suffix(".toml.esne-tmp")
    temporary.write_text("".join(new), encoding="utf-8")
    temporary.replace(toml)
    return True


class Xemu(Standalone):
    name = "xemu"

    def generate(self, ctx: Context) -> Command:
        command = super().generate(ctx)
        if not configure(config_file(command.argv), ctx):
            log.info("xemu: xemu.toml introuvable, lance xemu une fois à la main pour le créer (BIOS dans %s)", paths.bios_dir() / "xbox")
        return command


GENERATOR = Xemu
