# SPDX-License-Identifier: GPL-3.0-or-later
import xml.etree.ElementTree as ET

import pytest

from esne.generators import cemu, standalone
from esne.generators.base import Context, Controller

GUID = "030000004c050000cc09000000006800"


class Cfg:
    def __init__(self, **values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)


def pad(player, guid=GUID, name="PS4 Controller"):
    return Controller(player=player, index=player - 1, guid=guid, name=name)


@pytest.fixture
def cemu_home(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr(standalone.shutil, "which", lambda n: f"/usr/bin/{n}" if n in ("cemu", "Cemu") else None)
    return tmp_path / "xdg" / "Cemu"


def context(rom, pads, **settings):
    return Context(system="wiiu", rom=str(rom), config=Cfg(**settings), emulator="cemu", controllers=pads)


def test_uuid_counts_identical_guids():
    pads = [pad(1), pad(2, "o" * 32), pad(3)]
    assert [cemu.pad_uuid(pads, i) for i in range(3)] == [f"0_{GUID}", "0_" + "o" * 32, f"1_{GUID}"]


def test_profile_is_pro_controller_with_all_mappings():
    root = ET.fromstring(cemu.profile_xml(pad(1), "0_x"))
    assert root.findtext("type") == "Wii U Pro Controller"
    assert root.findtext("controller/uuid") == "0_x"
    entries = root.findall("controller/mappings/entry")
    assert len(entries) == len(cemu.SDL_PRO_MAPPING)
    assert len({e.findtext("mapping") for e in entries}) == len(entries)


def test_write_profiles_skips_pads_without_guid_and_caps_at_four(tmp_path):
    pads = [pad(1, ""), *[pad(i, f"{i:0>32}") for i in range(2, 9)]]
    written = cemu.write_profiles(pads, tmp_path)
    assert [p.name for p in written] == [f"controller{i}.xml" for i in range(4)]


def test_set_graphic_api(tmp_path):
    settings = tmp_path / "settings.xml"
    assert not cemu.set_graphic_api(settings, "vulkan")  # absent: rien n'est créé
    assert not settings.exists()
    settings.write_text("<content><Graphic><api>0</api></Graphic></content>")
    assert cemu.set_graphic_api(settings, "vulkan")
    assert ET.parse(settings).getroot().findtext("Graphic/api") == "1"
    assert not cemu.set_graphic_api(settings, "vulkan")
    assert not cemu.set_graphic_api(settings, "nimporte")
    settings.write_text("pas du xml")
    assert not cemu.set_graphic_api(settings, "opengl")


def test_flatpak_config_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert cemu.config_dir(["flatpak", "run", "info.cemu.Cemu"]) == tmp_path / ".var/app/info.cemu.Cemu/config/Cemu"


def test_generate_writes_profiles_and_api(cemu_home, tmp_path):
    cemu_home.mkdir(parents=True)
    (cemu_home / "settings.xml").write_text("<content/>")
    rom = tmp_path / "Jeu.wua"
    rom.write_bytes(b"x")
    command = cemu.Cemu().generate(context(rom, [pad(1)], cemu_api="vulkan"))
    assert command.argv == ["/usr/bin/cemu", "-f", "-g", str(rom)]
    assert (cemu_home / "controllerProfiles" / "controller0.xml").is_file()
    assert ET.parse(cemu_home / "settings.xml").getroot().findtext("Graphic/api") == "1"


def test_autoconfig_can_be_disabled(cemu_home, tmp_path):
    rom = tmp_path / "Jeu.wua"
    rom.write_bytes(b"x")
    cemu.Cemu().generate(context(rom, [pad(1)], cemu_autoconfig="0"))
    assert not (cemu_home / "controllerProfiles").exists()


def test_reuses_the_guid_cemu_wrote_for_the_same_model(tmp_path):
    cemu_guid = "03009b514c050000cc09000011810000"  # même fabricant/produit, CRC et version SDL3
    target = tmp_path / "controllerProfiles"
    target.mkdir()
    (target / "controller0.xml").write_text(cemu.profile_xml(pad(1), f"0_{cemu_guid}"))
    cemu.write_profiles([pad(1)], tmp_path)
    assert ET.parse(target / "controller0.xml").getroot().findtext("controller/uuid") == f"0_{cemu_guid}"
    # un autre modèle ne la reprend pas
    other = "030000007e050000092000000000" + "0000"
    cemu.write_profiles([pad(1, other)], tmp_path)
    assert ET.parse(target / "controller0.xml").getroot().findtext("controller/uuid") == f"0_{other}"


def test_settings_are_created_and_changed(tmp_path):
    settings = tmp_path / "settings.xml"
    settings.write_text("<content><console_language>2</console_language><Graphic><api>1</api><VSync>0</VSync></Graphic></content>")
    ctx = context(tmp_path / "a.wua", [], cemu_language="1", cemu_vsync="1", cemu_volume="25", cemu_fps="true", cemu_upscale="9")
    changed = cemu.set_settings(settings, ctx)
    root = ET.parse(settings).getroot()
    assert root.findtext("console_language") == "1" and root.findtext("Graphic/VSync") == "1"
    assert root.findtext("Audio/TVVolume") == "25" and root.findtext("Graphic/Overlay/FPS") == "true"
    assert root.findtext("Graphic/api") == "1" and root.find("Graphic/UpscaleFilter") is None  # valeur invalide ignorée
    assert "console_language" in changed
    assert cemu.set_settings(settings, ctx) == []  # déjà appliqué
    assert cemu.set_settings(tmp_path / "absent.xml", ctx) == []
