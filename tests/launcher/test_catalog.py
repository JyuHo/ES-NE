import yaml

from esne import catalog


def test_builtin_default_choice():
    assert catalog.default_choice("snes") == ("libretro", "snes9x")
    assert catalog.default_choice("megadrive") == ("libretro", "genesis_plus_gx")
    assert catalog.default_choice("inconnu") == (None, None)


def test_lowest_priority_wins_then_file_order(tmp_path):
    (tmp_path / "systems.yml").write_text(yaml.safe_dump({
        "snes": {"emulators": {"libretro": {"a": {"priority": 5}, "b": {"priority": 2}, "c": {}}}},
        "x": {"emulators": {"libretro": {"first": {}, "second": {}}}},
    }, sort_keys=False))
    assert catalog.default_choice("snes", tmp_path) == ("libretro", "b")
    assert catalog.default_choice("x", tmp_path) == ("libretro", "first")


def test_user_file_overrides_builtin(tmp_path):
    (tmp_path / "systems.yml").write_text(yaml.safe_dump({"snes": {"emulators": {"libretro": {"bsnes": {"priority": 1}}}}}))
    assert catalog.default_choice("snes", tmp_path) == ("libretro", "bsnes")
    assert catalog.default_choice("nes", tmp_path) == ("libretro", "fceumm")   # le reste du catalogue est conservé


def test_invalid_user_file(tmp_path):
    import pytest
    from esne.errors import INVALID_CONFIG, LaunchError

    (tmp_path / "systems.yml").write_text("- pas\n- un dictionnaire\n")
    with pytest.raises(LaunchError) as error:
        catalog.systems(tmp_path)
    assert error.value.code == INVALID_CONFIG


def test_builtin_emulator_info():
    info = catalog.emulator_info("libretro")
    assert "retroarch" in info["binary"] and info["core_dirs"]
    assert catalog.emulator_info("dolphin") is None
