import os
import subprocess
from .generators import load_generator
from .generators.base import Context


def run(ctx: Context) -> int:
    gen = load_generator("retroarch" if ctx.emulator == "libretro" else ctx.emulator)
    cmd = gen.generate(ctx)
    proc = subprocess.run(cmd.argv, env={**os.environ, **cmd.env}, cwd=cmd.cwd)
    gen.post_run(ctx)
    return proc.returncode
