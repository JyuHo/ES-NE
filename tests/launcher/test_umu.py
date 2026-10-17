# SPDX-License-Identifier: GPL-3.0-or-later
import xml.etree.ElementTree as ET

from esne import featurescfg
from esne.generators import standalone, umu
from esne.generators.base import Context


class Cfg:
    def __init__(self, **values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)


def make(tmp_path, monkeypatch, rom="Mon Jeu (2020).exe", which=("umu-run", "gamemoderun", "mangohud"), **settings):
    monkeypatch.setattr(standalone.shutil, "which", lambda name: f"/usr/bin/{name}" if name in which else None)
    monkeypatch.setattr(umu.shutil, "which", lambda name: f"/usr/bin/{name}" if name in which else None)
    file = tmp_path / rom
    file.write_bytes(b"MZ")
    ctx = Context(system="windows", rom=str(file), config=Cfg(**settings), emulator="umu")
    return umu.Umu().generate(ctx), file


def test_defaults_use_ge_proton_and_a_prefix_per_game(esne_env, tmp_path, monkeypatch):
    command, rom = make(tmp_path, monkeypatch)
    assert command.argv == ["/usr/bin/umu-run", str(rom)] and command.cwd == str(tmp_path)
    assert command.env["PROTONPATH"] == "GE-Proton"
    assert command.env["GAMEID"] == "mon-jeu-2020"
    assert command.env["WINEPREFIX"].endswith("/saves/windows/mon-jeu-2020")
    assert set(command.env) == {"GAMEID", "PROTONPATH", "WINEPREFIX"}  # rien d'autre tant que rien n'est choisi


def test_shared_prefix_and_proton_choice(esne_env, tmp_path, monkeypatch):
    command, _ = make(tmp_path, monkeypatch, umu_prefix="shared", umu_proton="UMU-Latest")
    assert command.env["WINEPREFIX"].endswith("/saves/windows/shared") and command.env["PROTONPATH"] == "UMU-Latest"
    command, _ = make(tmp_path, monkeypatch, umu_proton="../evil")
    assert command.env["PROTONPATH"] == "GE-Proton"


def test_sync_choices(esne_env, tmp_path, monkeypatch):
    for choice, expected in {"auto": {}, "esync": {"PROTON_NO_FSYNC": "1"}, "fsync": {"PROTON_NO_ESYNC": "1"},
                             "none": {"PROTON_NO_FSYNC": "1", "PROTON_NO_ESYNC": "1"}}.items():
        command, _ = make(tmp_path, monkeypatch, umu_sync=choice)
        assert {k: v for k, v in command.env.items() if k.startswith("PROTON_NO")} == expected


def test_d3d_fsr_mangohud_and_frame_rate(esne_env, tmp_path, monkeypatch):
    command, _ = make(tmp_path, monkeypatch, umu_d3d="wined3d", umu_fsr="1", umu_fsr_strength="1", umu_mangohud="1", umu_fps="60")
    assert command.env["PROTON_USE_WINED3D"] == "1"
    assert command.env["WINE_FULLSCREEN_FSR"] == "1" and command.env["WINE_FULLSCREEN_FSR_STRENGTH"] == "1"
    assert command.env["MANGOHUD"] == "1" and command.env["DXVK_FRAME_RATE"] == "60"
    command, _ = make(tmp_path, monkeypatch, umu_fsr_strength="3", umu_fps="0")  # sans FSR, la netteté n'a pas d'effet
    assert "WINE_FULLSCREEN_FSR_STRENGTH" not in command.env and "DXVK_FRAME_RATE" not in command.env


def test_invalid_values_are_ignored(esne_env, tmp_path, monkeypatch):
    command, _ = make(tmp_path, monkeypatch, umu_sync="turbo", umu_fsr="2", umu_fps="abc", umu_vdesktop="grand")
    assert set(command.env) == {"GAMEID", "PROTONPATH", "WINEPREFIX"} and command.argv[1].endswith(".exe")


def test_gamemode_wraps_the_command_and_is_skipped_when_missing(esne_env, tmp_path, monkeypatch):
    command, rom = make(tmp_path, monkeypatch, umu_gamemode="1")
    assert command.argv == ["/usr/bin/gamemoderun", "/usr/bin/umu-run", str(rom)]
    command, rom = make(tmp_path, monkeypatch, which=("umu-run",), umu_gamemode="1")
    assert command.argv == ["/usr/bin/umu-run", str(rom)]


def test_virtual_desktop_runs_explorer_from_the_game_folder(esne_env, tmp_path, monkeypatch):
    command, rom = make(tmp_path, monkeypatch, umu_vdesktop="1920x1080")
    assert command.argv == ["/usr/bin/umu-run", "explorer", "/desktop=esne,1920x1080", rom.name]
    assert command.cwd == str(tmp_path)


def test_slug():
    assert umu.slug("Hollow Knight (v1.5)") == "hollow-knight-v1-5" and umu.slug("???") == "game"


def test_features_declare_the_umu_options():
    emulator = next(e for e in ET.fromstring(featurescfg.render()).findall("emulator") if e.get("name") == "umu")
    assert {f.get("value") for f in emulator.findall("feature")} == {
        "umu_proton", "umu_prefix", "umu_d3d", "umu_sync", "umu_fsr", "umu_fsr_strength", "umu_vdesktop", "umu_mangohud",
        "umu_gamemode", "umu_fps"}
