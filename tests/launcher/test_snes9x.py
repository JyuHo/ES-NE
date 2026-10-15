# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from esne.generators import snes9x, standalone
from esne.generators.base import Context


class Cfg:
    def __init__(self, **values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)


@pytest.fixture
def home(tmp_path, monkeypatch, esne_env):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setattr(standalone.shutil, "which", lambda n: f"/usr/bin/{n}" if n == "snes9x-gtk" else None)
    return tmp_path


def ctx(rom, **settings):
    return Context(system="snes", rom=str(rom), config=Cfg(**settings), emulator="snes9x")


CONF = ("[Display]\nAspectRatio             = 2       # 0: uncorrected\nBilinearFilter          = true    # Smoothes\n"
        "FullscreenOnOpen        = false   # x\nHardwareAcceleration    = vulkan  # none, opengl, xv, vulkan\n"
        "[OpenGL]\nVSync               = true\n[Sound]\nMuteSound               = false\n")


def write(home):
    conf = home / "cfg" / "snes9x" / "snes9x.conf"
    conf.parent.mkdir(parents=True)
    conf.write_text(CONF)
    return conf


def test_command_and_settings(home):
    conf = write(home)
    rom = home / "g.sfc"
    command = snes9x.Snes9x().generate(ctx(rom, snes9x_renderer="opengl", snes9x_aspect="4", snes9x_vsync="0",
                                           snes9x_bilinear="0", snes9x_mute="1", snes9x_rewind="50"))
    assert command.argv[-1] == str(rom)
    text = conf.read_text()
    assert "HardwareAcceleration    = opengl" in text and "AspectRatio             = 4" in text
    assert "BilinearFilter          = false" in text and "FullscreenOnOpen        = true" in text
    assert "VSync               = false" in text and "MuteSound               = true" in text
    assert "[Behavior]\nRewindBufferSize = 50\n" in text


def test_invalid_ignored_and_missing_file(home):
    conf = write(home)
    snes9x.Snes9x().generate(ctx(home / "g.sfc", snes9x_aspect="9"))
    assert "AspectRatio             = 2" in conf.read_text()
    conf.unlink()
    assert snes9x.Snes9x().generate(ctx(home / "g.sfc")).argv[-1] == str(home / "g.sfc")
