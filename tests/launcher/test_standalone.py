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
    assert command.argv == ["esne-steam-run", "70", "--", "/usr/bin/steam", "-silent", "steam://rungameid/70"]


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


def test_glob_candidate_picks_latest_executable(tmp_path, monkeypatch):
    for name in ("Cemu-2.5.AppImage", "Cemu-2.6.AppImage"):
        file = tmp_path / name
        file.write_text("")
        file.chmod(0o755)
    (tmp_path / "Cemu-2.7.AppImage").write_text("")  # non exécutable: ignoré
    found = standalone.find_program([str(tmp_path / "Cemu*.AppImage")], which=lambda n: None)
    assert found == [str(tmp_path / "Cemu-2.6.AppImage")]


def test_flatpak_candidate_requires_the_app(monkeypatch):
    monkeypatch.setattr(standalone, "_flatpak_installed", lambda flatpak, app: app == "a.b.C")
    which = lambda n: "/usr/bin/flatpak" if n == "flatpak" else None
    assert standalone.find_program(["flatpak run x.y.Z"], which) is None
    assert standalone.find_program(["flatpak run x.y.Z", "flatpak run a.b.C"], which) == ["/usr/bin/flatpak", "run", "a.b.C"]


def test_xenia_appimage_is_found_and_gets_the_game(esne_env, monkeypatch, tmp_path):
    home = tmp_path / "home"
    bin_dir = home / ".local" / "bin"
    bin_dir.mkdir(parents=True)
    old = bin_dir / "xenia_canary_linux-native-2026.09.17-x86_64.AppImage"
    new = bin_dir / "xenia_canary_linux-native-2026.10.05.1-x86_64.AppImage"
    for f in (old, new):
        f.write_bytes(b"x")
        f.chmod(0o755)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(standalone.shutil, "which", lambda name: None)
    rom = tmp_path / "Jeu.iso"
    rom.write_bytes(b"x")
    command = standalone.Standalone().generate(ctx("xenia", rom, "xbox360"))
    assert command.argv == [str(new), "--fullscreen=true", str(rom)]


def _xenia(esne_env, monkeypatch, tmp_path, settings):
    from esne.generators import xenia
    exe = tmp_path / "xenia"
    exe.write_bytes(b"x")
    exe.chmod(0o755)
    monkeypatch.setattr(standalone.shutil, "which", lambda name: str(exe) if name == "xenia" else None)
    rom = tmp_path / "Jeu.iso"
    rom.write_bytes(b"x")
    class Settings:
        def get(self, key, default=None):
            return settings.get(key, default)
    c = Context(system="xbox360", rom=str(rom), config=Settings(), emulator="xenia")
    return xenia.Xenia().generate(c), rom


def test_xenia_video_options_come_before_the_game(esne_env, monkeypatch, tmp_path):
    command, rom = _xenia(esne_env, monkeypatch, tmp_path, {
        "xenia_resolution": "2", "xenia_aa": "fxaa", "xenia_af": "5"})
    assert command.argv[-1] == str(rom)
    for option in ("--draw_resolution_scale_x=2", "--draw_resolution_scale_y=2",
                   "--postprocess_antialiasing=fxaa", "--anisotropic_override=5", "--fullscreen=true"):
        assert option in command.argv


def test_xenia_unset_and_invalid_options_are_not_passed(esne_env, monkeypatch, tmp_path):
    command, rom = _xenia(esne_env, monkeypatch, tmp_path, {"xenia_scaling": "dlaa"})
    assert command.argv[1:] == ["--fullscreen=true", str(rom)]
