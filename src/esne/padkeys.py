# SPDX-License-Identifier: GPL-3.0-or-later
"""Traduction manette -> clavier/souris pour les jeux qui n'acceptent que le clavier (ports PortMaster, etc.).

Équivalent de ``gptokeyb`` de PortMaster: lit le même fichier de correspondance ``.gptk`` (``a = enter``,
``left_analog_up = up``, ``right_analog_left = mouse_movement_left``...). Les manettes sont lues avec evdev
et les touches sont émises par un clavier virtuel uinput.

    esne-padkeys [--grab] jeu.gptk -- ./jeu          # traduit pendant que « ./jeu » tourne
    esne-padkeys jeu.gptk                             # traduit jusqu'à SIGTERM/SIGINT

Si uinput n'est pas utilisable (droits, module absent), la commande est quand même lancée, sans traduction.
"""
from __future__ import annotations

import argparse
import logging
import re
import selectors
import signal
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

log = logging.getLogger("esne.padkeys")

STICK_THRESHOLD = 0.5  # fraction de la course d'un axe à partir de laquelle il compte comme « appuyé »
MOUSE_SPEED = 900.0  # pixels par seconde à pleine inclinaison (ou bouton directionnel)
TICK = 0.016

# source gptk -> code evdev (noms de ecodes)
BUTTON_SOURCES = {
    "a": "BTN_SOUTH", "b": "BTN_EAST", "x": "BTN_WEST", "y": "BTN_NORTH",
    "l1": "BTN_TL", "r1": "BTN_TR", "l2": "BTN_TL2", "r2": "BTN_TR2", "l3": "BTN_THUMBL", "r3": "BTN_THUMBR",
    "start": "BTN_START", "back": "BTN_SELECT", "guide": "BTN_MODE",
    "up": "BTN_DPAD_UP", "down": "BTN_DPAD_DOWN", "left": "BTN_DPAD_LEFT", "right": "BTN_DPAD_RIGHT",
}
# axe evdev -> (source si valeur négative, source si valeur positive)
AXIS_SOURCES = {
    "ABS_HAT0X": ("left", "right"), "ABS_HAT0Y": ("up", "down"),
    "ABS_X": ("left_analog_left", "left_analog_right"), "ABS_Y": ("left_analog_up", "left_analog_down"),
    "ABS_RX": ("right_analog_left", "right_analog_right"), "ABS_RY": ("right_analog_up", "right_analog_down"),
    "ABS_Z": (None, "l2"), "ABS_RZ": (None, "r2"),
}
KEY_ALIASES = {
    "enter": "KEY_ENTER", "return": "KEY_ENTER", "esc": "KEY_ESC", "escape": "KEY_ESC", "space": "KEY_SPACE",
    "tab": "KEY_TAB", "backspace": "KEY_BACKSPACE", "ctrl": "KEY_LEFTCTRL", "lctrl": "KEY_LEFTCTRL",
    "rctrl": "KEY_RIGHTCTRL", "alt": "KEY_LEFTALT", "lalt": "KEY_LEFTALT", "ralt": "KEY_RIGHTALT",
    "shift": "KEY_LEFTSHIFT", "lshift": "KEY_LEFTSHIFT", "rshift": "KEY_RIGHTSHIFT", "pageup": "KEY_PAGEUP",
    "pagedown": "KEY_PAGEDOWN", "minus": "KEY_MINUS", "equals": "KEY_EQUAL", "comma": "KEY_COMMA",
    "period": "KEY_DOT", "slash": "KEY_SLASH", "backslash": "KEY_BACKSLASH", "semicolon": "KEY_SEMICOLON",
    "apostrophe": "KEY_APOSTROPHE", "leftbracket": "KEY_LEFTBRACE", "rightbracket": "KEY_RIGHTBRACE",
    "grave": "KEY_GRAVE", "capslock": "KEY_CAPSLOCK", "pause": "KEY_PAUSE", "printscreen": "KEY_SYSRQ",
}
MOUSE_BUTTONS = {"mouse_left": "BTN_LEFT", "mouse_right": "BTN_RIGHT", "mouse_middle": "BTN_MIDDLE"}
MOUSE_MOVES = {"mouse_movement_up": (0, -1), "mouse_movement_down": (0, 1),
               "mouse_movement_left": (-1, 0), "mouse_movement_right": (1, 0)}
MOUSE_WHEEL = {"mouse_wheel_up": 1, "mouse_wheel_down": -1}


def parse_gptk(text: str) -> dict[str, str]:
    """``source = cible`` -> dict. Lignes vides, commentaires (#) et options inconnues (deadzone_*, mouse_scale...) ignorés."""
    mapping = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if "=" not in line:
            continue
        source, target = (part.strip().lower() for part in line.split("=", 1))
        if source in BUTTON_SOURCES or source.startswith(("left_analog_", "right_analog_")):
            if target:
                mapping[source] = target
    return mapping


def key_name(target: str) -> str | None:
    """Nom evdev (``KEY_*``/``BTN_*``) d'une cible clavier ou bouton de souris, ou None si ce n'est pas une touche."""
    if target in MOUSE_BUTTONS:
        return MOUSE_BUTTONS[target]
    if target in KEY_ALIASES:
        return KEY_ALIASES[target]
    if re.fullmatch(r"[a-z0-9]", target) or re.fullmatch(r"f([1-9]|1[0-2])", target):
        return "KEY_" + target.upper()
    if re.fullmatch(r"(up|down|left|right|home|end|insert|delete)", target):
        return "KEY_" + target.upper()
    return None


class Translator:
    """Machine à états pure (sans evdev): sources de manette appuyées -> touches, déplacements souris, molette."""

    def __init__(self, mapping: dict[str, str]):
        self.mapping = dict(mapping)
        self.pressed: dict[tuple, float] = {}  # (manette, source) -> intensité 0..1
        self.keys = Counter()  # nom de touche -> nombre de sources qui l'enfoncent

    def set_source(self, pad, source: str, strength: float) -> list[tuple[str, int, int]]:
        """Met à jour une source (0 = relâchée). Renvoie des événements (``key``|``wheel``, nom/valeur, 1|0)."""
        target = self.mapping.get(source)
        was = (pad, source) in self.pressed
        now = strength > 0
        if now:
            self.pressed[(pad, source)] = strength
        else:
            self.pressed.pop((pad, source), None)
        if target is None or was == now:
            return []
        if target in MOUSE_WHEEL:
            return [("wheel", MOUSE_WHEEL[target], 1)] if now else []
        name = key_name(target)
        if name is None:
            return []
        if now:
            self.keys[name] += 1
            return [("key", name, 1)] if self.keys[name] == 1 else []
        self.keys[name] -= 1
        if self.keys[name] <= 0:
            del self.keys[name]
            return [("key", name, 0)]
        return []

    def mouse_vector(self) -> tuple[float, float]:
        dx = dy = 0.0
        for (_pad, source), strength in self.pressed.items():
            move = MOUSE_MOVES.get(self.mapping.get(source, ""))
            if move:
                dx += move[0] * strength
                dy += move[1] * strength
        return dx, dy

    def release_all(self) -> list[tuple[str, int, int]]:
        events = [("key", name, 0) for name in self.keys]
        self.keys.clear()
        self.pressed.clear()
        return events

    def used_keys(self) -> set[str]:
        names = {key_name(target) for target in self.mapping.values()}
        return {name for name in names if name}

    def uses_mouse_move(self) -> bool:
        return any(target in MOUSE_MOVES for target in self.mapping.values())

    def uses_wheel(self) -> bool:
        return any(target in MOUSE_WHEEL for target in self.mapping.values())


def axis_strengths(source_neg, source_pos, value: int, lo: int, hi: int) -> dict[str, float]:
    """Intensité (0..1) des sources d'un axe. Une gâchette (``source_neg`` None) va de ``lo`` à ``hi``; un stick ou une
    croix (hat) est centré, chaque sens compte à partir de ``STICK_THRESHOLD``."""
    if hi <= lo:
        return {}
    if source_neg is None:
        fraction = (value - lo) / (hi - lo)
        return {source_pos: fraction if fraction >= STICK_THRESHOLD else 0.0}
    centre = (hi + lo) / 2
    fraction = (value - centre) / ((hi - lo) / 2)
    return {source_neg: -fraction if -fraction >= STICK_THRESHOLD else 0.0,
            source_pos: fraction if fraction >= STICK_THRESHOLD else 0.0}


def _open_uinput(translator: Translator):
    from evdev import UInput, ecodes
    keys = [getattr(ecodes, name) for name in translator.used_keys()]
    capabilities = {ecodes.EV_KEY: keys or [ecodes.KEY_ENTER]}
    rel = []
    if translator.uses_mouse_move():
        rel += [ecodes.REL_X, ecodes.REL_Y]
    if translator.uses_wheel():
        rel.append(ecodes.REL_WHEEL)
    if rel:
        capabilities[ecodes.EV_REL] = rel
        capabilities[ecodes.EV_KEY] += [ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_MIDDLE]
    return UInput(capabilities, name="ES-NE pad keys")


class Pads:
    """Manettes ouvertes (hotplug par rescan) et lecture de leurs événements."""

    def __init__(self, selector, grab: bool):
        self.selector = selector
        self.grab = grab
        self.devices = {}  # chemin -> InputDevice
        self.axes = {}  # chemin -> {code: (source_neg, source_pos, lo, hi)}

    def rescan(self) -> None:
        from evdev import InputDevice, ecodes
        from . import hotkey
        for path in hotkey.find_gamepads():
            if path in self.devices:
                continue
            try:
                device = InputDevice(path)
                if self.grab:
                    device.grab()
            except OSError as exc:
                log.warning("manette %s inutilisable: %s", path, exc)
                continue
            axes = {}
            for code, info in device.capabilities().get(ecodes.EV_ABS, []):
                name = ecodes.ABS.get(code)
                if isinstance(name, list):
                    name = name[0]
                if name in AXIS_SOURCES:
                    axes[code] = (*AXIS_SOURCES[name], info.min, info.max)
            self.devices[path] = device
            self.axes[path] = axes
            self.selector.register(device, selectors.EVENT_READ, path)

    def drop(self, path: str) -> None:
        device = self.devices.pop(path, None)
        self.axes.pop(path, None)
        if device is not None:
            try:
                self.selector.unregister(device)
                device.close()
            except (OSError, ValueError, KeyError):
                pass

    def close(self) -> None:
        for path in list(self.devices):
            self.drop(path)


def _emit(uinput, events) -> None:
    from evdev import ecodes
    for kind, what, value in events:
        if kind == "key":
            uinput.write(ecodes.EV_KEY, getattr(ecodes, what), value)
        else:
            uinput.write(ecodes.EV_REL, ecodes.REL_WHEEL, what)
    if events:
        uinput.syn()


def _handle_event(translator: Translator, pads: Pads, path: str, event, uinput) -> None:
    from evdev import ecodes
    out = []
    if event.type == ecodes.EV_KEY:
        for source, name in BUTTON_SOURCES.items():
            if getattr(ecodes, name) == event.code:
                out += translator.set_source(path, source, 1.0 if event.value else 0.0)
    elif event.type == ecodes.EV_ABS and event.code in pads.axes[path]:
        neg, pos, lo, hi = pads.axes[path][event.code]
        for source, strength in axis_strengths(neg, pos, event.value, lo, hi).items():
            out += translator.set_source(path, source, strength)
    _emit(uinput, out)


def translate(mapping: dict[str, str], child: subprocess.Popen | None = None, grab: bool = False,
              rescan: float = 2.0, stop=None) -> None:
    """Boucle principale: tourne tant que ``child`` vit (ou jusqu'à ``stop()``)."""
    from evdev import ecodes
    translator = Translator(mapping)
    uinput = _open_uinput(translator)
    selector = selectors.DefaultSelector()
    pads = Pads(selector, grab)
    carry_x = carry_y = 0.0
    next_scan = 0.0
    last = time.monotonic()
    try:
        while (child is None or child.poll() is None) and not (stop and stop()):
            now = time.monotonic()
            if now >= next_scan:
                pads.rescan()
                next_scan = now + rescan
            for key, _mask in selector.select(timeout=TICK):
                path = key.data
                try:
                    for event in key.fileobj.read():
                        _handle_event(translator, pads, path, event, uinput)
                except OSError:  # manette débranchée
                    _emit(uinput, [e for e in translator.release_all()])
                    pads.drop(path)
            now = time.monotonic()
            dx, dy = translator.mouse_vector()
            carry_x += dx * MOUSE_SPEED * (now - last)
            carry_y += dy * MOUSE_SPEED * (now - last)
            last = now
            step_x, step_y = int(carry_x), int(carry_y)
            if step_x or step_y:
                carry_x -= step_x
                carry_y -= step_y
                uinput.write(ecodes.EV_REL, ecodes.REL_X, step_x)
                uinput.write(ecodes.EV_REL, ecodes.REL_Y, step_y)
                uinput.syn()
    finally:
        _emit(uinput, translator.release_all())
        pads.close()
        selector.close()
        uinput.close()


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    command = []
    if "--" in args:
        split = args.index("--")
        args, command = args[:split], args[split + 1:]
    parser = argparse.ArgumentParser(prog="esne-padkeys", description="Traduit les manettes en clavier/souris (format .gptk de PortMaster).")
    parser.add_argument("gptk", type=Path, help="fichier de correspondance .gptk")
    parser.add_argument("--grab", action="store_true", help="accès exclusif aux manettes (le jeu ne les voit plus; coupe aussi le raccourci de sortie d'ES-NE)")
    options = parser.parse_args(args)

    try:
        mapping = parse_gptk(options.gptk.read_text(encoding="utf-8", errors="replace"))
    except OSError as exc:
        print(f"esne-padkeys: {exc}", file=sys.stderr)
        mapping = {}
    child = subprocess.Popen(command) if command else None

    def terminate(_signum, _frame):
        if child is not None and child.poll() is None:
            child.terminate()
        raise SystemExit(143)

    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    try:
        if not mapping:
            raise RuntimeError("aucune correspondance dans " + str(options.gptk))
        translate(mapping, child, options.grab)
    except SystemExit:
        raise
    except Exception as exc:  # droits uinput, evdev absent, fichier vide: le jeu doit quand même se lancer
        print(f"esne-padkeys: traduction manette -> clavier indisponible ({exc})", file=sys.stderr)
        if child is not None:
            return child.wait()
        return 1
    return child.returncode if child is not None else 0


if __name__ == "__main__":
    raise SystemExit(main())
