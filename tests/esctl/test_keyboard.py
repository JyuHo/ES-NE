# SPDX-License-Identifier: GPL-3.0-or-later
import subprocess

from esne.esctl.commands import keyboard


def fake(outputs, calls=None, code=0):
    def run(argv, **kwargs):
        if calls is not None:
            calls.append(argv)
        return subprocess.CompletedProcess(argv, code, outputs.get(tuple(argv[1:]), ""), "refusé" if code else "")
    return run


def test_list_layouts_and_variants(capsys):
    run = fake({("list-x11-keymap-layouts",): "fr\nus\n", ("list-x11-keymap-variants", "fr"): "oss\nazerty\n"})
    assert keyboard.run(["list-layouts"], run) == 0
    assert keyboard.run(["list-variants", "fr"], run) == 0
    assert capsys.readouterr().out.splitlines() == ["fr fr", "us us", "oss oss", "azerty azerty"]


def test_get_reads_status(capsys):
    status = "   X11 Layout: fr\n  X11 Variant: n/a\n"
    assert keyboard.run(["get"], fake({("status",): status})) == 0
    assert capsys.readouterr().out.strip() == "fr none"


def test_set_calls_localectl_with_empty_model():
    calls = []
    assert keyboard.run(["set", "fr", "none"], fake({}, calls)) == 0
    assert keyboard.run(["set", "us", "intl"], fake({}, calls)) == 0
    assert calls == [["localectl", "set-x11-keymap", "fr", "", ""], ["localectl", "set-x11-keymap", "us", "", "intl"]]


def test_set_rejects_odd_names_and_reports_polkit_failure(capsys):
    assert keyboard.run(["set", "fr; reboot"], fake({})) == 2
    assert keyboard.run(["list-variants", "../x"], fake({})) == 2
    assert keyboard.run(["set", "fr"], fake({}, code=1)) == 1
    assert "polkit" in capsys.readouterr().err
