# SPDX-License-Identifier: GPL-3.0-or-later
import tomllib

import pytest

from esne.generators import standalone, xemu
from esne.generators.base import Context, Controller

GUID = "03000000" + "4c05000009cc0000" + "11810000"

TOML = """[general]
show_welcome = true
skip_boot_anim = false

[general.updates]
check = true

[sys.files]
bootrom_path = ''
flashrom_path = ''
eeprom_path = ''
hdd_path = ''

[display.window]
fullscreen_on_startup = false

[input.bindings]
port1 = ''
port1_driver = 'usb-xbox-gamepad'
"""


class Cfg:
    def __init__(self, **values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)


@pytest.fixture
def home(tmp_path, monkeypatch, esne_env):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setattr(standalone.shutil, "which", lambda n: f"/usr/bin/{n}" if n == "xemu" else None)
    bios = tmp_path / "bios"
    bios.mkdir()
    (bios / "mcpx_1.0.bin").write_bytes(b"\0" * 512)
    (bios / "Complex_4627.bin").write_bytes(b"\0" * 1048576)
    (bios / "eeprom.bin").write_bytes(b"\0" * 256)
    (bios / "xbox_hdd.qcow2").write_bytes(b"q")
    toml = tmp_path / "data" / "xemu" / "xemu" / "xemu.toml"
    toml.parent.mkdir(parents=True)
    toml.write_text(TOML)
    return toml, bios


def context(rom, pads=(), **settings):
    return Context(system="xbox", rom=str(rom), config=Cfg(**settings), emulator="xemu", controllers=list(pads))


def test_system_files_are_found_by_size(home):
    _, bios = home
    found = xemu.find_system_files(bios)
    assert found == {"bootrom_path": str(bios / "mcpx_1.0.bin"), "flashrom_path": str(bios / "Complex_4627.bin"),
                     "eeprom_path": str(bios / "eeprom.bin"), "hdd_path": str(bios / "xbox_hdd.qcow2")}


def test_configure_rewrites_and_creates_keys_and_stays_valid_toml(home, tmp_path):
    toml, bios = home
    pad = Controller(player=1, index=0, guid=GUID, name="PS4")
    assert xemu.configure(toml, context(tmp_path / "jeu.iso", [pad]), bios)
    data = tomllib.loads(toml.read_text())
    assert data["sys"]["files"]["bootrom_path"] == str(bios / "mcpx_1.0.bin")
    assert data["general"]["skip_boot_anim"] is False and data["general"]["show_welcome"] is True  # non touchés
    assert data["input"]["bindings"]["port1"] == GUID


def test_real_sparse_file_gets_missing_keys(home, tmp_path):
    toml, bios = home
    toml.write_text("[general]\nshow_welcome = false\n\n[input]\ngamepad_mappings = [\n    { gamepad_id = 'abc'}\n    ]\n\n"
                    "[sys.files]\neeprom_path = '/x/eeprom.bin'\n")
    pad = Controller(player=1, index=0, guid=GUID)
    xemu.configure(toml, context(tmp_path / "jeu.iso", [pad]), bios)
    data = tomllib.loads(toml.read_text())
    assert data["sys"]["files"]["hdd_path"] == str(bios / "xbox_hdd.qcow2")
    assert data["input"]["bindings"] == {"port1": GUID, "port1_driver": "usb-xbox-gamepad"}  # section créée
    assert data["input"]["gamepad_mappings"] == [{"gamepad_id": "abc"}]
    assert data["general"]["show_welcome"] is False


def test_autoconfig_off_keeps_pads(home, tmp_path):
    toml, bios = home
    pad = Controller(player=1, index=0, guid=GUID)
    xemu.configure(toml, context(tmp_path / "jeu.iso", [pad], xemu_autoconfig="0"), bios)
    assert tomllib.loads(toml.read_text())["input"]["bindings"]["port1"] == ""


def test_bios_directory_ignores_case(tmp_path):
    (tmp_path / "Xbox").mkdir()
    assert xemu.bios_directory(tmp_path) == tmp_path / "Xbox"
    assert xemu.bios_directory(tmp_path / "vide") == tmp_path / "vide" / "xbox"


def test_missing_config_is_left_alone(home, tmp_path):
    toml, bios = home
    toml.unlink()
    assert xemu.configure(toml, context(tmp_path / "jeu.iso"), bios) is False
    assert not toml.exists()


def test_generate_uses_xemu_command_line(home, tmp_path):
    rom = tmp_path / "Halo.iso"
    rom.write_bytes(b"x")
    command = xemu.Xemu().generate(context(rom))
    assert command.argv == ["/usr/bin/xemu", "-full-screen", "-dvd_path", str(rom)]


def test_appimage_is_found(tmp_path, monkeypatch, esne_env):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(standalone.shutil, "which", lambda n: None)
    image = tmp_path / ".local" / "bin" / "xemu-v0.8.0-x86_64.AppImage"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"x")
    image.chmod(0o755)
    rom = tmp_path / "Halo.iso"
    rom.write_bytes(b"x")
    assert xemu.Xemu().generate(context(rom)).argv[0] == str(image)


def test_render_settings_are_written_as_valid_toml(home, tmp_path):
    toml, bios = home
    xemu.configure(toml, context(tmp_path / "jeu.iso", [], xemu_scale="3", xemu_aspect="16x9"), bios)
    data = tomllib.loads(toml.read_text())
    assert data["display"]["quality"]["surface_scale"] == 3
    assert data["display"]["ui"]["aspect_ratio"] == "16x9"
    assert data["display"]["window"]["fullscreen_on_startup"] is False  # intact


def test_invalid_render_settings_are_ignored(home, tmp_path):
    toml, bios = home
    xemu.configure(toml, context(tmp_path / "jeu.iso", [], xemu_scale="40", xemu_aspect="rond"), bios)
    assert "surface_scale" not in toml.read_text() and "aspect_ratio" not in toml.read_text()
