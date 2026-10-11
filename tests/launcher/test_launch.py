"""Lancement complet avec un faux retroarch: ce qu'ES voit (code de sortie, fichier d'erreur)."""
from esne import errors, paths
from esne.cli import main


def line(rom="/roms/snes/Mario World.sfc", *extra, system="snes"):
    return ["-system", system, "-rom", rom, "-gameinfoxml", "", "-systemname", "Super Nintendo", *extra]


def test_default_core_launch(emulation):
    assert main(line()) == 0
    args = emulation.args()
    assert args[:2] == ["-L", str(emulation.core_dir / "snes9x_libretro.so")]
    assert args[-1] == "/roms/snes/Mario World.sfc"         # chemin avec espace transmis tel quel
    config = args[args.index("--appendconfig") + 1]
    assert config == str(paths.cache_dir() / "retroarch" / "snes.cfg")


def test_core_from_es_argument(emulation):
    assert main(line("/r/a.sfc", "-emulator", "libretro", "-core", "bsnes")) == 0
    assert "bsnes_libretro.so" in emulation.args()[1]


def test_core_from_user_config(emulation):
    (paths.config_dir() / "esne.conf").write_text('snes.core=bsnes\nsnes["Mario World.sfc"].core=snes9x\n')
    assert main(line("/roms/snes/other.sfc")) == 0
    assert "bsnes_libretro.so" in emulation.args()[1]
    assert main(line("/roms/snes/Mario World.sfc")) == 0
    assert "snes9x_libretro.so" in emulation.args()[1]


def test_settings_reach_retroarch_config(emulation):
    (paths.config_dir() / "esne.conf").write_text("snes.ratio=16/9\nsnes.smooth=0\n")
    assert main(line()) == 0
    text = (paths.cache_dir() / "retroarch" / "snes.cfg").read_text()
    assert 'aspect_ratio_index = "1"' in text and 'video_smooth = "false"' in text


def test_emulator_failure_is_reported_as_200(emulation, monkeypatch):
    monkeypatch.setenv("FAKE_RETROARCH_EXIT", "1")
    assert main(line()) == errors.EMULATOR_EXITED


def test_missing_core_is_205(emulation):
    assert main(line("/r/a.sfc", "-core", "absent")) == errors.CORE_MISSING


def test_system_without_known_core_is_205(emulation):
    (paths.config_dir() / "systems.yml").write_text("exotic:\n  name: Exotique\n  emulators:\n    libretro: {}\n")
    assert main(line("/r/a.x", system="exotic")) == errors.CORE_MISSING


def test_unknown_system_is_203(emulation):
    assert main(line("/r/a.x", system="nexistepas")) == errors.UNKNOWN_EMULATOR


def test_unknown_emulator_is_203(emulation):
    assert main(line("/r/a.sfc", "-emulator", "dolphin")) == errors.UNKNOWN_EMULATOR


def test_missing_retroarch_is_204(emulation):
    (emulation.bin_dir / "retroarch").unlink()
    assert main(line()) == errors.EMULATOR_MISSING


def test_bad_arguments_is_201(emulation):
    assert main(["-system", "snes"]) == errors.BAD_ARGUMENTS


def test_invalid_user_catalog_is_202(emulation):
    (paths.config_dir() / "systems.yml").write_text("- liste\n")
    assert main(line()) == errors.INVALID_CONFIG


def test_unexpected_error_writes_message_for_es(emulation, monkeypatch):
    from esne.generators import retroarch

    def boom(*a, **k):
        raise RuntimeError("panne")

    monkeypatch.setattr(retroarch.RetroArch, "generate", boom)
    assert main(line()) == errors.OTHER_ERROR
    assert "panne" in errors.launch_error_file().read_text()


def test_launcher_log_is_written(emulation):
    main(line())
    log = (paths.state_dir() / "logs" / "es-launcher.log").read_text()
    assert "système=snes émulateur=libretro core=snes9x" in log
