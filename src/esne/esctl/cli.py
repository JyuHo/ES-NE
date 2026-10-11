# SPDX-License-Identifier: GPL-3.0-or-later
"""Point d'entrée d'esctl."""
from __future__ import annotations

import sys

from .commands import COMMANDS

USAGE = """usage: esctl <commande> [arguments]

commandes:
  has <commande>   code de sortie 0 si la commande est utilisable sur cette machine
  commands         liste les commandes utilisables, une par ligne
  help             affiche ce message
""" + "".join(f"  {name}\n" for name in sorted(COMMANDS))

EXIT_USAGE = 2


def has(args: list[str]) -> int:
    if len(args) != 1:
        print("usage: esctl has <commande>", file=sys.stderr)
        return EXIT_USAGE
    module = COMMANDS.get(args[0])
    return 0 if module is not None and module.available() else 1


def list_commands() -> int:
    for name in sorted(COMMANDS):
        if COMMANDS[name].available():
            print(name)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if not args or args[0] in ("help", "-h", "--help"):
        print(USAGE, end="")
        return 0 if args else EXIT_USAGE

    name, rest = args[0], args[1:]
    if name == "has":
        return has(rest)
    if name == "commands":
        return list_commands()

    module = COMMANDS.get(name)
    if module is None:
        print(f"esctl: commande inconnue: {name}", file=sys.stderr)
        return EXIT_USAGE
    return module.run(rest)


if __name__ == "__main__":
    sys.exit(main())
