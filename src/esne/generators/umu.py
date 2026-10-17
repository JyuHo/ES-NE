# SPDX-License-Identifier: GPL-3.0-or-later
"""Générateur umu (jeux Windows via umu-launcher + Proton): ``umu-run`` + réglages choisis dans ES, passés par l'environnement.

Rien n'est écrit sur le disque en dehors du préfixe de chaque jeu: tout passe par des variables d'environnement (``PROTONPATH``,
``WINEPREFIX``, ``GAMEID``, ``PROTON_*``, ``WINE_FULLSCREEN_FSR*``, ``DXVK_FRAME_RATE``, ``MANGOHUD``) et, pour Gamemode, par un
programme intercalé (``gamemoderun``). Un réglage non choisi garde le comportement par défaut de umu/Proton.

Préfixe: un par jeu (``<données>/saves/windows/<nom du jeu>``, le plus sûr: DLL et bibliothèques ne se mélangent pas) ou un
préfixe partagé (``umu_prefix=shared``). Le nom du jeu (nom du fichier sans extension, nettoyé) sert aussi de ``GAMEID``.
"""
from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path

from .. import paths
from .base import Command, Context
from .standalone import Standalone

log = logging.getLogger(__name__)

DEFAULT_PROTON = "GE-Proton"  # umu télécharge et tient à jour la dernière version de GE-Proton
PROTON_NAME = re.compile(r"^[\w.\-]+$")  # GE-Proton, UMU-Latest, GE-Proton9-27 (dossier de ~/.local/share/Steam/compatibilitytools.d)
DESKTOP = re.compile(r"^\d{3,5}x\d{3,5}$")

# clé ES -> valeurs permises
CHOICES: dict[str, frozenset[str]] = {
    "umu_prefix": frozenset({"game", "shared"}),
    "umu_d3d": frozenset({"default", "wined3d"}),
    "umu_sync": frozenset({"auto", "esync", "fsync", "none"}),
    "umu_fsr": frozenset({"0", "1"}),
    "umu_fsr_strength": frozenset({"0", "1", "2", "3", "4", "5"}),
    "umu_mangohud": frozenset({"0", "1"}),
    "umu_gamemode": frozenset({"0", "1"}),
}


def slug(name: str) -> str:
    """Nom de jeu utilisable comme dossier et comme GAMEID."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "game"


def _value(ctx: Context, key: str) -> str:
    value = str(ctx.setting(key, "") or "").strip()
    allowed = CHOICES.get(key)
    if allowed is not None:
        value = value.lower()
        if value and value not in allowed:
            log.warning("valeur inconnue pour %s ignorée: %s", key, value)
            return ""
    return value


def environment(ctx: Context, game: str) -> dict[str, str]:
    """Variables d'environnement déduites des réglages ES (les réglages vides ne produisent rien)."""
    env: dict[str, str] = {"GAMEID": game}

    proton = _value(ctx, "umu_proton") or DEFAULT_PROTON
    if PROTON_NAME.match(proton):
        env["PROTONPATH"] = proton
    else:
        log.warning("umu_proton ignoré (nom invalide): %s", proton)
        env["PROTONPATH"] = DEFAULT_PROTON

    prefix = paths.data_dir() / "saves" / "windows" / ("shared" if _value(ctx, "umu_prefix") == "shared" else game)
    env["WINEPREFIX"] = str(prefix)

    if _value(ctx, "umu_d3d") == "wined3d":
        env["PROTON_USE_WINED3D"] = "1"  # sinon DXVK (D3D9/10/11) et VKD3D-Proton (D3D12), les valeurs par défaut de Proton

    sync = _value(ctx, "umu_sync")
    if sync in ("esync", "none"):
        env["PROTON_NO_FSYNC"] = "1"
    if sync in ("fsync", "none"):
        env["PROTON_NO_ESYNC"] = "1"

    if _value(ctx, "umu_fsr") == "1":
        env["WINE_FULLSCREEN_FSR"] = "1"
        strength = _value(ctx, "umu_fsr_strength")
        if strength:
            env["WINE_FULLSCREEN_FSR_STRENGTH"] = strength  # 0 = plus net, 5 = plus doux

    if _value(ctx, "umu_mangohud") == "1":
        env["MANGOHUD"] = "1"

    fps = _value(ctx, "umu_fps")
    if fps.isdigit() and 0 < int(fps) <= 1000:
        env["DXVK_FRAME_RATE"] = fps
    return env


class Umu(Standalone):
    name = "umu"

    def generate(self, ctx: Context) -> Command:
        command = super().generate(ctx)
        game = slug(Path(ctx.rom).stem)
        command.env.update(environment(ctx, game))

        desktop = _value(ctx, "umu_vdesktop")
        if desktop:
            if DESKTOP.match(desktop) and command.argv:
                # bureau virtuel de Wine: umu-run explorer /desktop=<nom>,<LxH> <jeu> (lancé depuis le dossier du jeu)
                command.argv = [command.argv[0], "explorer", f"/desktop=esne,{desktop}", Path(ctx.rom).name]
            else:
                log.warning("umu_vdesktop ignoré (format LxH attendu): %s", desktop)

        if _value(ctx, "umu_mangohud") == "1" and not shutil.which("mangohud"):
            log.warning("umu: MangoHud demandé mais mangohud est introuvable (installez mangohud)")
        if _value(ctx, "umu_gamemode") == "1":
            gamemode = shutil.which("gamemoderun")
            if gamemode:
                command.argv = [gamemode, *command.argv]
            else:
                log.warning("umu: Gamemode demandé mais gamemoderun est introuvable (installez gamemode)")

        log.info("umu: %s (préfixe %s, Proton %s)", game, command.env["WINEPREFIX"], command.env["PROTONPATH"])
        return command


GENERATOR = Umu
