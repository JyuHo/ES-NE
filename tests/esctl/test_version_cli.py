import subprocess
import sys
from pathlib import Path

import pytest

from esne import __version__
from esne.esctl import runner
from esne.esctl.cli import main
from esne.esctl.commands import version

SRC = str(Path(__file__).resolve().parents[2] / "src")


def test_version_from_share_file(tmp_path, monkeypatch, capsys):
    (tmp_path / "esne.version").write_text("\n  2026.10-rc1  \nignored\n")
    monkeypatch.setenv("ESNE_SHARE_DIR", str(tmp_path))
    assert main(["version"]) == 0
    assert capsys.readouterr().out == "2026.10-rc1\n"


def test_version_falls_back_to_package(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("ESNE_SHARE_DIR", str(tmp_path))       # dossier sans esne.version
    assert main(["version"]) == 0
    assert capsys.readouterr().out == __version__ + "\n"


def test_version_extra(tmp_path, capsys):
    osr = tmp_path / "os-release"
    osr.write_text('NAME="CachyOS Linux"\nPRETTY_NAME="CachyOS Linux"\nID=cachyos\n')
    assert version.read_distribution(osr) == "CachyOS Linux"
    assert version.read_distribution(tmp_path / "absent") == ""


def test_version_bad_option(capsys):
    assert main(["version", "--nope"]) == 2


def test_has(fake):
    assert main(["has", "version"]) == 0
    assert main(["has", "inexistante"]) == 1
    assert main(["has"]) == 2
    assert main(["has", "a", "b"]) == 2


def test_commands_lists_only_usable(fake, capsys, monkeypatch):
    from esne.esctl.commands import install_core, keyboard, padsinfo, timezone
    # ces commandes dépendent de la machine (sysfs, timedatectl): on les neutralise pour ce test
    monkeypatch.setattr(padsinfo, "available", lambda: False)
    monkeypatch.setattr(timezone, "available", lambda: False)
    monkeypatch.setattr(keyboard, "available", lambda: False)
    monkeypatch.setattr(install_core, "available", lambda: False)
    assert main(["commands"]) == 0
    assert capsys.readouterr().out.splitlines() == ["info", "preupdate-gamelists-hook", "swissknife", "systems", "thebezelproject", "version"]
    fake.tools.update({"pactl", "xrandr"})
    assert main(["commands"]) == 0
    assert capsys.readouterr().out.splitlines() == ["audio", "config", "info", "preupdate-gamelists-hook", "resolution", "swissknife", "systems", "thebezelproject", "version"]


def test_unknown_command_and_help(capsys):
    assert main(["frobnicate"]) == 2
    assert "inconnue" in capsys.readouterr().err
    assert main([]) == 2
    assert main(["help"]) == 0
    out = capsys.readouterr().out
    assert all(name in out for name in ("has", "audio", "resolution", "version"))


# --- sous-processus réels: ce que le frontend exécute vraiment ----------------------------

def _esctl(args, env_extra=None, path=None):
    import os
    env = {"PATH": path or os.environ["PATH"], "PYTHONPATH": SRC, "HOME": "/nonexistent",
           "ESNE_SHARE_DIR": "/nonexistent"}
    env.update(env_extra or {})
    return subprocess.run([sys.executable, "-m", "esne.esctl", *args], env=env, capture_output=True, text=True)


def test_subprocess_exit_codes():
    assert _esctl(["version"]).returncode == 0
    assert _esctl(["has", "version"]).returncode == 0
    assert _esctl(["has", "nope"]).returncode == 1
    assert _esctl(["nope"]).returncode == 2


def test_subprocess_audio_with_a_real_fake_pactl(tmp_path):
    """Un faux pactl (script shell) sur le PATH: vérifie runner.run + analyse JSON de bout en bout."""
    pactl = tmp_path / "pactl"
    pactl.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  "--format=json list sinks") echo \'[{"name": "sink_a", "description": "Sortie A"}]\' ;;\n'
        '  "get-default-sink") echo sink_a ;;\n'
        '  "set-default-sink sink_a") exit 0 ;;\n'
        "  *) echo \"inattendu: $*\" >&2; exit 1 ;;\n"
        "esac\n")
    pactl.chmod(0o755)
    path = f"{tmp_path}:/usr/bin:/bin"

    assert _esctl(["has", "audio"], path=path).returncode == 0
    listed = _esctl(["audio", "list"], path=path)
    assert listed.returncode == 0
    assert listed.stdout == "auto\tAuto\nsink_a\tSortie A\n"
    assert _esctl(["audio", "get"], path=path).stdout == "sink_a\n"
    assert _esctl(["audio", "set", "sink_a"], path=path).returncode == 0
    assert _esctl(["audio", "set", "autre"], path=path).returncode == 1


def test_runner_real():
    assert runner.run(["definitely-not-a-command-xyz"]).returncode == 127
    assert runner.run(["sh", "-c", "echo hi; exit 3"]).returncode == 3
    assert runner.run(["sh", "-c", "echo hi"]).stdout == "hi\n"
    assert runner.run(["sleep", "5"], timeout=0.2).returncode == 124
