# SPDX-License-Identifier: GPL-3.0-or-later
import struct

import pytest

from esne.generators import dolphin, standalone
from esne.generators.base import Context, Controller


class Cfg:
    def __init__(self, **values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)


@pytest.fixture
def home(tmp_path, monkeypatch, esne_env):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setattr(standalone.shutil, "which", lambda n: f"/usr/bin/{n}" if n == "dolphin-emu" else None)
    return tmp_path


def context(rom, **settings):
    return Context(system="gamecube", rom=str(rom), config=Cfg(**settings), emulator="dolphin")


def read(path):
    parser = dolphin._parser()
    parser.read(path)
    return parser


def test_settings_written_to_both_files(home):
    folder = home / "cfg" / "dolphin-emu"
    folder.mkdir(parents=True)
    (folder / "Dolphin.ini").write_text("[Core]\nGFXBackend = OGL\nOther = 1\n")
    (folder / "GFX.ini").write_text("[Settings]\nInternalResolution = 1\nMSAA = 0x00000004\n[Enhancements]\nMaxAnisotropy = 0\n")
    rom = home / "Jeu.iso"
    rom.write_bytes(b"x")
    command = dolphin.Dolphin().generate(context(
        rom, dolphin_backend="Vulkan", dolphin_resolution="4", dolphin_msaa="2", dolphin_af="4", dolphin_ratio="1",
        dolphin_vsync="true", dolphin_cheats="false", dolphin_gc_language="2", dolphin_shaders="2"))
    assert command.argv[0] == "/usr/bin/dolphin-emu"
    core = read(folder / "Dolphin.ini")["Core"]
    assert (core["GFXBackend"], core["EnableCheats"], core["SelectedLanguage"], core["Other"]) == ("Vulkan", "False", "2", "1")
    gfx = read(folder / "GFX.ini")
    assert gfx["Settings"]["InternalResolution"] == "4" and gfx["Settings"]["MSAA"] == "2"
    assert gfx["Settings"]["AspectRatio"] == "1" and gfx["Settings"]["ShaderCompilationMode"] == "2"
    assert gfx["Enhancements"]["MaxAnisotropy"] == "4" and gfx["Hardware"]["VSync"] == "True"


def test_unset_and_invalid_settings_change_nothing(home):
    folder = home / "cfg" / "dolphin-emu"
    folder.mkdir(parents=True)
    (folder / "GFX.ini").write_text("[Settings]\nInternalResolution = 3\n")
    rom = home / "Jeu.iso"
    rom.write_bytes(b"x")
    dolphin.Dolphin().generate(context(rom, dolphin_resolution="99", dolphin_msaa="zz"))
    assert read(folder / "GFX.ini")["Settings"]["InternalResolution"] == "3"


def test_missing_files_are_not_created(home):
    rom = home / "Jeu.iso"
    rom.write_bytes(b"x")
    dolphin.Dolphin().generate(context(rom, dolphin_resolution="2"))
    assert not (home / "cfg" / "dolphin-emu").exists()


def make_sysconf(path, language=1, ratio=0):
    entries = [("IPL.LNG", language), ("IPL.AR", ratio), ("BT.BAR", 0)]
    body = b"".join(bytes([(3 << 5) | (len(name) - 1)]) + name.encode() + bytes([value]) for name, value in entries)
    header = b"SCv0" + struct.pack(">H", len(entries)) + b"\0\0" * (len(entries) + 1)
    path.parent.mkdir(parents=True)
    path.write_bytes(header + body)


def test_wii_language_and_tv_patched_in_sysconf(home):
    sysconf = home / "data" / "dolphin-emu" / "Wii/shared2/sys/SYSCONF"
    make_sysconf(sysconf)
    rom = home / "Jeu.rvz"
    rom.write_bytes(b"x")
    ctx = Context(system="wii", rom=str(rom), config=Cfg(dolphin_wii_language="3", dolphin_wii_tv="1"), emulator="dolphin")
    dolphin.Dolphin().generate(ctx)
    data = sysconf.read_bytes()
    assert data.endswith(bytes([3 << 5 | 6]) + b"IPL.LNG" + bytes([3]) + bytes([3 << 5 | 5]) + b"IPL.AR" + bytes([1])
                         + bytes([3 << 5 | 5]) + b"BT.BAR" + bytes([0]))


def test_invalid_wii_values_ignored(home):
    sysconf = home / "data" / "dolphin-emu" / "Wii/shared2/sys/SYSCONF"
    make_sysconf(sysconf)
    before = sysconf.read_bytes()
    rom = home / "Jeu.rvz"
    rom.write_bytes(b"x")
    dolphin.Dolphin().generate(Context(system="wii", rom=str(rom), config=Cfg(dolphin_wii_language="42"), emulator="dolphin"))
    assert sysconf.read_bytes() == before


def test_sensor_bar_position_patched(home):
    sysconf = home / "data" / "dolphin-emu" / "Wii/shared2/sys/SYSCONF"
    make_sysconf(sysconf)
    rom = home / "Jeu.rvz"
    rom.write_bytes(b"x")
    dolphin.Dolphin().generate(Context(system="wii", rom=str(rom), config=Cfg(dolphin_sensorbar="1"), emulator="dolphin"))
    data = sysconf.read_bytes()
    assert data.endswith(b"BT.BAR" + bytes([1]))
    assert data.count(b"IPL.LNG" + bytes([1])) == 1  # le reste est intact


def wii_context(rom, pads, mode):
    return Context(system="wii", rom=str(rom), config=Cfg(dolphin_wii_pad=mode), emulator="dolphin", controllers=pads)


def test_wii_classic_controller_mapped_to_sdl_pad(home):
    rom = home / "Jeu.rvz"
    rom.write_bytes(b"x")
    pads = [Controller(player=1, index=0, name="PS4 Controller"), Controller(player=2, index=1, name="PS4 Controller")]
    dolphin.Dolphin().generate(wii_context(rom, pads, "classic"))
    parser = read(home / "cfg" / "dolphin-emu" / "WiimoteNew.ini")
    first, second = parser["Wiimote1"], parser["Wiimote2"]
    assert first["Device"] == "SDL/0/PS4 Controller" and second["Device"] == "SDL/1/PS4 Controller"
    assert first["Source"] == "1" and first["Extension"] == "Classic"
    assert first["Classic/Buttons/A"] == "`Button B`" and first["Classic/Left Stick/Up"] == "`Left Y+`"
    assert parser["Wiimote3"]["Source"] == "0"


def test_wii_nunchuk_mode_uses_right_stick_for_pointer(home):
    rom = home / "Jeu.rvz"
    rom.write_bytes(b"x")
    dolphin.Dolphin().generate(wii_context(rom, [Controller(player=1, index=0, name="PS4 Controller")], "nunchuk"))
    first = read(home / "cfg" / "dolphin-emu" / "WiimoteNew.ini")["Wiimote1"]
    assert first["Extension"] == "Nunchuk" and first["Buttons/A"] == "`Button A`"
    assert first["Nunchuk/Stick/Left"] == "`Left X-`" and first["IR/Right"] == "`Right X+`"


def test_wii_real_wiimotes_and_untouched_without_setting(home):
    rom = home / "Jeu.rvz"
    rom.write_bytes(b"x")
    dolphin.Dolphin().generate(wii_context(rom, [], "real"))
    parser = read(home / "cfg" / "dolphin-emu" / "WiimoteNew.ini")
    assert parser["Wiimote1"]["Source"] == "2" and parser["BalanceBoard"]["Source"] == "2"
    ini = home / "cfg" / "dolphin-emu" / "WiimoteNew.ini"
    ini.write_text("[Wiimote1]\nSource = 1\n")
    dolphin.Dolphin().generate(wii_context(rom, [], ""))
    assert ini.read_text() == "[Wiimote1]\nSource = 1\n"


def test_wii_pad_ignored_for_gamecube(home):
    rom = home / "Jeu.iso"
    rom.write_bytes(b"x")
    ctx = Context(system="gamecube", rom=str(rom), config=Cfg(dolphin_wii_pad="classic"), emulator="dolphin")
    dolphin.Dolphin().generate(ctx)
    assert not (home / "cfg" / "dolphin-emu" / "WiimoteNew.ini").exists()


def test_gamecube_two_players_mapped_and_ports_set(home):
    folder = home / "cfg" / "dolphin-emu"
    folder.mkdir(parents=True)
    (folder / "Dolphin.ini").write_text("[Core]\nSIDevice0 = 0\nSIDevice1 = 0\nSIDevice2 = 6\n")
    rom = home / "Jeu.iso"
    rom.write_bytes(b"x")
    pads = [Controller(player=1, index=0, name="PS4 Controller"), Controller(player=2, index=1, name="PS4 Controller")]
    dolphin.Dolphin().generate(Context(system="gamecube", rom=str(rom), config=Cfg(dolphin_gc_pad="sdl"),
                                       emulator="dolphin", controllers=pads))
    parser = read(folder / "GCPadNew.ini")
    assert parser["GCPad1"]["Device"] == "SDL/0/PS4 Controller" and parser["GCPad2"]["Device"] == "SDL/1/PS4 Controller"
    assert parser["GCPad1"]["Buttons/Z"] == "`Shoulder R`" and parser["GCPad2"]["Main Stick/Up"] == "`Left Y+`"
    assert "Device" not in parser["GCPad3"] and "Device" not in parser["GCPad4"]
    core = read(folder / "Dolphin.ini")["Core"]
    assert [core[f"SIDevice{i}"] for i in range(4)] == ["6", "6", "0", "0"]


def test_gamecube_pads_untouched_without_setting(home):
    rom = home / "Jeu.iso"
    rom.write_bytes(b"x")
    dolphin.Dolphin().generate(Context(system="gamecube", rom=str(rom), config=Cfg(), emulator="dolphin",
                                       controllers=[Controller(player=1, index=0, name="PS4 Controller")]))
    assert not (home / "cfg" / "dolphin-emu" / "GCPadNew.ini").exists()
