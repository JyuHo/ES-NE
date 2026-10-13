# SPDX-License-Identifier: GPL-3.0-or-later
import pytest
import yaml

from esne.generators import rpcs3, standalone
from esne.generators.base import Context, Controller


class Cfg:
    def __init__(self, **values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)


def pad(player, name="PS4 Controller"):
    return Controller(player=player, index=player - 1, guid="g" * 32, name=name)


@pytest.fixture
def home(tmp_path, monkeypatch, esne_env):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr(standalone.shutil, "which", lambda n: f"/usr/bin/{n}" if n == "rpcs3" else None)
    return tmp_path / "xdg" / "rpcs3"


def context(rom, pads, **settings):
    return Context(system="ps3", rom=str(rom), config=Cfg(**settings), emulator="rpcs3", controllers=pads)


def test_device_names_are_counted_per_name():
    result = rpcs3.controllers_config([pad(1), pad(2), pad(3, "Xbox, One")])
    assert result["Player 1 Input"]["Device"] == "PS4 Controller 1"
    assert result["Player 2 Input"]["Device"] == "PS4 Controller 2"
    assert result["Player 3 Input"]["Device"] == "Xbox. One 1"  # virgule remplacée
    assert result["Player 1 Input"]["Handler"] == "SDL" and result["Player 1 Input"]["Config"]["Cross"] == "South"


def test_generate_writes_controllers_and_video(home, tmp_path):
    home.mkdir(parents=True)
    (home / "config.yml").write_text(yaml.safe_dump({"Video": {"Renderer": "OpenGL", "Resolution Scale": 100}, "Core": {"A": 1}}))
    rom = tmp_path / "Jeu.iso"
    rom.write_bytes(b"x")
    command = rpcs3.Rpcs3().generate(context(rom, [pad(1)], rpcs3_gfxbackend="vulkan", rpcs3_resolution_scale="150"))
    assert command.argv == ["/usr/bin/rpcs3", "--no-gui", str(rom)]
    data = yaml.safe_load((home / "config.yml").read_text())
    assert data["Video"]["Renderer"] == "Vulkan" and data["Video"]["Resolution Scale"] == 150 and data["Core"] == {"A": 1}
    pads = yaml.safe_load((home / "input_configs" / "global" / "Default.yml").read_text())
    assert pads["Player 1 Input"]["Device"] == "PS4 Controller 1"


def test_autoconfig_off_and_missing_config_dir(home, tmp_path):
    rom = tmp_path / "Jeu.iso"
    rom.write_bytes(b"x")
    rpcs3.Rpcs3().generate(context(rom, [pad(1)]))  # RPCS3 jamais lancé: rien n'est créé
    assert not home.exists()
    home.mkdir(parents=True)
    rpcs3.Rpcs3().generate(context(rom, [pad(1)], rpcs3_autoconfig="0"))
    assert not (home / "input_configs").exists()


def test_game_folder_runs_eboot(tmp_path):
    folder = tmp_path / "Jeu.ps3"
    eboot = folder / "PS3_GAME" / "USRDIR" / "EBOOT.BIN"
    eboot.parent.mkdir(parents=True)
    eboot.write_bytes(b"x")
    assert rpcs3.game_target(str(folder)) == str(eboot)
    assert rpcs3.game_target(str(tmp_path / "a.iso")) == str(tmp_path / "a.iso")
