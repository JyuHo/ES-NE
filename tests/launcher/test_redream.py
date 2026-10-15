# SPDX-License-Identifier: GPL-3.0-or-later
from esne.generators import redream
from esne.generators.base import Context

CFG = "gamedir=/roms;\nmode=exclusive fullscreen\nres=3\naspect=16:9\nvsync=1\nregion=europe\nlanguage=french\ncable=vga\n"


class Cfg:
    def __init__(self, **values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)


def ctx(**settings):
    return Context(system="dreamcast", rom="/r/a.gdi", config=Cfg(**settings), emulator="redream")


def test_chosen_settings_replace_or_add_keys_and_keep_the_rest(tmp_path):
    cfg = tmp_path / "redream.cfg"
    cfg.write_text(CFG)
    values = redream.chosen(ctx(redream_region="usa", redream_language="english", redream_broadcast="ntsc"))
    assert redream.apply(cfg, values)
    lines = cfg.read_text().splitlines()
    assert "region=usa" in lines and "language=english" in lines and "broadcast=ntsc" in lines  # dont une clé créée
    assert "res=3" in lines and "gamedir=/roms;" in lines and "mode=exclusive fullscreen" in lines
    assert not redream.apply(cfg, values)  # déjà appliqué


def test_unset_invalid_or_missing_config_change_nothing(tmp_path):
    assert redream.chosen(ctx()) == {}
    assert redream.chosen(ctx(redream_res="40", redream_cable="scart")) == {}
    assert not redream.apply(tmp_path / "absent.cfg", {"res": "2"})


def test_config_is_found_next_to_the_binary(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "h"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "d"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "c"))
    bin_dir = tmp_path / "apps"
    bin_dir.mkdir()
    (bin_dir / "redream.cfg").write_text(CFG)
    assert redream.find_config(str(bin_dir / "redream")) == bin_dir / "redream.cfg"
    assert redream.find_config() is None
