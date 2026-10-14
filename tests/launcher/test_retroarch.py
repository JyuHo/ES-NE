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
    assert ra.RATIOS.index("core") == 22 and ra.RATIOS.index("custom") == 23 and ra.RATIOS.index("8/3") == 14
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


def test_default_hotkeys(esne_env):
    s = ra.build_settings(ctx_for())
    assert s["input_enable_hotkey_btn"] == "4"
    assert s["input_exit_emulator_btn"] == "6"
    assert s["input_menu_toggle_btn"] == "8"


def test_hotkeys_need_enable_button(esne_env):
    from esne.generators.base import Context
    ctx = ctx_for()
    ctx.config.get = lambda key, default=None: "none" if key == "hotkey_enable" else default
    s = ra.build_settings(ctx)
    assert "input_exit_emulator_btn" not in s and "input_menu_toggle_btn" not in s


def test_user_settings(esne_env):
    s = ra.build_settings(ctx_for({"snes.smooth": "0", "snes.ratio": "16/9", "global.rewind": "1", "snes.integerscale": "1"}))
    assert s["video_smooth"] == "false"
    assert s["aspect_ratio_index"] == "1"
    assert s["rewind_enable"] == "true"
    assert s["video_scale_integer"] == "true"


def test_ratio_disables_core_provided_aspect(esne_env):
    ctx = ctx_for()
    ctx.config.get = lambda key, default=None: "16/9" if key == "ratio" else default
    s = ra.build_settings(ctx)
    assert s["aspect_ratio_index"] == "1" and s["video_aspect_ratio_auto"] == "false"


def test_slang_shader_picks_vulkan_or_glcore_and_driver_can_be_overridden(esne_env, tmp_path, monkeypatch):
    preset = tmp_path / "crt-geom.slangp"
    preset.write_text("")
    monkeypatch.setattr(ra, "find_shader", lambda name, directories=None: preset)
    ctx = ctx_for()
    ctx.config.get = lambda key, default=None: "crt-geom" if key == "shaderset" else default
    monkeypatch.setattr(ra, "vulkan_available", lambda *a: False)
    assert ra.build_settings(ctx)["video_driver"] == "glcore"
    monkeypatch.setattr(ra, "vulkan_available", lambda *a: True)
    assert ra.build_settings(ctx)["video_driver"] == "vulkan"
    ctx.config.get = lambda key, default=None: {"shaderset": "crt-geom", "video_driver": "gl"}.get(key, default)
    assert ra.build_settings(ctx)["video_driver"] == "gl"
    assert "video_driver" not in ra.build_settings(ctx_for())


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


def test_generate_command_passes_shader_with_set_shader(emulation, tmp_path, monkeypatch):
    preset = tmp_path / "crt-geom.slangp"
    preset.write_text("")
    monkeypatch.setattr(ra, "find_shader", lambda name, directories=None: preset)
    ctx = ctx_for()
    ctx.core = "snes9x"
    ctx.config.get = lambda key, default=None: "crt-geom" if key == "shaderset" else default
    argv = ra.GENERATOR().generate(ctx).argv
    assert argv[argv.index("--set-shader") + 1] == str(preset) and argv[-1] == "/roms/snes/mario.sfc"


def test_state_options_from_es(esne_env):
    s = ra.build_settings(ctx_for(extra=["-state_slot", "3", "-autosave", "1"]))
    assert s["state_slot"] == "3" and s["savestate_auto_load"] == "true" and s["savestate_auto_index"] == "true"
    s = ra.build_settings(ctx_for({"global.incrementalsavestates": "0"}))
    assert s["savestate_auto_index"] == "false" and s["savestate_max_keep"] == "50" and "state_slot" not in s
    assert "state_slot" not in ra.build_settings(ctx_for(extra=["-state_slot", "abc"]))


def test_state_file_auto_loads_and_slot_file_is_entry(emulation):
    s = ra.build_settings(ctx_for(extra=["-state_file", "/s/mario.state.auto"]))
    assert s["savestate_auto_load"] == "true"
    ctx = ctx_for(extra=["-state_slot", "2", "-state_file", "/s/mario.state2"])
    ctx.core = "snes9x"
    argv = ra.GENERATOR().generate(ctx).argv
    assert argv[argv.index("-e") + 1] == "2"
    ctx = ctx_for(extra=["-state_slot", "2", "-state_file", "/s/mario.state.auto"])
    ctx.core = "snes9x"
    assert "-e" not in ra.GENERATOR().generate(ctx).argv


def test_monitor_is_one_based_for_retroarch(esne_env):
    assert ra.build_settings(ctx_for(extra=["-monitor", "1"]))["video_monitor_index"] == "2"
    assert "video_monitor_index" not in ra.build_settings(ctx_for())
    assert "video_monitor_index" not in ra.build_settings(ctx_for(extra=["-monitor", "x"]))


def test_netplay_host(esne_env):
    ctx = ctx_for({"global.netplay.nickname": "Moi", "global.netplay.port": "55435", "global.netplay.password": "pw"},
                  extra=["-netplaymode", "host"])
    assert ra.netplay_args(ctx) == ["--host", "--port", "55435", "--nick", "Moi"]
    s = ra.netplay_settings(ctx)
    assert s["netplay_ip_port"] == "55435" and s["netplay_password"] == "pw" and s["netplay_start_as_spectator"] == "false"
    assert s["netplay_use_mitm_server"] == "false"


def test_netplay_client_and_spectator_with_relay(esne_env):
    extra = ["-netplaymode", "client", "-netplayip", "10.0.0.2", "-netplayport", "5000", "-netplaysession", "abc", "-netplaypass", "pw"]
    ctx = ctx_for({"global.netplay.relay": "nyc"}, extra=extra)
    assert ra.netplay_args(ctx) == ["--connect", "10.0.0.2", "--port", "5000", "--mitm-session", "abc"]
    s = ra.netplay_settings(ctx)
    assert s["netplay_ip_address"] == "10.0.0.2" and s["netplay_password"] == "pw"
    assert s["netplay_use_mitm_server"] == "true" and s["netplay_mitm_server"] == "nyc"
    spectator = ra.netplay_settings(ctx_for(extra=["-netplaymode", "spectator", "-netplayip", "h", "-netplaypass", "x"]))
    assert spectator["netplay_start_as_spectator"] == "true" and spectator["netplay_spectate_password"] == "x"
    assert "netplay_password" not in spectator


def test_no_netplay_without_mode(esne_env):
    assert ra.netplay_args(ctx_for()) == [] and ra.netplay_settings(ctx_for()) == {}
    assert ra.netplay_args(ctx_for(extra=["-netplaymode", "bogus"])) == []


def test_generate_command_netplay_before_rom(emulation):
    ctx = ctx_for(extra=["-netplaymode", "host"])
    ctx.core = "snes9x"
    argv = ra.GENERATOR().generate(ctx).argv
    assert "--host" in argv and argv[-1] == "/roms/snes/mario.sfc"


def test_archive_is_extracted_for_a_core_that_does_not_read_it(emulation, tmp_path, monkeypatch):
    import zipfile
    zip_path = tmp_path / "Mario World (USA).zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("rom.sfc", "DATA")
    info = tmp_path / "info"
    info.mkdir()
    (info / "snes9x_libretro.info").write_text('supported_extensions = "smc|sfc|swc"\n')
    monkeypatch.setattr(ra, "DEFAULT_INFO_DIRS", [str(info)])
    ctx = ctx_for(rom=str(zip_path))
    ctx.core = "snes9x"
    rom = ra.GENERATOR().generate(ctx).argv[-1]
    assert rom.endswith("Mario World (USA).sfc") and open(rom).read() == "DATA"  # renommé comme l'archive


def test_states_not_sorted_in_subfolders(esne_env):
    settings = ra.build_settings(ctx_for())
    assert settings["sort_savestates_enable"] == "false"
    assert settings["sort_savestates_by_content_enable"] == "false"
