# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from esne.generators import pcsx2, standalone
from esne.generators.base import Context, Controller


class Cfg:
    def __init__(self, **values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)


def pad(player, index):
    return Controller(player=player, index=index, guid="g" * 32, name="PS4 Controller")


@pytest.fixture
def home(tmp_path, monkeypatch, esne_env):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr(standalone.shutil, "which", lambda n: f"/usr/bin/{n}" if n == "pcsx2-qt" else None)
    return tmp_path / "xdg" / "PCSX2"


def context(rom, pads, **settings):
    return Context(system="ps2", rom=str(rom), config=Cfg(**settings), emulator="pcsx2", controllers=pads)


def read(ini):
    parser = pcsx2._parser()
    parser.read(ini)
    return parser


def test_pads_use_sdl_index_and_old_sections_are_removed(home, tmp_path):
    ini = home / "inis" / "PCSX2.ini"
    ini.parent.mkdir(parents=True)
    ini.write_text("[Pad3]\nType = DualShock2\n[Hotkeys]\nToggleFullscreen = Keyboard/Alt & Keyboard/Return\n")
    rom = tmp_path / "Jeu.iso"
    rom.write_bytes(b"x")
    command = pcsx2.Pcsx2().generate(context(rom, [pad(1, 0), pad(2, 3)]))
    assert command.argv[0] == "/usr/bin/pcsx2-qt"
    parser = read(ini)
    assert not parser.has_section("Pad3")
    assert parser["Pad1"]["Cross"] == "SDL-0/FaceSouth" and parser["Pad2"]["L2"] == "SDL-3/+LeftTrigger"
    assert parser["InputSources"]["SDL"] == "true"
    assert parser["Hotkeys"]["ToggleFullscreen"] == "Keyboard/Alt & Keyboard/Return"  # le reste est intact


def test_settings_applied(home, tmp_path):
    ini = home / "inis" / "PCSX2.ini"
    ini.parent.mkdir(parents=True)
    ini.write_text("[EmuCore/GS]\nRenderer = -1\n")
    rom = tmp_path / "Jeu.iso"
    rom.write_bytes(b"x")
    pcsx2.Pcsx2().generate(context(rom, [], pcsx2_gfxbackend="vulkan", pcsx2_resolution="3", pcsx2_ratio="16:9"))
    gs = read(ini)["EmuCore/GS"]
    assert (gs["Renderer"], gs["upscale_multiplier"], gs["AspectRatio"]) == ("14", "3", "16:9")


def test_autoconfig_off_keeps_pads(home, tmp_path):
    ini = home / "inis" / "PCSX2.ini"
    ini.parent.mkdir(parents=True)
    ini.write_text("[Pad1]\nUp = SDL-9/DPadUp\n")
    rom = tmp_path / "Jeu.iso"
    rom.write_bytes(b"x")
    pcsx2.Pcsx2().generate(context(rom, [pad(1, 0)], pcsx2_autoconfig="0"))
    assert read(ini)["Pad1"]["Up"] == "SDL-9/DPadUp"


def test_missing_ini_is_not_created(home, tmp_path):
    rom = tmp_path / "Jeu.iso"
    rom.write_bytes(b"x")
    pcsx2.Pcsx2().generate(context(rom, [pad(1, 0)]))
    assert not (home / "inis" / "PCSX2.ini").exists()


def test_checked_settings_are_written_and_invalid_ones_ignored(home, tmp_path):
    ini = home / "inis" / "PCSX2.ini"
    ini.parent.mkdir(parents=True)
    ini.write_text("[EmuCore/GS]\nMaxAnisotropy = 0\nfilter = 2\n\n[SPU2/Output]\nStandardVolume = 100\n")
    rom = tmp_path / "Jeu.iso"
    rom.write_bytes(b"x")
    pcsx2.Pcsx2().generate(context(rom, [], pcsx2_af="16", pcsx2_filter="9", pcsx2_widescreen="true", pcsx2_volume="50",
                                   pcsx2_mute="false", pcsx2_achievements="true", pcsx2_fps="true", pcsx2_dither="1"))
    data = read(ini)
    assert data["EmuCore/GS"]["MaxAnisotropy"] == "16" and data["EmuCore/GS"]["filter"] == "2"  # 9: ignoré
    assert data["EmuCore/GS"]["OsdShowFPS"] == "true" and data["EmuCore/GS"]["dithering_ps2"] == "1"
    assert data["EmuCore"]["EnableWideScreenPatches"] == "true"
    assert data["SPU2/Output"]["StandardVolume"] == "50" and data["SPU2/Output"]["OutputMuted"] == "false"
    assert data["Achievements"]["Enabled"] == "true"
