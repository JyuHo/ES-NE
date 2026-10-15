# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from esne.generators import duckstation, standalone
from esne.generators.base import Context, Controller


class Cfg:
    def __init__(self, **values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)


@pytest.fixture
def home(tmp_path, monkeypatch, esne_env):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setattr(standalone.shutil, "which", lambda n: f"/usr/bin/{n}" if n == "duckstation-qt" else None)
    return tmp_path


def ctx(rom, controllers=None, **settings):
    return Context(system="psx", rom=str(rom), config=Cfg(**settings), emulator="duckstation", controllers=controllers or [])


INI = "[GPU]\nRenderer = Automatic\nResolutionScale = 8\nMultisamples = 8\n[Display]\nAspectRatio = 16:9\nVSync = false\n[Pad1]\nType = AnalogController\nCross = SDL-0/A\n[Pad2]\nType = None\n"


def test_command_settings_and_pads(home):
    ini = home / "data" / "duckstation" / "settings.ini"
    ini.parent.mkdir(parents=True)
    ini.write_text(INI)
    rom = home / "g.cue"
    pads = [Controller(player=1, index=3), Controller(player=2, index=1)]
    command = duckstation.Duckstation().generate(ctx(rom, pads, duckstation_renderer="Vulkan", duckstation_resolution="4",
                                                    duckstation_vsync="1", duckstation_aspect="4:3", duckstation_pgxp="1"))
    assert command.argv[-3:-1] == ["-fullscreen", "--"] or command.argv[-2] == "--"
    assert command.argv[-1] == str(rom)
    text = ini.read_text()
    assert "Renderer = Vulkan" in text and "ResolutionScale = 4" in text and "Multisamples = 8" in text
    assert "VSync = true" in text and "AspectRatio = 4:3" in text and "PGXPEnable = true" in text
    assert "Cross = SDL-3/A" in text and "[Pad2]\nType = AnalogController" in text and "Cross = SDL-1/A" in text


def test_exit_options(home):
    ini = home / "data" / "duckstation" / "settings.ini"
    ini.parent.mkdir(parents=True)
    ini.write_text("[Main]\nConfirmPowerOff = true\nSaveStateOnExit = true\n")
    duckstation.Duckstation().generate(ctx(home / "g.cue", duckstation_confirm_exit="0", duckstation_save_on_exit="1"))
    assert ini.read_text() == "[Main]\nConfirmPowerOff = false\nSaveStateOnExit = true\n"


def test_one_pad_disables_pad2_and_invalid_ignored(home):
    ini = home / "data" / "duckstation" / "settings.ini"
    ini.parent.mkdir(parents=True)
    ini.write_text(INI)
    duckstation.Duckstation().generate(ctx(home / "g.cue", [Controller(player=1, index=0)], duckstation_resolution="99"))
    text = ini.read_text()
    assert "ResolutionScale = 8" in text and "[Pad2]\nType = None" in text


def test_autoconfig_off_and_missing_ini(home):
    ini = home / "data" / "duckstation" / "settings.ini"
    ini.parent.mkdir(parents=True)
    ini.write_text(INI)
    duckstation.Duckstation().generate(ctx(home / "g.cue", [Controller(player=1, index=5)], duckstation_autoconfig="0"))
    assert ini.read_text() == INI
    ini.unlink()
    duckstation.Duckstation().generate(ctx(home / "g.cue", [Controller(player=1, index=5)], duckstation_vsync="1"))
