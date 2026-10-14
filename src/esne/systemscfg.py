# SPDX-License-Identifier: GPL-3.0-or-later
"""Génère ``es_systems.cfg`` (le fichier lu par EmulationStation) à partir du catalogue."""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

from . import catalog, featurescfg, paths, portmaster, steam
from . import cores as cores_mod
from .generators import standalone
from .generators.retroarch import find_binary, find_core

LAUNCH_COMMAND = (
    "es-launcher %CONTROLLERSCONFIG% -system %SYSTEM% -rom %ROM% -gameinfoxml %GAMEINFOXML% "
    "-systemname %SYSTEMNAME% -emulator %EMULATOR% -core %CORE%"
)


def _cores(entry: dict) -> list[tuple[str, str, int]]:
    """[(émulateur, core, priorité)] triés: le plus prioritaire d'abord, l'ordre du fichier départage.
    Un émulateur autonome a le core ''."""
    return sorted(((e, c or "", p) for e, c, p in catalog.choices(entry)), key=lambda item: item[2])


def core_installed(emulator: str, core: str) -> bool:
    if emulator != "libretro":
        return standalone.is_installed(emulator)
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
        if installed_only and not any(is_installed(e, c) for e, c, _ in cores):
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
        # le core par défaut est le plus prioritaire des cores installés (sinon celui du catalogue: « cœur manquant »)
        if not is_installed(default_emulator, default_core or ""):
            for emulator, core, _ in cores:
                if is_installed(emulator, core):
                    default_emulator, default_core = emulator, core or None
                    break
        for emulator, emulator_cores in by_emulator.items():
            named = [core for core, _ in emulator_cores if core]
            if not named:
                lines.append(f"      <emulator name={quoteattr(emulator)} />")
                continue
            lines.append(f"      <emulator name={quoteattr(emulator)}>")
            lines.append("        <cores>")
            for core in named:
                default = ' default="true"' if (emulator, core) == (default_emulator, default_core) else ""
                netplay = ' netplay="true"' if emulator == "libretro" and core in cores_mod.NETPLAY else ""
                lines.append(f"          <core{default}{netplay}>{escape(core)}</core>")
            lines.append("        </cores>")
            lines.append("      </emulator>")
        lines += ["    </emulators>", "  </system>"]
    lines.append("</systemList>")
    return "\n".join(lines) + "\n"


KEYS_TEMPLATE = """# Clés de développeur d'ES-NE (lues au démarrage d'ES, jamais commitées ni empaquetées). Une ligne NOM=valeur, # = commentaire.
# Garde ce fichier privé (chmod 600). Redémarre ES après modification.

# ScreenScraper (https://screenscraper.fr, compte développeur)
# SCREENSCRAPER_SOFTNAME=ES-NE
# SCREENSCRAPER_DEV_LOGIN=devid=TON_DEVID&devpassword=TON_MOT_DE_PASSE

# TheGamesDB (https://thegamesdb.net)
# GAMESDB_APIKEY=TA_CLE

# RetroAchievements (menu des succès d'ES)
# CHEEVOS_DEV_LOGIN=z=TON_UTILISATEUR&y=TA_CLE_API

# HFS (facultatif)
# HFS_DEV_LOGIN=utilisateur:mot_de_passe
"""


def seed_keys(config: Path) -> bool:
    """Crée le modèle ``keys.conf`` (mode 600) s'il n'existe pas. True si créé."""
    target = config / "keys.conf"
    if target.exists():
        return False
    config.mkdir(parents=True, exist_ok=True)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(KEYS_TEMPLATE)
    return True


LAUNCHER_PORTMASTER = """#!/bin/sh
# Lanceur ES-NE d'un jeu du catalogue PortMaster (le script PortMaster d'origine n'est pas utilisé).
cd "$(dirname "$0")/{dir}" || exit 1
ARCH=$(uname -m)
export LD_LIBRARY_PATH="$PWD/libs.$ARCH${{LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}}"
# manette -> clavier avec la correspondance .gptk du jeu (si fournie), sans quoi le jeu se lance tel quel
if [ -f "{binary}.gptk" ] && command -v esne-padkeys >/dev/null 2>&1; then
    exec esne-padkeys "{binary}.gptk" -- "./{binary}.$ARCH"
fi
exec "./{binary}.$ARCH"
"""


def seed_ports(roms: Path, ports: dict | None = None, which=None) -> list[str]:
    """Crée les scripts des jeux libres installés dans ``<roms>/ports`` (un fichier existant n'est jamais écrasé).

    Deux formes d'entrée: ``command`` (programme du système, trouvé dans le PATH) ou ``portmaster`` (jeu installé par
    ``es-genconfig --install-port``, dossier ``dir`` contenant ``<binary>.<arch>``).
    """
    which = which or shutil.which
    created = []
    for key, entry in (catalog.load_data("ports.yml") if ports is None else ports).items():
        if not isinstance(entry, dict) or not entry.get("file"):
            continue
        if entry.get("portmaster"):
            game_dir = str(entry.get("dir", key))
            binary = str(entry.get("binary", key))
            if not (roms / "ports" / game_dir / f"{binary}.{portmaster.machine()}").is_file():
                continue
            content = LAUNCHER_PORTMASTER.format(dir=game_dir, binary=binary)
        elif entry.get("command"):
            if not which(str(entry.get("program") or str(entry["command"]).split()[0])):
                continue
            content = f"#!/bin/sh\nexec {entry['command']}\n"
        else:
            continue
        target = roms / "ports" / str(entry["file"])
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        target.chmod(0o755)
        created.append(target.name)
    return created


def install_port(name: str, roms: Path, ports: dict | None = None) -> int:
    """``es-genconfig --install-port NOM``: télécharge un jeu PortMaster puis crée son lanceur."""
    games = {key: e for key, e in (catalog.load_data("ports.yml") if ports is None else ports).items()
             if isinstance(e, dict) and e.get("portmaster")}
    if name not in games:
        print(f"jeu inconnu: {name} (disponibles: {', '.join(sorted(games)) or 'aucun'})", file=sys.stderr)
        return 1
    entry = games[name]
    try:
        files = portmaster.install(str(entry["portmaster"]), str(entry.get("dir", name)), roms / "ports")
    except portmaster.PortmasterError as exc:
        print(f"erreur: {exc}", file=sys.stderr)
        return 1
    print(f"{name}: {len(files)} fichiers installés dans {roms / 'ports'}")
    for script in seed_ports(roms, games):
        print(f"port ajouté: {script}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="es-genconfig", description="Génère es_systems.cfg à partir du catalogue ES-NE.")
    parser.add_argument("-o", "--output", type=Path, help=f"fichier à écrire (défaut: {paths.config_dir() / 'es_systems.cfg'})")
    parser.add_argument("--stdout", action="store_true", help="écrit sur la sortie standard au lieu d'un fichier")
    parser.add_argument("--installed-only", action="store_true", help="ne garde que les systèmes dont un core est installé")
    parser.add_argument("--install-port", metavar="NOM", help="télécharge un jeu libre du catalogue PortMaster (ex: digger) dans le système ports")
    parser.add_argument("--list-ports", action="store_true", help="liste les jeux PortMaster proposés")
    parser.add_argument("--no-mkdir", action="store_true", help="ne crée pas les dossiers de roms")
    args = parser.parse_args(argv)

    roms = paths.roms_dir()
    if args.list_ports:
        for key, e in sorted(catalog.load_data("ports.yml").items()):
            if isinstance(e, dict) and e.get("portmaster"):
                print(f"{key}\t{e.get('title', key)}")
        return 0
    if args.install_port:
        return install_port(args.install_port, roms)

    systems = catalog.systems()
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
    if not args.no_mkdir:
        for name in seed_ports(roms):
            print(f"port ajouté: {name}")
        for name in steam.seed(roms):
            print(f"jeu Steam ajouté: {name}")

    if seed_keys(target.parent):
        print(f"modèle créé: {target.parent / 'keys.conf'} (clés de scraping, mode 600)")

    features = target.parent / "es_features.cfg"
    features.write_text(featurescfg.render(), encoding="utf-8")
    print(f"écrit: {features}")
    # ES n'affiche les menus de décorations (bezels) que si ce dossier existe
    (paths.data_dir() / "decorations").mkdir(parents=True, exist_ok=True)
    shader_sets = featurescfg.installed_shader_sets()
    featurescfg.write_shader_sets(featurescfg.shaders_root(), shader_sets)
    print(f"jeux de shaders: {', '.join(shader_sets) if shader_sets else 'aucun (installez libretro-shaders-slang)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
