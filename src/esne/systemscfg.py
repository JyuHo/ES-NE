# SPDX-License-Identifier: GPL-3.0-or-later
"""Génère ``es_systems.cfg`` (le fichier lu par EmulationStation) à partir du catalogue."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

from . import catalog, paths
from .generators.retroarch import find_binary, find_core

LAUNCH_COMMAND = (
    "es-launcher %CONTROLLERSCONFIG% -system %SYSTEM% -rom %ROM% -gameinfoxml %GAMEINFOXML% "
    "-systemname %SYSTEMNAME% -emulator %EMULATOR% -core %CORE%"
)


def _cores(entry: dict) -> list[tuple[str, str, int]]:
    """[(émulateur, core, priorité)] triés: le plus prioritaire d'abord, l'ordre du fichier départage."""
    found = []
    for emulator, cores in (entry.get("emulators") or {}).items():
        if not cores:
            found.append((emulator, "", catalog.DEFAULT_PRIORITY))
            continue
        for core, opts in cores.items():
            found.append((emulator, core, int((opts or {}).get("priority", catalog.DEFAULT_PRIORITY))))
    return sorted(found, key=lambda item: item[2])


def core_installed(emulator: str, core: str) -> bool:
    if emulator != "libretro":
        return False
    try:
        info = catalog.emulator_info("libretro") or {}
        find_binary(info.get("binary"))
        find_core(core, info.get("core_dirs"))
        return True
    except Exception:  # LaunchError: binaire ou core absent
        return False


def render(systems: dict, roms: Path, installed_only: bool = False, is_installed=core_installed) -> str:
    lines = ['<?xml version="1.0"?>', "<systemList>"]
    for name, entry in systems.items():
        if not isinstance(entry, dict):
            continue
        cores = _cores(entry)
        if installed_only and not any(is_installed(e, c) for e, c, _ in cores if c):
            continue

        extensions = " ".join(entry.get("extensions") or [])
        lines += [
            "  <system>",
            f"    <name>{escape(name)}</name>",
            f"    <fullname>{escape(str(entry.get('name', name)))}</fullname>",
            f"    <manufacturer>{escape(str(entry.get('manufacturer', '')))}</manufacturer>",
            f"    <release>{entry.get('release', '')}</release>",
            f"    <hardware>{escape(str(entry.get('hardware', '')))}</hardware>",
            f"    <path>{escape(str(roms / name))}</path>",
            f"    <extension>{escape(extensions)} {escape(extensions.upper())}</extension>",
            f"    <command>{escape(LAUNCH_COMMAND)}</command>",
            f"    <platform>{escape(str(entry.get('platform', name)))}</platform>",
            f"    <theme>{escape(str(entry.get('theme', name)))}</theme>",
            "    <emulators>",
        ]
        by_emulator: dict[str, list[tuple[str, int]]] = {}
        for emulator, core, priority in cores:
            by_emulator.setdefault(emulator, []).append((core, priority))
        default_emulator, default_core = catalog.default_choice(name)
        for emulator, emulator_cores in by_emulator.items():
            lines.append(f"      <emulator name={quoteattr(emulator)}>")
            lines.append("        <cores>")
            for core, _ in emulator_cores:
                if not core:
                    continue
                default = ' default="true"' if (emulator, core) == (default_emulator, default_core) else ""
                lines.append(f"          <core{default}>{escape(core)}</core>")
            lines.append("        </cores>")
            lines.append("      </emulator>")
        lines += ["    </emulators>", "  </system>"]
    lines.append("</systemList>")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="es-genconfig", description="Génère es_systems.cfg à partir du catalogue ES-NE.")
    parser.add_argument("-o", "--output", type=Path, help=f"fichier à écrire (défaut: {paths.config_dir() / 'es_systems.cfg'})")
    parser.add_argument("--stdout", action="store_true", help="écrit sur la sortie standard au lieu d'un fichier")
    parser.add_argument("--installed-only", action="store_true", help="ne garde que les systèmes dont un core est installé")
    parser.add_argument("--no-mkdir", action="store_true", help="ne crée pas les dossiers de roms")
    args = parser.parse_args(argv)

    systems = catalog.systems()
    roms = paths.roms_dir()
    xml = render(systems, roms, args.installed_only)

    if args.stdout:
        sys.stdout.write(xml)
        return 0

    target = args.output or paths.config_dir() / "es_systems.cfg"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(xml, encoding="utf-8")
    if not args.no_mkdir:
        for name, entry in systems.items():
            if isinstance(entry, dict) and f"<name>{name}</name>" in xml:
                (roms / name).mkdir(parents=True, exist_ok=True)
    print(f"écrit: {target} ({xml.count('<system>')} systèmes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
