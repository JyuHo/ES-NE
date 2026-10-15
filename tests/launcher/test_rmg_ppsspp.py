# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from esne.generators import iniedit, ppsspp, rmg, standalone
from esne.generators.base import Context, Controller


class Cfg:
    def __init__(self, **values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)


@pytest.fixture
def home(tmp_path, monkeypatch, esne_env):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setattr(standalone.shutil, "which", lambda n: f"/usr/bin/{n}" if n in ("rmg", "PPSSPPSDL") else None)
    return tmp_path


def ctx(system, emulator, rom, controllers=None, **settings):
    return Context(system=system, rom=str(rom), config=Cfg(**settings), emulator=emulator, controllers=controllers or [])


# ---------- iniedit ----------

def test_patch_ini_keeps_everything_else(tmp_path):
    ini = tmp_path / "a.ini"
    ini.write_text("[General]\nx=1\n\n[User]\nvideo\\fxaa=0\nfont\\color=@Variant(\\0\\0)\n\n[Other]\nvideo\\fxaa=9\n")
    assert iniedit.patch_ini(ini, {"User": {r"video\fxaa": "1", r"video\vsync": "1"}, "New": {"k": "v"}})
    assert ini.read_text() == ("[General]\nx=1\n\n[User]\nvideo\\fxaa=1\nfont\\color=@Variant(\\0\\0)\nvideo\\vsync=1\n\n"
                               "[Other]\nvideo\\fxaa=9\n\n[New]\nk=v\n")
    assert not iniedit.patch_ini(ini, {"User": {r"video\fxaa": "1"}})  # déjà à jour


def test_patch_ini_keeps_spacing_and_missing_file(tmp_path):
    ini = tmp_path / "b.ini"
    ini.write_text("[Sound]\nEnable = True\n[Graphics]\nVerticalSync = True\n")
    iniedit.patch_ini(ini, {"Sound": {"Enable": "False", "Volume": "5"}}, spaced=True)
    assert ini.read_text() == "[Sound]\nEnable = False\nVolume = 5\n[Graphics]\nVerticalSync = True\n"
    assert not iniedit.patch_ini(tmp_path / "nope.ini", {"S": {"a": "b"}})


# ---------- PPSSPP ----------

PPSSPP_INI = "[General]\nFullScreen = x\n[Graphics]\nGraphicsBackend = 3 (VULKAN)\nInternalResolution = 4\nAnisotropyLevel = 4\nVerticalSync = True\n[Sound]\nEnable = True\n[SystemParam]\nGameLanguage = 2\n"


def test_ppsspp_command_and_settings(home):
    ini = home / "cfg" / "ppsspp" / "PSP" / "SYSTEM" / "ppsspp.ini"
    ini.parent.mkdir(parents=True)
    ini.write_text(PPSSPP_INI)
    rom = home / "Jeu.iso"
    rom.write_bytes(b"x")
    command = ppsspp.Ppsspp().generate(ctx("psp", "ppsspp", rom, ppsspp_resolution="6", ppsspp_af="2", ppsspp_vsync="0",
                                           ppsspp_mute="1", ppsspp_language="1", ppsspp_backend="opengl", ppsspp_frameskip="auto", ppsspp_fps="1"))
    assert command.argv == ["/usr/bin/PPSSPPSDL", "--fullscreen", "--pause-menu-exit", str(rom)]
    text = ini.read_text()
    for line in ("InternalResolution = 6", "AnisotropyLevel = 2", "VerticalSync = False", "Enable = False", "GameLanguage = 1",
                 "GraphicsBackend = 0 (OPENGL)", "iShowStatusFlags = 2", "AutoFrameSkip = True", "FrameSkip = 0"):
        assert line in text
    assert "FullScreen = x" in text  # le reste est intact


def test_ppsspp_unset_and_invalid_values_leave_the_file(home):
    ini = home / "cfg" / "ppsspp" / "PSP" / "SYSTEM" / "ppsspp.ini"
    ini.parent.mkdir(parents=True)
    ini.write_text(PPSSPP_INI)
    rom = home / "Jeu.iso"
    rom.write_bytes(b"x")
    ppsspp.Ppsspp().generate(ctx("psp", "ppsspp", rom, ppsspp_resolution="99", ppsspp_af="", ppsspp_frameskip="7"))
    assert ini.read_text() == PPSSPP_INI


def test_ppsspp_missing_ini_is_not_an_error(home):
    rom = home / "Jeu.iso"
    rom.write_bytes(b"x")
    assert ppsspp.Ppsspp().generate(ctx("psp", "ppsspp", rom, ppsspp_resolution="2")).argv[0] == "/usr/bin/PPSSPPSDL"


# ---------- RMG ----------

GLIDEN = "[General]\nprofile=User\n[User]\nvideo\\fxaa=0\nvideo\\multisampling=4\ntexture\\anisotropy=16\nframeBufferEmulation\\aspect=4\n"
CFG = '''[Core]
Version = 1

[Rosalie's Mupen GUI - Input Plugin Profile 0]

PluggedIn = True
DeviceName = "Xbox 360 Controller"
DeviceType = 4
DevicePath = "/dev/input/event14"
DeviceSerial = ""
A_InputType = "0"

[Rosalie's Mupen GUI - Input Plugin Profile 1]

PluggedIn = False
DeviceName = "None"
DeviceType = 0
DevicePath = ""
'''


def rmg_files(home):
    folder = home / "cfg" / "RMG"
    folder.mkdir(parents=True)
    (folder / "GLideN64.ini").write_text(GLIDEN)
    (folder / "mupen64plus.cfg").write_text(CFG)
    rom = home / "Jeu.z64"
    rom.write_bytes(b"x")
    return folder, rom


def test_rmg_command_and_video(home):
    folder, rom = rmg_files(home)
    command = rmg.Rmg().generate(ctx("n64", "rmg", rom, rmg_resolution="4", rmg_msaa="8", rmg_fxaa="1", rmg_af="8", rmg_fps="1",
                                     rmg_aspect="2", rmg_vsync="9"))
    assert command.argv == ["/usr/bin/rmg", "-f", "-n", "-q", str(rom)]
    text = (folder / "GLideN64.ini").read_text()
    for line in ("frameBufferEmulation\\nativeResFactor=4", "video\\multisampling=8", "video\\fxaa=1", "texture\\anisotropy=8",
                 "onScreenDisplay\\showFPS=1", "frameBufferEmulation\\aspect=2"):
        assert line in text
    assert "verticalSync" not in text  # valeur invalide ignorée


def test_rmg_pads_written_and_known_name_kept(home):
    folder, rom = rmg_files(home)
    pads = [Controller(player=1, index=0, name="PS4 Controller", path="/dev/input/event14"),
            Controller(player=2, index=1, name="PS4 Controller", path="/dev/input/event15")]
    rmg.Rmg().generate(ctx("n64", "rmg", rom, pads))
    cfg = folder / "mupen64plus.cfg"
    first = iniedit_read(cfg, 0)
    second = iniedit_read(cfg, 1)
    assert first["DeviceName"] == "Xbox 360 Controller"  # le nom connu de RMG pour ce chemin est gardé
    assert second["DeviceName"] == "PS4 Controller" and second["DevicePath"] == "/dev/input/event15" and second["PluggedIn"] == "True"
    assert first["B_Name"] == "x" and first["B_Data"] == "2" and first["ZTrigger_InputType"] == "1" and first["CButtonUp_Data"] == "3"
    assert iniedit_read(cfg, 2)["PluggedIn"] == "False" and iniedit_read(cfg, 3)["DeviceName"] == "None"


def test_rmg_autoconfig_off_and_pad_without_path(home):
    folder, rom = rmg_files(home)
    rmg.Rmg().generate(ctx("n64", "rmg", rom, [Controller(player=1, index=0, name="Pad", path="/dev/input/event3")], rmg_autoconfig="0"))
    assert (folder / "mupen64plus.cfg").read_text() == CFG
    rmg.Rmg().generate(ctx("n64", "rmg", rom, [Controller(player=1, index=0, name="Pad", path="")]))
    assert iniedit_read(folder / "mupen64plus.cfg", 0)["PluggedIn"] == "False"


def iniedit_read(cfg, number):
    return iniedit.read_section(cfg, rmg.PROFILE.format(number))


PROC = """I: Bus=0003 Vendor=054c Product=09cc Version=8111
N: Name="Wireless Controller"
H: Handlers=event14 js0

I: Bus=0003 Vendor=054c Product=09cc Version=8111
N: Name="Wireless Controller Touchpad"
H: Handlers=mouse2 event15

I: Bus=0003 Vendor=054c Product=09cc Version=8111
N: Name="Wireless Controller"
H: Handlers=event20 js1
"""


def test_evdev_path_from_guid():
    from esne.generators import evdev
    from esne.generators.base import Controller

    guid = "030000004c050000cc09000011810000"
    pads = [Controller(player=1, index=0, guid=guid), Controller(player=2, index=1, guid=guid)]
    evdev.resolve_paths(pads, PROC, [])
    assert [p.path for p in pads] == ["/dev/input/event14", "/dev/input/event20"]


def test_evdev_path_unknown_guid_untouched():
    from esne.generators import evdev
    from esne.generators.base import Controller

    pad = Controller(player=1, index=0, guid="0000000000000000")
    evdev.resolve_paths([pad], PROC, [])
    assert pad.path == ""


def test_path_prefers_hidraw_for_sony_and_known_path():
    from esne.generators import evdev
    from esne.generators.base import Controller

    guid = "030000004c050000cc09000011810000"
    hid = [(0x054C, 0x09CC, "/dev/hidraw3")]
    pad = Controller(player=1, index=0, guid=guid)
    evdev.resolve_paths([pad], PROC, hid)
    assert pad.path == "/dev/hidraw3"
    pad = Controller(player=1, index=0, guid=guid)
    evdev.resolve_paths([pad], PROC, hid, known={"/dev/input/event14"})
    assert pad.path == "/dev/input/event14"
