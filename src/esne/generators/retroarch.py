import shutil
from pathlib import Path
from .base import Command, Context, Generator

CORE_DIRS = [Path("/usr/lib/libretro"), Path.home() / ".config/retroarch/cores"]


def find_core(core: str) -> Path | None:
    for d in CORE_DIRS:
        p = d / f"{core}_libretro.so"
        if p.exists():
            return p
    return None


class RetroArch(Generator):
    name = "libretro"

    def generate(self, ctx: Context) -> Command:
        core = ctx.core or ctx.config.get("core", ctx.system)
        if not core:
            raise SystemExit(f"Aucun core défini pour {ctx.system}")
        core_path = find_core(core)
        if core_path is None:
            raise SystemExit(f"Core introuvable: {core}")
        binary = shutil.which("retroarch") or "retroarch"
        return Command(argv=[binary, "-L", str(core_path), ctx.rom])


GENERATOR = RetroArch
