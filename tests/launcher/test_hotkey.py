# SPDX-License-Identifier: GPL-3.0-or-later
import os
import struct
import sys
import time

import pytest

from esne import hotkey
from esne.generators.base import Context

SELECT, START, SOUTH = hotkey.BUTTON_CODES["select"], hotkey.BUTTON_CODES["start"], hotkey.BUTTON_CODES["south"]


def event(code, value):
    return struct.pack("llHHi", 0, 0, hotkey.EV_KEY, code, value)


def test_required_codes_default_and_disabled():
    assert hotkey.required_codes(lambda k, d=None: d) == {SELECT, START}
    assert hotkey.required_codes(lambda k, d=None: "none" if k == "hotkey_enable" else d) is None
    assert hotkey.required_codes(lambda k, d=None: "r3" if k == "hotkey_exit" else d) == {SELECT, hotkey.BUTTON_CODES["r3"]}


def test_is_gamepad_parses_kernel_bitmap():
    assert hotkey._is_gamepad("7fdb000000000000 0 0 0 0")  # bitmap d'une DS4 (BTN_SOUTH = bit 304)
    assert not hotkey._is_gamepad("120000 0 0 0 0")  # clavier sans bouton de manette


def fifo_watcher(tmp_path, fired):
    path = tmp_path / "event0"
    os.mkfifo(path)
    reader = hotkey.Watcher({SELECT, START}, lambda: fired.append(1), devices=lambda: [str(path)], rescan=0.1)
    # ouvrir en écriture débloque l'ouverture non bloquante du lecteur
    reader.start()
    time.sleep(0.3)
    return reader, os.open(path, os.O_WRONLY)


def test_combo_triggers_once(tmp_path):
    fired = []
    watcher, fd = fifo_watcher(tmp_path, fired)
    os.write(fd, event(SELECT, 1) + event(START, 1))
    watcher.join(2)
    os.close(fd)
    assert fired == [1] and watcher.triggered


def test_single_button_or_release_does_not_trigger(tmp_path):
    fired = []
    watcher, fd = fifo_watcher(tmp_path, fired)
    os.write(fd, event(SELECT, 1) + event(SOUTH, 1) + event(SELECT, 0) + event(START, 1))
    time.sleep(0.5)
    watcher.stop()
    watcher.join(2)
    os.close(fd)
    assert fired == [] and not watcher.triggered


@pytest.mark.skipif(sys.platform == "win32", reason="posix")
def test_launcher_stops_standalone_emulator_with_combo(esne_env, monkeypatch):
    from esne import launcher
    from esne.generators.base import Command

    class Cfg:
        def get(self, key, default=None):
            return default

    class Gen:
        external_hotkey = True

    class Instant(hotkey.Watcher):  # se déclenche aussitôt, sans manette
        def run(self):
            time.sleep(0.3)
            self.triggered = True
            self.on_trigger()

    monkeypatch.setattr(hotkey, "Watcher", Instant)
    started = time.monotonic()
    result = launcher.run_command(Command(argv=["sleep", "30"]), Context(system="wii", rom="/r/a", config=Cfg()), Gen())
    assert result.returncode == 0 and time.monotonic() - started < 10
