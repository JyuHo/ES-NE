# SPDX-License-Identifier: GPL-3.0-or-later
"""esctl systems [--filter <système>]

Remplace ``batocera-systems``: état des BIOS de chaque système. Une ligne ``> <système>`` puis une ligne par fichier:
``<statut> <md5> <chemin>``, statut ``OK``, ``MISSING`` (absent) ou ``INVALID`` (somme MD5 différente).
Le catalogue est ``data/bios.yml`` (complété par ``<config>/bios.yml``); les fichiers sont cherchés dans ``<data>/bios``.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from ... import catalog, paths

NAME = "systems"


def available() -> bool:
    return True


def entries(user_dir: Path | None = None) -> dict:
    return catalog.load_data("bios.yml", user_dir)


def md5_of(path: Path) -> str:
    digest = hashlib.md5()  # noqa: S324 (somme d'identification, pas de sécurité)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def check(item: dict, bios: Path) -> tuple[str, str, str]:
    """(statut, md5 attendu, chemin) d'un fichier du catalogue."""
    name = str(item["file"])
    expected = item.get("md5")
    accepted = [str(value).lower() for value in (expected if isinstance(expected, list) else [expected] if expected else [])]
    shown = accepted[0] if accepted else "-"
    target = bios / name
    if not target.is_file():
        return "MISSING", shown, str(target)
    if accepted:
        try:
            if md5_of(target) not in accepted:
                return "INVALID", shown, str(target)
        except OSError:
            return "INVALID", shown, str(target)
    return "OK", shown, str(target)


def report(system_filter: str | None = None, data: dict | None = None, bios: Path | None = None) -> list[str]:
    data = entries() if data is None else data
    bios = bios or paths.bios_dir()
    lines = []
    for system in sorted(data):
        if system_filter and system != system_filter:
            continue
        lines.append(f"> {system}")
        lines.extend(" ".join(check(item, bios)) for item in data[system] or [])
    return lines


def run(args: list[str]) -> int:
    system_filter = None
    if args[:1] == ["--filter"] and len(args) == 2:
        system_filter = args[1]
    elif args:
        print("usage: esctl systems [--filter <système>]", file=sys.stderr)
        return 2
    lines = report(system_filter)
    if lines:
        print("\n".join(lines))
    return 0
