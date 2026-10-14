# SPDX-License-Identifier: GPL-3.0-or-later
from esne import cores
from esne.esctl.commands import install_core


def test_classify():
    assert cores.classify("mgba") == ("official", "libretro-mgba")
    assert cores.classify("fceumm") == ("aur", "libretro-fceumm")
    assert "libretro-fbneo-git" in cores.aur_names()
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


def test_install_refuses_unknown():
    never = lambda argv: (_ for _ in ()).throw(AssertionError("ne doit rien lancer"))
    assert install_core.run(["x; rm -rf /"], call=never) == install_core.EXIT_UNKNOWN


def test_install_aur_builds_then_installs(tmp_path, monkeypatch):
    monkeypatch.setattr(install_core, "assistant", lambda: None)
    monkeypatch.setattr(install_core.shutil, "which", lambda name: "/usr/bin/" + name)
    calls = []
    pkg = tmp_path / "libretro-fceumm-git-1-1-x86_64.pkg.tar.zst"
    # le premier nom n'existe pas dans l'AUR, le second oui
    build = lambda name: pkg if name == "libretro-fceumm-git" else None
    assert install_core.run(["fceumm"], call=lambda argv: calls.append(argv) or 0, build=build) == 0
    assert calls == [["pkexec", cores.AUR_HELPER, str(pkg)]]


def test_install_aur_with_paru_uses_pkexec_as_sudo(monkeypatch):
    monkeypatch.setattr(install_core, "assistant", lambda: "paru")
    calls = []
    results = iter([1, 0])  # premier nom refusé, second accepté
    code = install_core.run(["fbneo"], call=lambda argv: calls.append(argv) or next(results))
    assert code == 0
    assert calls == [["paru", "-S", "--needed", "--noconfirm", "--sudo", "pkexec", "libretro-fbneo"],
                     ["paru", "-S", "--needed", "--noconfirm", "--sudo", "pkexec", "libretro-fbneo-git"]]


def test_install_aur_build_failure_skips_install(monkeypatch):
    monkeypatch.setattr(install_core, "assistant", lambda: None)
    monkeypatch.setattr(install_core.shutil, "which", lambda name: "/usr/bin/" + name)
    never = lambda argv: (_ for _ in ()).throw(AssertionError("ne doit rien installer"))
    assert install_core.run(["fceumm"], call=never, build=lambda p: None) == install_core.EXIT_AUR


def test_build_aur_clone_make_and_pick_package(tmp_path):
    calls = []

    def fake(argv, cwd=None):
        calls.append(argv[0])
        if argv[0] == "makepkg":
            (tmp_path / "libretro-stella" / "libretro-stella-1-1-x86_64.pkg.tar.zst").write_text("")
            (tmp_path / "libretro-stella" / "libretro-stella-debug-1-1-x86_64.pkg.tar.zst").write_text("")
        elif argv[0] == "git":
            (tmp_path / "libretro-stella").mkdir()
            (tmp_path / "libretro-stella" / "PKGBUILD").write_text("")
        return 0

    built = install_core.build_aur("libretro-stella", call=fake, base=tmp_path)
    assert built.name == "libretro-stella-1-1-x86_64.pkg.tar.zst" and calls == ["git", "makepkg"]


def test_every_catalog_core_is_known():
    from esne import catalog
    for entry in catalog.systems().values():
        for emulator, core, _ in catalog.choices(entry):
            if emulator == "libretro" and core:
                assert cores.classify(core)[0] != "unknown", core
