# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur Redream (Dreamcast): ligne de commande de ``emulators.yml`` + réglages choisis dans ES dans ``redream.cfg``.

``redream.cfg`` est un fichier ``clé=valeur``. Les réglages ES (``redream_*``) sont écrits quand ils sont définis; un réglage
non choisi garde la valeur de Redream. Noms de clés relevés sur un ``redream.cfg`` réel (région, langue, câble, standard TV,
format d'image, résolution, VSync); les valeurs permises sont celles de l'interface de Redream. Le fichier n'est modifié que
s'il existe (Redream le crée à son premier lancement), cherché dans le dossier de données XDG, le dossier de configuration XDG,
``~/.redream`` puis à côté du binaire.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from .base import Command, Context
from .standalone import Standalone

log = logging.getLogger(__name__)

# clé ES -> (clé du redream.cfg, valeurs permises)
SETTINGS: dict[str, tuple[str, frozenset[str]]] = {
    "redream_region": ("region", frozenset({"japan", "usa", "europe"})),
    "redream_language": ("language", frozenset({"japanese", "english", "german", "french", "spanish", "italian"})),
    "redream_broadcast": ("broadcast", frozenset({"ntsc", "pal", "pal_m", "pal_n"})),
    "redream_renderer": ("renderer", frozenset({"vk_lle", "gl_lle", "gl_hle_perpixel", "gl_hle_perstrip"})),
    "redream_cable": ("cable", frozenset({"composite", "rgb", "vga"})),
    "redream_aspect": ("aspect", frozenset({"4:3", "16:9", "stretch"})),
    "redream_res": ("res", frozenset({"1", "2", "3", "4", "5", "6"})),
    "redream_vsync": ("vsync", frozenset({"0", "1"})),
    "redream_frameskip": ("frameskip", frozenset({"0", "1"})),  # 0 off, 1 auto
    "redream_framerate": ("framerate", frozenset({"0", "1"})),  # compteur: 0 off, 1 vblanks par seconde
}


def config_candidates(binary: str | None = None) -> list[Path]:
    home = Path.home()
    data = Path(os.environ.get("XDG_DATA_HOME") or home / ".local/share")
    config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    found = [data / "redream" / "redream.cfg", config / "redream" / "redream.cfg", home / ".redream" / "redream.cfg"]
    if binary:
        found.append(Path(binary).resolve().parent / "redream.cfg")
    return found


def find_config(binary: str | None = None) -> Path | None:
    return next((path for path in config_candidates(binary) if path.is_file()), None)


def chosen(ctx: Context) -> dict[str, str]:
    values: dict[str, str] = {}
    for name, (key, allowed) in SETTINGS.items():
        value = str(ctx.setting(name, "") or "").strip().lower()
        if not value:
            continue
        if value not in allowed:
            log.warning("valeur inconnue pour %s ignorée: %s", name, value)
            continue
        values[key] = value
    return values


def apply(cfg: Path, values: dict[str, str]) -> bool:
    if not values or not cfg.is_file():
        return False
    lines = cfg.read_text(encoding="utf-8").splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    changed = False
    for key, value in values.items():
        wanted = f"{key}="
        for i, line in enumerate(lines):
            if line.startswith(wanted):
                if line.rstrip("\n") != f"{wanted}{value}":
                    lines[i] = f"{wanted}{value}\n"
                    changed = True
                break
        else:
            lines.append(f"{wanted}{value}\n")
            changed = True
    if changed:
        temporary = cfg.with_name(cfg.name + ".esne-tmp")
        temporary.write_text("".join(lines), encoding="utf-8")
        temporary.replace(cfg)
    return changed


class Redream(Standalone):
    name = "redream"

    def generate(self, ctx: Context) -> Command:
        command = super().generate(ctx)
        values = chosen(ctx)
        if values:
            cfg = find_config(command.argv[0] if command.argv else None)
            if cfg is None:
                log.info("redream: redream.cfg introuvable, lance Redream une fois à la main pour le créer")
            elif apply(cfg, values):
                log.info("redream: réglages %s", ", ".join(f"{k}={v}" for k, v in values.items()))
        return command


GENERATOR = Redream
