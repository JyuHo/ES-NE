# SPDX-License-Identifier: GPL-3.0-or-later
"""esctl timezone get | detect | set "<Zone/Ville>"

``get`` et ``detect`` affichent le fuseau actuel (timedatectl, sinon le lien /etc/localtime).
``set`` passe par ``timedatectl set-timezone``: sur une session locale active polkit peut demander un mot de passe;
sans règle polkit adaptée l'ordre échoue avec un message explicite (voir docs).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

NAME = "timezone"
ZONEINFO = Path("/usr/share/zoneinfo")


def available() -> bool:
    return shutil.which("timedatectl") is not None or Path("/etc/localtime").is_symlink()


def current(run=subprocess.run, localtime: Path = Path("/etc/localtime")) -> str:
    if shutil.which("timedatectl"):
        try:
            result = run(["timedatectl", "show", "-p", "Timezone", "--value"], capture_output=True, text=True, timeout=10)
            value = (result.stdout or "").strip()
            if result.returncode == 0 and value:
                return value
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        target = str(localtime.resolve())
        marker = "zoneinfo/"
        if marker in target:
            return target.split(marker, 1)[1]
    except OSError:
        pass
    return ""


def valid(zone: str, zoneinfo: Path = ZONEINFO) -> bool:
    if not zone or zone.startswith("/") or ".." in zone.split("/"):
        return False
    return (zoneinfo / zone).is_file()


def set_timezone(zone: str, run=subprocess.run, zoneinfo: Path = ZONEINFO) -> int:
    if not valid(zone, zoneinfo):
        print(f"esctl timezone: fuseau inconnu: {zone}", file=sys.stderr)
        return 1
    try:
        result = run(["timedatectl", "set-timezone", zone], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"esctl timezone: timedatectl a échoué: {exc}", file=sys.stderr)
        return 1
    if result.returncode != 0:
        detail = (result.stderr or "").strip() or "échec"
        print(f"esctl timezone: impossible de changer le fuseau ({detail}). Une règle polkit est nécessaire "
              "pour org.freedesktop.timedate1.set-timezone.", file=sys.stderr)
        return result.returncode
    return 0


def run(args: list[str]) -> int:
    action = args[0] if args else "get"
    if action in ("get", "detect"):
        zone = current()
        if not zone:
            return 1
        print(zone)
        return 0
    if action == "set" and len(args) == 2:
        return set_timezone(args[1])
    print('usage: esctl timezone get | detect | set "<Zone/Ville>"', file=sys.stderr)
    return 2
