# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
import os
import signal
import subprocess
import sys
import time

from esne import paths
from esne.esctl.commands import preupdate_gamelists_hook, swissknife, systems

DATA = {
    "psx": [{"file": "a.bin", "md5": hashlib.md5(b"good").hexdigest()}, {"file": "b.bin", "md5": "0" * 32}, {"file": "sub/c.bin"}],
    "gba": [{"file": "gba_bios.bin", "md5": ["1" * 32, hashlib.md5(b"x").hexdigest()]}],
}


def test_report_statuses(tmp_path):
    (tmp_path / "a.bin").write_bytes(b"good")
    (tmp_path / "b.bin").write_bytes(b"bad")
    (tmp_path / "gba_bios.bin").write_bytes(b"x")
    lines = systems.report(data=DATA, bios=tmp_path)
    assert lines[0] == "> gba"
    assert lines[1].startswith("OK 1111") and lines[1].endswith(str(tmp_path / "gba_bios.bin"))
    assert lines[2] == "> psx"
    assert lines[3].split(" ")[0] == "OK"
    assert lines[4].split(" ")[0] == "INVALID"
    assert lines[5] == f"MISSING - {tmp_path / 'sub' / 'c.bin'}"


def test_report_filter_and_cli_output(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(systems, "entries", lambda: DATA)
    monkeypatch.setattr(paths, "bios_dir", lambda: tmp_path)
    assert systems.run(["--filter", "gba"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "> gba" and len(out) == 2
    assert systems.run(["--filter", "inconnu"]) == 0
    assert capsys.readouterr().out == ""
    assert systems.run(["--bad"]) == 2


def test_packaged_catalog_is_well_formed():
    for system, items in systems.entries().items():
        assert items, system
        for item in items:
            assert item["file"]
            md5 = item.get("md5")
            for value in md5 if isinstance(md5, list) else [md5] if md5 else []:
                assert len(str(value)) == 32, (system, item)


def test_emukill_terminates_process_group(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "emulator_pid_file", lambda: tmp_path / "emulator.pid")
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], start_new_session=True)
    (tmp_path / "emulator.pid").write_text(f"{child.pid}\n")
    try:
        assert swissknife.emukill(grace=3) == 0
        assert child.wait(timeout=5) == -signal.SIGTERM
    finally:
        if child.poll() is None:
            child.kill()


def test_emukill_without_pid_or_dead_process(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "emulator_pid_file", lambda: tmp_path / "emulator.pid")
    assert swissknife.emukill() == 0
    (tmp_path / "emulator.pid").write_text("not a pid")
    assert swissknife.emukill() == 0
    (tmp_path / "emulator.pid").write_text("999999")
    assert swissknife.emukill() == 0
    assert swissknife.run(["--autre"]) == 2


def test_hook_runs_executable_scripts_in_order(tmp_path):
    for name, code in (("20-b", 0), ("10-a", 0), ("30-fail", 3)):
        script = tmp_path / name
        script.write_text(f"#!/bin/sh\necho {name} >> {tmp_path}/log\nexit {code}\n")
        script.chmod(0o755)
    (tmp_path / "ignored").write_text("#!/bin/sh\necho x >> log\n")  # non exécutable
    assert preupdate_gamelists_hook.run([], directory=tmp_path) == 1
    assert (tmp_path / "log").read_text().split() == ["10-a", "20-b", "30-fail"]
    assert preupdate_gamelists_hook.run([], directory=tmp_path / "absent") == 0
