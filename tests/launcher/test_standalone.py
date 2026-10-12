# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from esne import errors
from esne.errors import LaunchError
from esne.generators import standalone
from esne.generators.base import Context


class Cfg:
    def get(self, key, default=None):
        return default


def ctx(emulator, rom, system="wii"):
    return Context(system=system, rom=str(rom), config=Cfg(), emulator=emulator)


@pytest.fixture
def fake_which(monkeypatch):
    available = {"dolphin-emu", "steam", "wine"}
    monkeypatch.setattr(standalone.shutil, "which", lambda name: f"/usr/bin/{name}" if name in available else None)
    return available


def test_dolphin_command(esne_env, fake_which, tmp_path):
    rom = tmp_path / "Jeu.rvz"
    rom.write_bytes(b"x")
    command = standalone.Standalone().generate(ctx("dolphin", rom))
    assert command.argv == ["/usr/bin/dolphin-emu", "-b", "-e", str(rom)]


def test_steam_uses_file_content(esne_env, fake_which, tmp_path):
    rom = tmp_path / "Half-Life.steam"
    rom.write_text("70\n")
    command = standalone.Standalone().generate(ctx("steam", rom, "steam"))
    assert command.argv == ["/usr/bin/steam", "steam://rungameid/70"]


def test_wine_runs_from_rom_dir(esne_env, fake_which, tmp_path):
    rom = tmp_path / "jeu.exe"
    rom.write_bytes(b"MZ")
    command = standalone.Standalone().generate(ctx("wine", rom, "windows"))
    assert command.argv == ["/usr/bin/wine", str(rom)] and command.cwd == str(tmp_path)


def test_missing_binary_is_204_with_hint(esne_env, fake_which, tmp_path):
    with pytest.raises(LaunchError) as exc:
        standalone.Standalone().generate(ctx("rpcs3", tmp_path / "a.iso", "ps3"))
    assert exc.value.code == errors.EMULATOR_MISSING and "rpcs3" in exc.value.message


def test_unknown_emulator_is_203(esne_env):
    with pytest.raises(LaunchError) as exc:
        standalone.Standalone().generate(ctx("inexistant", "/r/a.iso"))
    assert exc.value.code == errors.UNKNOWN_EMULATOR


def test_is_installed(esne_env, fake_which):
    assert standalone.is_installed("dolphin") and not standalone.is_installed("rpcs3")
    assert not standalone.is_installed("libretro")  # pas d'"args": géré par RetroArch
