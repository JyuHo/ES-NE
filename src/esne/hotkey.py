# SPDX-License-Identifier: GPL-3.0-or-later
"""Raccourci manette pour quitter un émulateur autonome (Select + Start par défaut).

RetroArch gère son propre raccourci; les autres émulateurs n'en ont pas. Pendant qu'ils tournent,
``es-launcher`` lit directement les manettes (evdev, sans dépendance) et ferme l'émulateur quand
la combinaison est maintenue.
"""
from __future__ import annotations

import ctypes
import logging
import os
import select
import struct
import threading
import time
from pathlib import Path

log = logging.getLogger(__name__)

EV_KEY = 1
BTN_GAMEPAD = 0x130  # BTN_SOUTH: présent sur toute manette

# noms de boutons (mêmes que pour RetroArch) -> codes evdev
BUTTON_CODES = {
    "south": 0x130, "east": 0x131, "north": 0x133, "west": 0x134,
    "l1": 0x136, "r1": 0x137, "select": 0x13A, "start": 0x13B, "guide": 0x13C, "l3": 0x13D, "r3": 0x13E,
}
DEFAULTS = {"hotkey_enable": "select", "hotkey_exit": "start"}

_EVENT = struct.Struct("llHHi")  # struct input_event: timeval, type, code, value


def required_codes(setting) -> set[int] | None:
    """Codes à maintenir pour quitter, ou None si le raccourci est désactivé."""
    codes = set()
    for name, default in DEFAULTS.items():
        button = str(setting(name, default)).lower()
        if button in ("none", "off", ""):
            return None
        if button not in BUTTON_CODES:
            log.warning("bouton inconnu pour %s ignoré: %s", name, button)
            return None
        codes.add(BUTTON_CODES[button])
    return codes


def _is_gamepad(caps: str) -> bool:
    words = caps.split()
    bits = 8 * ctypes.sizeof(ctypes.c_ulong)
    value = sum(int(word, 16) << (bits * i) for i, word in enumerate(reversed(words)))
    return bool(value >> BTN_GAMEPAD & 1)


def find_gamepads(sys_root="/sys/class/input", dev_root="/dev/input") -> list[str]:
    found = []
    for event in sorted(Path(sys_root).glob("event*")):
        try:
            caps = (event / "device" / "capabilities" / "key").read_text()
        except OSError:
            continue
        if _is_gamepad(caps) and (Path(dev_root) / event.name).exists():
            found.append(str(Path(dev_root) / event.name))
    return found


class Watcher(threading.Thread):
    """Appelle ``on_trigger`` une fois quand tous les boutons de ``codes`` sont enfoncés sur la même manette."""

    def __init__(self, codes: set[int], on_trigger, devices=find_gamepads, rescan: float = 2.0):
        super().__init__(daemon=True, name="esne-hotkey")
        self.codes = set(codes)
        self.on_trigger = on_trigger
        self.devices = devices
        self.rescan = rescan
        self._halt = threading.Event()
        self.triggered = False

    def stop(self) -> None:
        self._halt.set()

    def _open(self, opened: dict) -> None:
        for path in self.devices():
            if path in opened:
                continue
            try:
                opened[path] = (os.open(path, os.O_RDONLY | os.O_NONBLOCK), set())
                log.debug("raccourci manette: surveille %s", path)
            except OSError as exc:
                log.debug("raccourci manette: %s illisible (%s)", path, exc)

    def run(self) -> None:
        opened: dict[str, tuple[int, set[int]]] = {}
        next_scan = 0.0
        try:
            while not self._halt.is_set():
                if time.monotonic() >= next_scan:
                    self._open(opened)
                    next_scan = time.monotonic() + self.rescan
                if not opened:
                    self._halt.wait(0.5)
                    continue
                ready, _, _ = select.select([fd for fd, _ in opened.values()], [], [], 0.25)
                for path, (fd, pressed) in list(opened.items()):
                    if fd not in ready:
                        continue
                    try:
                        data = os.read(fd, _EVENT.size * 64)
                    except BlockingIOError:
                        continue
                    except OSError:  # manette débranchée
                        os.close(fd)
                        del opened[path]
                        continue
                    for offset in range(0, len(data) - _EVENT.size + 1, _EVENT.size):
                        _, _, etype, code, value = _EVENT.unpack_from(data, offset)
                        if etype != EV_KEY or code not in self.codes:
                            continue
                        (pressed.add if value else pressed.discard)(code)
                        if pressed >= self.codes:
                            self.triggered = True
                            self.on_trigger()
                            return
        finally:
            for fd, _ in opened.values():
                try:
                    os.close(fd)
                except OSError:
                    pass
