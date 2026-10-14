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


def _zip(files):
    import io
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        for name, (data, mode) in files.items():
            info = zipfile.ZipInfo(name)
            info.external_attr = mode << 16
            archive.writestr(info, data)
    return buf.getvalue()


def test_portmaster_install_keeps_only_game_dir_and_seeds_launcher(tmp_path, monkeypatch):
    import hashlib
    import json
    from esne import portmaster, systemscfg
    monkeypatch.setattr(portmaster, "machine", lambda: "x86_64")
    data = _zip({"Digger.sh": (b"#!/bin/bash", 0o755), "digger/digger.x86_64": (b"ELF", 0o644),
                 "digger/licenses/L.txt": (b"gpl", 0o644)})
    catalog_json = json.dumps({"ports": {"digger.zip": {"attr": {"arch": ["aarch64", "x86_64"]},
                                                       "source": {"url": "u://zip", "md5": hashlib.md5(data).hexdigest()}}}}).encode()
    fetch = lambda url: data if url == "u://zip" else catalog_json
    files = portmaster.install("digger.zip", "digger", tmp_path / "ports", fetch=fetch)
    assert sorted(files) == ["digger/digger.x86_64", "digger/licenses/L.txt"]
    assert not (tmp_path / "ports" / "Digger.sh").exists()
    assert (tmp_path / "ports" / "digger" / "digger.x86_64").stat().st_mode & 0o111
    ports = {"digger": {"file": "Digger.sh", "portmaster": "digger.zip", "dir": "digger", "binary": "digger"}}
    assert systemscfg.seed_ports(tmp_path, ports) == ["Digger.sh"]
    launcher = (tmp_path / "ports" / "Digger.sh").read_text()
    assert 'exec "./digger.$ARCH"' in launcher and 'exec esne-padkeys "digger.gptk" -- "./digger.$ARCH"' in launcher


def test_portmaster_rejects_bad_md5_wrong_arch_and_traversal(tmp_path, monkeypatch):
    import json
    import pytest
    from esne import portmaster
    monkeypatch.setattr(portmaster, "machine", lambda: "x86_64")
    data = _zip({"digger/a": (b"x", 0o644)})

    def make(arch, md5):
        cat = json.dumps({"ports": {"d.zip": {"attr": {"arch": arch}, "source": {"url": "u://z", "md5": md5}}}}).encode()
        return lambda url: data if url == "u://z" else cat

    with pytest.raises(portmaster.PortmasterError):
        portmaster.install("d.zip", "digger", tmp_path, fetch=make(["x86_64"], "0" * 32))
    with pytest.raises(portmaster.PortmasterError):
        portmaster.install("d.zip", "digger", tmp_path, fetch=make(["aarch64"], ""))
    evil = _zip({"digger/../../x": (b"x", 0o644)})
    assert portmaster.extract_game(evil, "digger", tmp_path / "ports") == []
