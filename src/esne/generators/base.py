from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Command:
    argv: list[str]
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None


@dataclass
class Context:
    system: str
    rom: str
    config: Any
    emulator: str = "libretro"
    core: str | None = None


class Generator:
    name: str = ""

    def generate(self, ctx: Context) -> Command:
        raise NotImplementedError

    def post_run(self, ctx: Context) -> None:
        pass
