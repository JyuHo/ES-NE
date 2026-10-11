import pytest

from esne.cli import build_context
from esne.config import Config
from esne.errors import BAD_ARGUMENTS, LaunchError

# Ligne produite par ES pour le système snes avec une manette (voir FileData::getlaunchCommand)
ES_LINE = [
    "-p1index", "0", "-p1guid", "03008fe54c050000cc09000000006800", "-p1path", "/dev/hidraw6",
    "-p1name", "PS4 Controller", "-p1nbbuttons", "13", "-p1nbhats", "1", "-p1nbaxes", "6",
    "-system", "snes", "-rom", "/roms/snes/Super Mario World (U).sfc",
    "-gameinfoxml", "", "-systemname", "Super Nintendo",
]


def test_es_command_line():
    ctx = build_context(ES_LINE, Config({}))
    assert ctx.system == "snes"
    assert ctx.rom == "/roms/snes/Super Mario World (U).sfc"
    assert ctx.system_name == "Super Nintendo"
    assert ctx.emulator == "" and ctx.core is None
    (pad,) = ctx.controllers
    assert (pad.player, pad.index, pad.name, pad.nbbuttons, pad.nbhats, pad.nbaxes) == (1, 0, "PS4 Controller", 13, 1, 6)
    assert pad.path == "/dev/hidraw6" and pad.guid.startswith("03008f")


def test_empty_emulator_and_core_from_unknown_variables():
    # ES remplace %EMULATOR% / %CORE% par une chaîne vide quand le système n'en définit pas
    ctx = build_context(["-system", "snes", "-rom", "r.sfc", "-emulator", "-core", "-gameinfoxml"], Config({}))
    assert ctx.emulator == "" and ctx.core is None


def test_explicit_emulator_and_core():
    ctx = build_context(["-system", "snes", "-rom", "r.sfc", "-emulator", "libretro", "-core", "bsnes"], Config({}))
    assert (ctx.emulator, ctx.core) == ("libretro", "bsnes")


def test_several_players_in_order():
    ctx = build_context(["-system", "snes", "-rom", "r", "-p2index", "1", "-p2name", "B", "-p1index", "0", "-p1name", "A"], Config({}))
    assert [(c.player, c.name) for c in ctx.controllers] == [(1, "A"), (2, "B")]


def test_extras_are_kept():
    ctx = build_context(["-system", "snes", "-rom", "r", "-netplaymode", "host", "-autosave", "1", "-state_slot", "2"], Config({}))
    assert ctx.extras == {"netplaymode": "host", "autosave": "1", "state_slot": "2"}


def test_scoped_settings_layers():
    cfg = Config({"global.ratio": "16/9", "snes.ratio": "4/3", 'snes["a.sfc"].ratio': "core"})
    assert build_context(["-system", "snes", "-rom", "/x/a.sfc"], cfg).setting("ratio") == "core"
    assert build_context(["-system", "snes", "-rom", "/x/b.sfc"], cfg).setting("ratio") == "4/3"
    assert build_context(["-system", "nes", "-rom", "/x/b.nes"], cfg).setting("ratio") == "16/9"


@pytest.mark.parametrize("argv", [
    [],
    ["-system", "snes"],
    ["-rom", "r"],
    ["-system", "snes", "-rom", "r", "-p1index", "abc"],
    ["-system", "snes", "-rom", "r", "-inconnu", "x"],
])
def test_bad_arguments(argv):
    with pytest.raises(LaunchError) as error:
        build_context(argv, Config({}))
    assert error.value.code == BAD_ARGUMENTS
