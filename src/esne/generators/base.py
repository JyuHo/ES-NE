# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Command:
    argv: list[str]
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None


@dataclass
class Controller:
    """Manette telle que la transmet ES (-p<N>index, -p<N>guid...). ``player`` commence à 1."""
    player: int
    index: int | None = None
    guid: str = ""
    path: str = ""
    name: str = ""
    nbbuttons: int | None = None
    nbhats: int | None = None
    nbaxes: int | None = None


@dataclass
class Context:
    system: str
    rom: str
    config: Any
    emulator: str = "libretro"
    core: str | None = None
    system_name: str = ""
    controllers: list[Controller] = field(default_factory=list)
    extras: dict[str, str] = field(default_factory=dict)  # options d'ES non interprétées (netplay, états...)

    def setting(self, key: str, default=None):
        """Réglage résolu en couches: <système>["rom"].clé > <système>.clé > global.clé."""
        return self.config.get(key, default=default)


class Generator:
    name: str = ""

    def generate(self, ctx: Context) -> Command:
        raise NotImplementedError

    def post_run(self, ctx: Context) -> None:
        pass
