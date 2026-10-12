# SPDX-License-Identifier: GPL-3.0-or-later
import io
import json
import zipfile

import pytest

from esne import bezels
from esne.esctl.commands import thebezelproject as tbp
from esne.generators import retroarch
from esne.generators.base import Context

PIL = pytest.importorskip("PIL.Image")


def make_bezel(path, size=(192, 108), hole=(24, 10, 168, 98)):
    image = PIL.new("RGBA", size, (10, 10, 10, 255))
    for x in range(hole[0], hole[2]):
        for y in range(hole[1], hole[3]):
            image.putpixel((x, y), (0, 0, 0, 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return path


def test_detect_area_finds_transparent_window(tmp_path):
    area = bezels.detect_area(make_bezel(tmp_path / "b.png"))
    assert (area.x, area.y, area.width, area.height) == (24, 10, 144, 88)
    assert (area.image_width, area.image_height) == (192, 108)


def test_detect_area_opaque_center_gives_none(tmp_path):
    PIL.new("RGBA", (40, 30), (1, 1, 1, 255)).save(tmp_path / "x.png")
    assert bezels.detect_area(tmp_path / "x.png") is None


def test_info_file_overrides_detection(tmp_path):
    image = make_bezel(tmp_path / "b.png")
    (tmp_path / "b.png.info").write_text(json.dumps({"width": 192, "height": 108, "top": 5, "left": 6, "bottom": 7, "right": 8}))
    area = bezels.game_area(image)
    assert (area.x, area.y, area.width, area.height) == (6, 5, 178, 96)


def test_viewport_scales_and_refuses_other_ratio():
    area = bezels.Area(24, 10, 144, 88, 192, 108)
    assert bezels.viewport(area, (1920, 1080)) == (240, 100, 1440, 880)
    assert bezels.viewport(area, (1920, 1200)) is None
    assert bezels.viewport(area, (1920, 1200), stretch=True) == (240, 111, 1440, 978)


def test_find_image_order_and_fuzzy_name(tmp_path):
    games = tmp_path / "tbp" / "games" / "snes"
    games.mkdir(parents=True)
    (games / "Zelda (USA).png").write_bytes(b"")
    (tmp_path / "tbp" / "systems").mkdir()
    (tmp_path / "tbp" / "systems" / "snes.png").write_bytes(b"")
    dirs = [tmp_path]
    assert bezels.find_image("tbp", "snes", "Zelda (USA)", dirs).name == "Zelda (USA).png"
    assert bezels.find_image("tbp", "snes", "Zelda (Europe)", dirs).name == "Zelda (USA).png"
    assert bezels.find_image("tbp", "snes", "Other", dirs).name == "snes.png"
    assert bezels.find_image("missing", "snes", "Other", dirs) is None


class Cfg:
    def __init__(self, values): self.values = values
    def get(self, key, default=None): return self.values.get(key, default)


def context(values, rom="/roms/snes/Zelda (USA).sfc"):
    return Context(system="snes", rom=rom, config=Cfg(values), core="snes9x")


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("ESNE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("ESNE_SHARE_DIR", str(tmp_path / "share"))
    monkeypatch.setenv("ESNE_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(retroarch, "screen_size", lambda: (1920, 1080))
    make_bezel(tmp_path / "data" / "decorations" / "thebezelproject" / "games" / "snes" / "Zelda (USA).png")
    return tmp_path


def test_bezel_settings_with_set_chosen(env):
    s = retroarch.bezel_settings(context({"bezel": "thebezelproject"}))
    assert s["input_overlay_enable"] == "true"
    assert s["aspect_ratio_index"] == str(retroarch.RATIOS.index("custom"))
    assert (s["custom_viewport_x"], s["custom_viewport_width"]) == ("240", "1440")
    assert "Zelda" in open(s["input_overlay"]).read()


def test_bezel_auto_uses_installed_tbp_and_none_disables(env):
    assert retroarch.bezel_settings(context({"bezel": ""}))["input_overlay_enable"] == "true"
    assert retroarch.bezel_settings(context({"bezel": "none"})) == {}


def test_bezel_auto_without_install_is_empty(env):
    ctx = Context(system="nes", rom="a.nes", config=Cfg({}), core="fceumm")
    assert retroarch.bezel_settings(ctx) == {}


def test_bezel_wrong_screen_ratio_is_skipped(env, monkeypatch):
    monkeypatch.setattr(retroarch, "screen_size", lambda: (1920, 1200))
    assert retroarch.bezel_settings(context({"bezel": "thebezelproject"})) == {}


def test_build_settings_includes_bezel(env):
    s = retroarch.build_settings(context({"bezel": "thebezelproject", "ratio": "16/9"}))
    assert s["aspect_ratio_index"] == str(retroarch.RATIOS.index("custom"))


# ---- esctl thebezelproject ----------------------------------------------------

def fake_zip():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("bezelproject-SNES-master/retroarch/overlay/GameBezels/SNES/Zelda (USA).png", b"png1")
        z.writestr("bezelproject-SNES-master/retroarch/overlay/GameBezels/SNES/Zelda (USA).cfg", b"cfg")
        z.writestr("bezelproject-SNES-master/retroarch/overlay/Super-Nintendo-Entertainment-System.png", b"sys")
        z.writestr("bezelproject-SNES-master/retroarch/overlay/GameBezels/SNES/../../../evil.png", b"x")
        z.writestr("bezelproject-SNES-master/README.md", b"x")
    return buffer.getvalue()


def test_install_and_remove(tmp_path, capsys):
    assert tbp.install("snes", fetch=lambda url: fake_zip(), base=tmp_path) == 0
    assert (tmp_path / "games" / "snes" / "Zelda (USA).png").read_bytes() == b"png1"
    assert (tmp_path / "systems" / "snes.png").read_bytes() == b"sys"
    assert not (tmp_path / "games" / "snes" / "Zelda (USA).cfg").exists()
    assert tbp.remove("snes", base=tmp_path) == 0
    assert not (tmp_path / "games" / "snes").exists() and not (tmp_path / "systems" / "snes.png").exists()


def test_install_rejects_unknown_system_and_empty_zip(tmp_path):
    assert tbp.install("unknown", fetch=lambda u: b"", base=tmp_path) == 1
    empty = io.BytesIO()
    zipfile.ZipFile(empty, "w").close()
    assert tbp.install("snes", fetch=lambda u: empty.getvalue(), base=tmp_path) == 1


def test_list_marks_installed(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("ESNE_DATA_DIR", str(tmp_path))
    (tmp_path / "decorations" / "thebezelproject" / "games" / "snes").mkdir(parents=True)
    lines = tbp.list_lines()
    assert any(l.startswith("[I] snes https://github.com/thebezelproject/bezelproject-SNES") for l in lines)
    assert any(l.startswith("[A] nes ") for l in lines)
    assert tbp.run(["list"]) == 0 and "[I] snes" in capsys.readouterr().out
