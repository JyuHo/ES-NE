# SPDX-License-Identifier: GPL-3.0-or-later
from esne import cores
from esne.esctl.commands import install_core


def test_classify():
    assert cores.classify("mgba") == ("official", "libretro-mgba")
    assert cores.classify("fceumm") == ("aur", "libretro-fceumm")
    assert cores.classify("nimporte") == ("unknown", "")


def test_hint_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("ESNE_MISSING_CORE_FILE", str(tmp_path / "hint"))
    cores.write_hint("mgba")
    assert (tmp_path / "hint").read_text() == "mgba\nlibretro-mgba\nofficial\n"
    cores.clear_hint()
    assert not (tmp_path / "hint").exists()


def test_install_official_calls_helper():
    calls = []
    assert install_core.run(["mgba"], call=lambda argv: calls.append(argv) or 0) == 0
    assert calls == [["pkexec", cores.HELPER, "mgba"]]


def test_install_refuses_aur_and_unknown():
    never = lambda argv: (_ for _ in ()).throw(AssertionError("ne doit rien lancer"))
    assert install_core.run(["fceumm"], call=never) == install_core.EXIT_AUR
    assert install_core.run(["x; rm -rf /"], call=never) == install_core.EXIT_UNKNOWN


def test_every_catalog_core_is_known():
    from esne import catalog
    for entry in catalog.systems().values():
        for emulator, core, _ in catalog.choices(entry):
            if emulator == "libretro" and core:
                assert cores.classify(core)[0] != "unknown", core
