# SPDX-License-Identifier: GPL-3.0-or-later
import struct

import pytest

from esne.generators import dolphin, standalone
from esne.generators.base import Context


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
