# SPDX-License-Identifier: GPL-3.0-or-later
"""esctl keyboard list-layouts | list-variants <disposition> | get | set <disposition> [<variante>|none]

Remplace ``batocera-keyboard``. Les listes viennent de ``localectl`` (``list-x11-keymap-layouts``, ``list-x11-keymap-variants``);
chaque ligne est ``<code> <libellé>`` (le frontend sépare au premier espace). ``set`` passe par
``localectl set-x11-keymap`` (polkit: org.freedesktop.locale1.set-keyboard, autorisé par la règle d'ES-NE); la nouvelle
disposition s'applique à la prochaine ouverture de session.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys

NAME = "keyboard"
CODE = re.compile(r"^[A-Za-z0-9_+-]+$")


def available() -> bool:
    return shutil.which("localectl") is not None


def _lines(args: list[str], run=subprocess.run) -> list[str]:
    result = run(["localectl", *args], capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        return []
    return [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]


def current(run=subprocess.run) -> tuple[str, str]:
    layout = variant = ""
    for line in _lines(["status"], run):
        key, _, value = line.partition(":")
        if key.strip() == "X11 Layout":
            layout = value.strip()
        elif key.strip() == "X11 Variant":
            variant = value.strip()
    return layout if layout != "n/a" else "", variant if variant != "n/a" else ""


def run(args: list[str], runner=subprocess.run) -> int:
    command = args[0] if args else ""
    if command == "list-layouts" and len(args) == 1:
        for code in _lines(["list-x11-keymap-layouts"], runner):
            print(f"{code} {code}")
        return 0
    if command == "list-variants" and len(args) == 2 and CODE.match(args[1]):
        for code in _lines(["list-x11-keymap-variants", args[1]], runner):
            print(f"{code} {code}")
        return 0
    if command == "get" and len(args) == 1:
        layout, variant = current(runner)
        print(f"{layout} {variant or 'none'}".strip())
        return 0
    if command == "set" and len(args) in (2, 3) and all(CODE.match(a) for a in args[1:]):
        variant = "" if len(args) == 2 or args[2] == "none" else args[2]
        try:
            result = runner(["localectl", "set-x11-keymap", args[1], "", variant], capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError) as exc:
            print(f"esctl keyboard: localectl a échoué: {exc}", file=sys.stderr)
            return 1
        if result.returncode != 0:
            detail = (result.stderr or "").strip() or "échec"
            print(f"esctl keyboard: impossible de changer la disposition ({detail}). Une règle polkit est nécessaire "
                  "pour org.freedesktop.locale1.set-keyboard.", file=sys.stderr)
            return 1
        return 0
    print("usage: esctl keyboard list-layouts | list-variants <disposition> | get | set <disposition> [<variante>]", file=sys.stderr)
    return 2
