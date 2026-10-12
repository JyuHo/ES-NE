# SPDX-License-Identifier: GPL-3.0-or-later

import json


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


def test_layout_same_ratio_scales_the_window():
    area = bezels.Area(24, 10, 144, 88, 192, 108)
    assert bezels.layout(area, (1920, 1080)) == (240, 100, 1440, 880)


def test_layout_other_ratio_keeps_game_proportions_in_stretched_window():
    area = bezels.Area(24, 10, 144, 88, 192, 108)
    # 16:10: image étirée en hauteur (x1,11), le jeu garde 1440x880 et reste centré dans la fenêtre étirée
    assert bezels.layout(area, (1920, 1200)) == (240, 160, 1440, 880)
    assert bezels.layout(area, (1920, 1200), stretch="0") is None
    assert bezels.layout(area, (3440, 1440), stretch="auto") is None   # 21:9: trop éloigné
    assert bezels.layout(area, (3440, 1440), stretch="1") is not None


def test_find_image_system_then_default(tmp_path):
    (tmp_path / "tbp" / "systems").mkdir(parents=True)
    (tmp_path / "tbp" / "systems" / "snes.png").write_bytes(b"")
    (tmp_path / "tbp" / "default.png").write_bytes(b"")
    dirs = [tmp_path]
    assert bezels.find_image("tbp", "snes", dirs).name == "snes.png"
    assert bezels.find_image("tbp", "nes", dirs).name == "default.png"
    assert bezels.find_image("missing", "snes", dirs) is None


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
    make_bezel(tmp_path / "data" / "decorations" / "thebezelproject" / "systems" / "snes.png")
    return tmp_path


def test_bezel_settings_with_set_chosen(env):
    s = retroarch.bezel_settings(context({"bezel": "thebezelproject"}))
    assert s["input_overlay_enable"] == "true"
    assert s["aspect_ratio_index"] == str(retroarch.RATIOS.index("custom"))
    assert (s["custom_viewport_x"], s["custom_viewport_width"]) == ("0", "1440")
    assert "snes.png" in open(s["input_overlay"]).read()


def test_bezel_auto_uses_installed_tbp_and_none_disables(env):
    assert retroarch.bezel_settings(context({"bezel": ""}))["input_overlay_enable"] == "true"
    assert retroarch.bezel_settings(context({"bezel": "none"})) == {}


def test_bezel_auto_without_install_is_empty(env):
    ctx = Context(system="nes", rom="a.nes", config=Cfg({}), core="fceumm")
    assert retroarch.bezel_settings(ctx) == {}


def test_bezel_viewport_is_relative_to_the_centered_one(env, monkeypatch):
    monkeypatch.setattr(retroarch, "screen_size", lambda: (1920, 1200))
    monkeypatch.setattr(retroarch, "vulkan_available", lambda: True)
    s = retroarch.bezel_settings(context({"bezel": "thebezelproject"}))
    # fenêtre voulue (240, 160, 1440, 880); centrée elle serait en (240, 160): écart nul
    assert (s["custom_viewport_x"], s["custom_viewport_y"]) == ("0", "0")
    assert (s["custom_viewport_width"], s["custom_viewport_height"]) == ("1440", "880")
    assert s["video_driver"] == "vulkan"
    assert "overlay0_full_screen = true" in open(s["input_overlay"]).read()


def test_bezel_off_center_window_gives_signed_offset(env, monkeypatch):
    monkeypatch.setattr(retroarch, "screen_size", lambda: (1920, 1080))
    # zone de jeu non centrée dans l'image (trou décalé vers la droite et le bas): écart signé par rapport au centrage
    make_bezel(env / "data" / "decorations" / "shifted" / "systems" / "snes.png", hole=(60, 20, 180, 100))
    s = retroarch.bezel_settings(context({"bezel": "shifted", "video_driver": "glcore"}))
    # fenêtre voulue (600, 200, 1200, 800) sur 1920x1080; centrée: ((1920-1200)/2, (1080-800)/2) = (360, 140)
    assert (s["custom_viewport_x"], s["custom_viewport_y"]) == ("240", "60") and s["video_driver"] == "glcore"


def test_build_settings_includes_bezel(env):
    s = retroarch.build_settings(context({"bezel": "thebezelproject", "ratio": "16/9"}))
    assert s["aspect_ratio_index"] == str(retroarch.RATIOS.index("custom"))


# ---- esctl thebezelproject ----------------------------------------------------

PNG = b"\x89PNG\r\n\x1a\nrest"


def fake_get(files):
    def get(url):
        if url == tbp.API.format(repo="bezelproject-SNES"):
            return json.dumps([{"name": n, "type": "file"} for n in files] + [{"name": "GameBezels", "type": "dir"}]).encode()
        return PNG
    return get


def test_install_downloads_only_the_system_image_and_remove_cleans(tmp_path):
    base = tmp_path / "decorations" / "thebezelproject"
    (base / "games" / "snes").mkdir(parents=True)  # reste d'une ancienne version
    assert tbp.install("snes", get=fake_get(["Super-Nintendo.cfg", "Super-Nintendo.png"]), base=base) == 0
    assert (base / "systems" / "snes.png").read_bytes() == PNG
    assert tbp.remove("snes", base=base) == 0
    assert not (base / "systems" / "snes.png").exists() and not (base / "games" / "snes").exists()
    assert not base.exists()  # plus aucun bezel: le jeu de décorations disparaît du menu d'ES


def test_install_removes_legacy_system_set(tmp_path):
    base = tmp_path / "decorations" / "thebezelproject"
    legacy = tmp_path / "decorations" / "thebezelproject-system" / "systems"
    legacy.mkdir(parents=True)
    (legacy / "snes.png").write_bytes(PNG)
    assert tbp.install("snes", get=fake_get(["a.png"]), base=base) == 0
    assert not (tmp_path / "decorations" / "thebezelproject-system").exists()
    assert (base / "systems" / "snes.png").is_file()


def test_pick_image_prefers_horizontal():
    assert tbp.pick_image(["MAME-Vertical.png", "MAME-Horizontal.png", "x.cfg"]) == "MAME-Horizontal.png"
    assert tbp.pick_image(["a.cfg"]) is None


def test_install_rejects_unknown_system_non_png_and_empty_listing(tmp_path):
    assert tbp.install("unknown", get=fake_get([]), base=tmp_path) == 1
    assert tbp.install("snes", get=fake_get([]), base=tmp_path) == 1
    bad = lambda url: json.dumps([{"name": "a.png", "type": "file"}]).encode() if "api." in url else b"<html>"
    assert tbp.install("snes", get=bad, base=tmp_path) == 1
    assert not (tmp_path / "systems").exists()


def test_list_marks_installed(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("ESNE_DATA_DIR", str(tmp_path))
    (tmp_path / "decorations" / "thebezelproject" / "systems").mkdir(parents=True)
    (tmp_path / "decorations" / "thebezelproject" / "systems" / "snes.png").write_bytes(PNG)
    lines = tbp.list_lines()
    assert any(l.startswith("[I] snes https://github.com/thebezelproject/bezelproject-SNES") for l in lines)
    assert any(l.startswith("[A] nes ") for l in lines)
    assert tbp.run(["list"]) == 0 and "[I] snes" in capsys.readouterr().out
