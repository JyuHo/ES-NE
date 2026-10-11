# SPDX-License-Identifier: GPL-3.0-or-later
"""esctl config lsoutputs

Le frontend appelle ``batocera-config lsoutputs`` pour lister les sorties vidéo. Seul ce verbe
est fourni: les autres verbes de ``batocera-config`` (stockage, mot de passe root, overscan...)
n'ont pas d'équivalent ici et les menus correspondants sont masqués.
"""
from __future__ import annotations

import sys

from . import resolution

NAME = "config"


def available() -> bool:
    return resolution.available()


def run(args: list[str]) -> int:
    if args != ["lsoutputs"]:
        print("usage: esctl config lsoutputs", file=sys.stderr)
        return 2

    backend, outputs = resolution.read_outputs()
    if backend is None:
        return 1
    for output in outputs:
        print(output.name)
    return 0
