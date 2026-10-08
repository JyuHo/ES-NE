"""CLI compatible avec l'appel d'ES: es-launcher -system X -rom Y [...]"""
import argparse
import sys
from pathlib import Path
from . import paths
from .config import Config
from .generators.base import Context
from .launcher import run


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="es-launcher")
    p.add_argument("-system", required=True)
    p.add_argument("-rom", required=True)
    p.add_argument("-emulator")
    p.add_argument("-core")
    p.add_argument("-gameinfoxml")
    p.add_argument("-systemname")
    args, _unknown = p.parse_known_args(argv)

    cfg = Config.load(paths.conf_file())
    rom_name = Path(args.rom).name
    ctx = Context(
        system=args.system,
        rom=args.rom,
        config=_Scoped(cfg, args.system, rom_name),
        emulator=args.emulator or cfg.get("emulator", args.system, rom_name, "libretro"),
        core=args.core or cfg.get("core", args.system, rom_name),
    )
    return run(ctx)


class _Scoped:
    """Config liée à un système/rom: get(key, [system]) simplifié."""
    def __init__(self, cfg, system, rom):
        self.cfg, self.system, self.rom = cfg, system, rom

    def get(self, key, system=None, default=None):
        return self.cfg.get(key, self.system, self.rom, default)


if __name__ == "__main__":
    sys.exit(main())
