import pytest

from esne import paths
from esne.config import Config
from esne.cli import build_context
from esne.errors import CORE_MISSING, EMULATOR_MISSING, LaunchError
from esne.generators import retroarch as ra


def ctx_for(settings=None, extra=None, system="snes", rom="/roms/snes/mario.sfc"):
    return build_context(["-system", system, "-rom", rom, *(extra or [])], Config(settings or {}))


def test_truthy_and_quote():
    assert ra.truthy("1") and ra.truthy("true") and ra.truthy("YES")
    assert not ra.truthy("0") and not ra.truthy("false") and not ra.truthy("")
    assert ra.quote('a"b\\c') == '"a\\"b\\\\c"'


def test_ratio_table_matches_retroarch_enum():
    assert ra.RATIOS.index("4/3") == 0 and ra.RATIOS.index("16/9") == 1
    assert ra.RATIOS.index("core") == 21 and ra.RATIOS.index("full") == 23
    assert len(ra.RATIOS) == len(set(ra.RATIOS))


def test_default_settings(esne_env):
    s = ra.build_settings(ctx_for())
    assert s["video_fullscreen"] == "true" and s["config_save_on_exit"] == "false"
    assert s["savefile_directory"] == str(paths.data_dir() / "saves" / "snes")
    assert s["system_directory"] == str(paths.bios_dir())
    # rien n'est forcé quand l'utilisateur n'a rien demandé
    for key in ("video_smooth", "aspect_ratio_index", "rewind_enable", "savestate_auto_save", "video_shader"):
        assert key not in s


def test_joypad_driver_defaults_to_sdl2(esne_env):
    assert ra.build_settings(ctx_for())["input_joypad_driver"] == "sdl2"


def test_user_settings(esne_env):
    s = ra.build_settings(ctx_for({"snes.smooth": "0", "snes.ratio": "16/9", "global.rewind": "1", "snes.integerscale": "1"}))
    assert s["video_smooth"] == "false"
    assert s["aspect_ratio_index"] == "1"
    assert s["rewind_enable"] == "true"
    assert s["video_scale_integer"] == "true"


def test_unknown_ratio_is_ignored(esne_env):
    assert "aspect_ratio_index" not in ra.build_settings(ctx_for({"snes.ratio": "n'importe quoi"}))


def test_autosave_from_es_wins_over_config(esne_env):
    s = ra.build_settings(ctx_for({"snes.autosave": "0"}, ["-autosave", "1"]))
    assert s["savestate_auto_save"] == "true" and s["savestate_auto_load"] == "true"
    s = ra.build_settings(ctx_for({"snes.autosave": "1"}))
    assert s["savestate_auto_save"] == "true"


def test_shader_lookup(esne_env):
    shaders = paths.data_dir() / "shaders"
    shaders.mkdir()
    (shaders / "scanlines.slangp").write_text("")
    s = ra.build_settings(ctx_for({"snes.shaderset": "scanlines"}))
    assert s["video_shader_enable"] == "true" and s["video_shader"] == str(shaders / "scanlines.slangp")
    assert "video_shader" not in ra.build_settings(ctx_for({"snes.shaderset": "absent"}))
    assert "video_shader" not in ra.build_settings(ctx_for({"snes.shaderset": "none"}))


def test_write_config_format(esne_env):
    ctx = ctx_for({"snes.smooth": "1"})
    target = ra.write_config(ctx, ra.build_settings(ctx))
    assert target == paths.cache_dir() / "retroarch" / "snes.cfg"
    lines = target.read_text().splitlines()
    assert 'video_smooth = "true"' in lines
    assert all(" = " in line and line.endswith('"') for line in lines)
    assert (paths.data_dir() / "saves" / "snes").is_dir()


def test_find_binary_and_core(tmp_path):
    prog = tmp_path / "retroarch"
    prog.write_text("")
    which = lambda name: str(prog) if name == "retroarch" else None
    assert ra.find_binary(["absent", "retroarch"], which) == [str(prog)]
    assert ra.find_binary(["absent", "retroarch --verbose"], which) == [str(prog), "--verbose"]
    with pytest.raises(LaunchError) as error:
        ra.find_binary(["absent"], which)
    assert error.value.code == EMULATOR_MISSING

    (tmp_path / "snes9x_libretro.so").write_text("")
    assert ra.find_core("snes9x", [tmp_path]) == tmp_path / "snes9x_libretro.so"
    with pytest.raises(LaunchError) as error:
        ra.find_core("bsnes", [tmp_path])
    assert error.value.code == CORE_MISSING


def test_generate_command(emulation):
    ctx = ctx_for()
    ctx.core = "snes9x"
    command = ra.GENERATOR().generate(ctx)
    assert command.argv[0].endswith("retroarch")
    assert command.argv[1:3] == ["-L", str(emulation.core_dir / "snes9x_libretro.so")]
    assert command.argv[3] == "--appendconfig" and command.argv[-1] == "/roms/snes/mario.sfc"
