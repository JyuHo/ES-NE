# SPDX-License-Identifier: GPL-3.0-or-later
import shlex
import xml.etree.ElementTree as ET
from pathlib import Path

from esne import catalog, cli, systemscfg


def parse(xml):
    return ET.fromstring(xml)


def test_renders_every_catalog_system(esne_env):
    root = parse(systemscfg.render(catalog.systems(), Path("/roms")))
    names = [s.findtext("name") for s in root.findall("system")]
    assert "snes" in names and len(names) == len(catalog.systems())
    snes = next(s for s in root.findall("system") if s.findtext("name") == "snes")
    assert snes.findtext("path") == "/roms/snes"
    assert snes.findtext("platform") == "snes" and snes.findtext("theme") == "snes"
    assert snes.findtext("manufacturer") == "Nintendo" and snes.findtext("release") == "1990"
    assert ".sfc" in snes.findtext("extension") and ".SFC" in snes.findtext("extension")


def test_default_core_is_flagged_once(esne_env):
    root = parse(systemscfg.render(catalog.systems(), Path("/roms")))
    for system in root.findall("system"):
        defaults = [c for c in system.iter("core") if c.get("default") == "true"]
        has_cores = any(True for _ in system.iter("core"))
        assert len(defaults) == (1 if has_cores else 0), system.findtext("name")
    snes = next(s for s in root.findall("system") if s.findtext("name") == "snes")
    assert [c.text for c in snes.iter("core")] == ["snes9x", "bsnes"]


def test_installed_only_filters(esne_env):
    only_snes = lambda emulator, core: core == "snes9x"
    root = parse(systemscfg.render(catalog.systems(), Path("/roms"), installed_only=True, is_installed=only_snes))
    assert [s.findtext("name") for s in root.findall("system")] == ["snes"]


def test_command_is_accepted_by_launcher(esne_env):
    argv = shlex.split(
        systemscfg.LAUNCH_COMMAND.replace("%CONTROLLERSCONFIG%", "-p1index 0 -p1guid abc -p1name Pad")
        .replace("%SYSTEM%", "snes").replace("%ROM%", "/roms/snes/a.sfc").replace("%GAMEINFOXML%", "")
        .replace("%SYSTEMNAME%", "'Super Nintendo'").replace("%EMULATOR%", "libretro").replace("%CORE%", "snes9x")
    )
    assert argv[0] == "es-launcher"
    ctx = cli.build_context(argv[1:])
    assert (ctx.system, ctx.emulator, ctx.core) == ("snes", "libretro", "snes9x")


def test_main_writes_file_and_roms_dirs(esne_env):
    from esne import paths
    assert systemscfg.main([]) == 0
    assert (paths.config_dir() / "es_systems.cfg").exists()
    assert (paths.roms_dir() / "snes").is_dir()


def test_standalone_systems_have_emulator_without_cores(esne_env):
    root = parse(systemscfg.render(catalog.systems(), Path("/roms")))
    wii = next(s for s in root.findall("system") if s.findtext("name") == "wii")
    emulators = list(wii.find("emulators"))
    assert [e.get("name") for e in emulators] == ["dolphin"] and not list(emulators[0])
    assert catalog.default_choice("wii") == ("dolphin", None)
    assert catalog.default_choice("switch") == ("eden", None)
    assert catalog.default_choice("windows") == ("wine", None)


def test_seed_ports_creates_script_only_for_installed_games(tmp_path):
    from esne import systemscfg
    ports = {"supertux": {"file": "SuperTux.sh", "command": "supertux2 --fullscreen", "program": "supertux2"}}
    assert systemscfg.seed_ports(tmp_path, ports, which=lambda name: None) == []
    assert not (tmp_path / "ports").exists()
    assert systemscfg.seed_ports(tmp_path, ports, which=lambda name: "/usr/bin/" + name) == ["SuperTux.sh"]
    script = tmp_path / "ports" / "SuperTux.sh"
    assert script.read_text() == "#!/bin/sh\nexec supertux2 --fullscreen\n"
    assert script.stat().st_mode & 0o111
    script.write_text("custom")
    assert systemscfg.seed_ports(tmp_path, ports, which=lambda name: "/usr/bin/" + name) == []
    assert script.read_text() == "custom"


def test_ports_system_runs_script_with_shell(tmp_path):
    from esne import catalog
    assert catalog.systems()["ports"]["extensions"] == [".sh"]
    assert catalog.emulators()["shell"]["args"] == ["{rom}"]


def test_seed_keys_creates_private_template_once(tmp_path):
    from esne import systemscfg
    config = tmp_path / "cfg"
    assert systemscfg.seed_keys(config) is True
    target = config / "keys.conf"
    assert target.stat().st_mode & 0o777 == 0o600
    assert "SCREENSCRAPER_DEV_LOGIN" in target.read_text()
    target.write_text("GAMESDB_APIKEY=secret\n")
    assert systemscfg.seed_keys(config) is False
    assert target.read_text() == "GAMESDB_APIKEY=secret\n"
