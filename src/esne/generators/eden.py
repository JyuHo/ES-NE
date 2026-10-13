# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur Eden (Switch): ligne de commande de ``emulators.yml`` + manettes dans ``qt-config.ini``.

Eden (fork de yuzu) enregistre chaque manette physique avec des index bruts SDL (boutons, axes, croix) propres au modèle de
manette, et un GUID SDL qui n'est pas celui qu'ES calcule. ES-NE ne peut donc pas deviner la disposition seul.
Il s'appuie sur ce que tu as configuré dans Eden pour le joueur 1 (Configurer > Contrôles):

* ce mappage (boutons, axes) devient le modèle: pour chaque manette du **même modèle** (fabricant + produit) transmise par
  ES, le joueur correspondant reçoit ce mappage avec le GUID que voit Eden (celui d'ES, CRC du nom à zéro), le bon ``port``
  (n-ième manette de même GUID) et passe à « connecté »;
* une manette d'un autre modèle n'est pas touchée (à configurer à la main dans Eden);
* ``eden_autoconfig=0`` désactive tout ça.

Le fichier n'est modifié que s'il existe déjà (Eden le crée à son premier lancement) et seules les lignes
``player_N_...`` de la section ``[Controls]`` sont réécrites; le reste est conservé tel quel.
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path

from .base import Command, Context
from .standalone import Standalone

log = logging.getLogger(__name__)

MAX_PLAYERS = 8
MAPPING_KEY = re.compile(r"^player_0_(button_\w+|lstick|rstick)$")
SKIP = ("button_screenshot",)  # inutile à recopier (pas de bouton physique)


def config_dir(argv: list[str] | None = None) -> Path:
    if argv and any("flatpak" in part for part in argv[:2]):
        return Path.home() / ".var/app/dev.eden_emu.eden/config/eden"
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "eden"


def _section_bounds(lines: list[str], name: str) -> tuple[int, int] | None:
    start = next((i for i, line in enumerate(lines) if line.strip() == f"[{name}]"), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("[")), len(lines))
    return start, end


def read_template(lines: list[str]) -> tuple[str, dict[str, str]] | None:
    """(GUID, {clé sans préfixe: valeur}) du joueur 1 s'il utilise le moteur SDL, sinon None."""
    bounds = _section_bounds(lines, "Controls")
    if bounds is None:
        return None
    template, guid = {}, ""
    for line in lines[bounds[0] + 1:bounds[1]]:
        key, _, value = line.rstrip("\n").partition("=")
        match = MAPPING_KEY.match(key)
        if not match or not value.startswith('"engine:sdl'):
            continue
        found = re.search(r"guid:([0-9a-fA-F]{32})", value)
        if found and match.group(1) not in SKIP:
            guid = found.group(1)
            template[match.group(1)] = value.strip('"')
    return (guid, template) if guid and template else None


def eden_guid(es_guid: str) -> str:
    """GUID vu par Eden: celui d'ES avec le CRC du nom (caractères 5 à 8) mis à zéro.

    Constaté sur une PS4: ES ``03008fe54c05...6800`` correspond à ``03000000 4c05...6800`` dans le qt-config.ini d'Eden.
    """
    return es_guid[:4] + "0000" + es_guid[8:]


def instantiate(value: str, guid: str, port: int) -> str:
    value = re.sub(r"guid:[0-9a-fA-F]{32}", f"guid:{guid}", value)
    return re.sub(r"port:\d+", f"port:{port}", value)


def set_keys(lines: list[str], keys: dict[str, str]) -> list[str]:
    """Remplace ou ajoute ``clé\\default=false`` + ``clé=valeur`` dans [Controls]."""
    bounds = _section_bounds(lines, "Controls")
    start, end = bounds
    body = lines[start + 1:end]
    for key, value in keys.items():
        quoted = f'"{value}"' if value not in ("true", "false", "0") and not value.isdigit() else value
        for suffix, new in ((r"\default", "false"), ("", quoted)):
            wanted = f"{key}{suffix}="
            for i, line in enumerate(body):
                if line.startswith(wanted):
                    body[i] = f"{wanted}{new}\n"
                    break
            else:
                body.append(f"{wanted}{new}\n")
    return lines[:start + 1] + body + lines[end:]


def configure(ini: Path, ctx: Context) -> bool:
    if not ini.is_file() or str(ctx.setting("eden_autoconfig", "1")) == "0":
        return False
    lines = ini.read_text(encoding="utf-8").splitlines(keepends=True)
    template = read_template(lines)
    if template is None:
        log.info("eden: aucun mappage SDL pour le joueur 1 dans qt-config.ini, configure la manette dans Eden une fois")
        return False
    template_guid, mapping = template
    seen = 0
    changed = False
    for player, pad in enumerate(ctx.controllers[:MAX_PLAYERS]):
        if pad.guid[8:24] != template_guid[8:24]:
            log.info("eden: manette %d (%s) d'un autre modèle que le joueur 1, à configurer dans Eden", player + 1, pad.name)
            continue
        keys = {f"player_{player}_{name}": instantiate(value, eden_guid(pad.guid), seen) for name, value in mapping.items()}
        keys[f"player_{player}_connected"] = "true"
        lines = set_keys(lines, keys)
        seen += 1
        changed = True
    if changed:
        temporary = ini.with_suffix(".ini.esne-tmp")
        temporary.write_text("".join(lines), encoding="utf-8")
        temporary.replace(ini)
        log.info("eden: %d manette(s) configurée(s)", seen)
    return changed


class Eden(Standalone):
    name = "eden"

    def generate(self, ctx: Context) -> Command:
        command = super().generate(ctx)
        if not configure(config_dir(command.argv) / "qt-config.ini", ctx):
            log.info("eden: manettes laissées telles quelles")
        return command


GENERATOR = Eden
