# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from esne.generators import eden, standalone
from esne.generators.base import Context, Controller

GUID = "030000004c050000cc09000011810000"
INI = f"""[DisabledAddOns]
size=0

[Controls]
player_0_connected\\default=true
player_0_connected=true
player_1_connected\\default=true
player_1_connected=false
player_0_button_a\\default=false
player_0_button_a="engine:sdl,guid:{GUID},port:0,button:1"
player_0_button_screenshot\\default=false
player_0_button_screenshot=[empty]
player_0_lstick\\default=false
player_0_lstick="engine:sdl,guid:{GUID},axis_x:0,offset_x:-0.000000,invert_y:+,port:0,axis_y:1,offset_y:0.000000,invert_x:+"
player_1_button_a\\default=false
player_1_button_a="engine:keyboard,code:67,toggle:0"

[Core]
use_multi_core=true
"""


class Cfg:
    def __init__(self, **values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)


def pad(player, guid):
    return Controller(player=player, index=player - 1, guid=guid, name="Pad")


@pytest.fixture
def ini(tmp_path):
    file = tmp_path / "qt-config.ini"
    file.write_text(INI)
    return file


def ctx(pads, **settings):
    return Context(system="switch", rom="/r/a.nsp", config=Cfg(**settings), emulator="eden", controllers=pads)


ES_GUID = "03008fe54c050000cc09000000006800"  # même modèle, GUID calculé par ES
EDEN_GUID = "030000004c050000cc09000000006800"  # ce que voit Eden: CRC du nom à zéro


def test_eden_guid_zeroes_the_name_crc():
    assert eden.eden_guid(ES_GUID) == EDEN_GUID


def test_template_ignores_empty_and_keyboard():
    guid, mapping = eden.read_template(INI.splitlines(keepends=True))
    assert guid == GUID and set(mapping) == {"button_a", "lstick"}


def test_second_pad_of_same_model_gets_port_1(ini):
    assert eden.configure(ini, ctx([pad(1, ES_GUID), pad(2, ES_GUID)]))
    text = ini.read_text()
    assert f'player_1_button_a="engine:sdl,guid:{EDEN_GUID},port:1,button:1"' in text
    assert "player_1_connected=true" in text and "player_1_connected\\default=false" in text
    assert f'player_0_button_a="engine:sdl,guid:{EDEN_GUID},port:0,button:1"' in text  # GUID corrigé aussi pour le joueur 1
    assert "engine:keyboard" not in text  # le clavier du joueur 2 est remplacé
    assert "[Core]\nuse_multi_core=true" in text  # le reste est conservé
    assert text.count("player_1_button_a=") == 1


def test_other_model_is_left_alone(ini):
    other = "030000007e050000092000000000" + "0000"
    eden.configure(ini, ctx([pad(1, ES_GUID), pad(2, other)]))
    assert 'player_1_button_a="engine:keyboard,code:67,toggle:0"' in ini.read_text()


def test_autoconfig_off_and_missing_file(ini, tmp_path):
    assert not eden.configure(ini, ctx([pad(1, ES_GUID)], eden_autoconfig="0"))
    assert not eden.configure(tmp_path / "absent.ini", ctx([pad(1, ES_GUID)]))


def test_generate_integration(tmp_path, monkeypatch, esne_env, ini):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    (tmp_path / "eden").mkdir()
    (tmp_path / "eden" / "qt-config.ini").write_text(INI)
    monkeypatch.setattr(standalone.shutil, "which", lambda n: f"/usr/bin/{n}" if n == "eden" else None)
    rom = tmp_path / "Jeu.nsp"
    rom.write_bytes(b"x")
    command = eden.Eden().generate(Context(system="switch", rom=str(rom), config=Cfg(), emulator="eden",
                                           controllers=[pad(1, ES_GUID), pad(2, ES_GUID)]))
    assert command.argv == ["/usr/bin/eden", "-f", "-g", str(rom)]
    assert "port:1" in (tmp_path / "eden" / "qt-config.ini").read_text()


REAL = """[Renderer]
backend=1
use_vsync\\default=false
use_vsync=1
anti_aliasing=2

[System]
language_index=2
region_index=2
use_docked_mode=1

[UI]
fullscreen=true
"""


def test_settings_are_written_in_the_right_sections(tmp_path):
    ini = tmp_path / "qt-config.ini"
    ini.write_text(REAL)
    assert eden.apply_settings(ini, ctx([], eden_vsync="2", eden_language="1", eden_docked="0", eden_filter="5"))
    text = ini.read_text()
    assert "use_vsync\\default=false\nuse_vsync=2\n" in text
    assert "language_index=1\n" in text and "use_docked_mode=0\n" in text
    assert "scaling_filter\\default=false\nscaling_filter=5\n" in text  # clé absente: créée
    assert "region_index=2\n" in text and "anti_aliasing=2\n" in text and "fullscreen=true\n" in text  # intacts


def test_settings_unset_invalid_or_missing_file_change_nothing(tmp_path):
    ini = tmp_path / "qt-config.ini"
    assert not eden.apply_settings(ini, ctx([], eden_vsync="2"))
    ini.write_text(REAL)
    assert not eden.apply_settings(ini, ctx([], eden_vsync="99", eden_language="6"))
    assert ini.read_text() == REAL


def test_resolution_uses_edens_own_indexes(tmp_path):
    ini = tmp_path / "qt-config.ini"
    ini.write_text(REAL)
    assert eden.apply_settings(ini, ctx([], eden_resolution="6"))
    assert "resolution_setup\\default=false\nresolution_setup=6\n" in ini.read_text()
    assert not eden.apply_settings(ini, ctx([], eden_resolution="4"))   # index de yuzu, pas d'Eden
