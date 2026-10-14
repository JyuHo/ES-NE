# SPDX-License-Identifier: GPL-3.0-or-later
import sys

from esne import padkeys

GPTK = """
# commentaire
start = enter
back = f10
a = f1
b = f1
l1 = e
up = up
left_analog_up = up
right_analog_left = mouse_movement_left
r1 = mouse_left
r2 = mouse_wheel_up
deadzone_triggers = 3000
mouse_scale = 512
bogus_button = x
"""


def test_parse_gptk_keeps_only_known_sources():
    mapping = padkeys.parse_gptk(GPTK)
    assert mapping["start"] == "enter" and mapping["left_analog_up"] == "up" and mapping["right_analog_left"] == "mouse_movement_left"
    assert "deadzone_triggers" not in mapping and "bogus_button" not in mapping and "mouse_scale" not in mapping


def test_key_name():
    assert padkeys.key_name("enter") == "KEY_ENTER"
    assert padkeys.key_name("f10") == "KEY_F10"
    assert padkeys.key_name("e") == "KEY_E" and padkeys.key_name("7") == "KEY_7"
    assert padkeys.key_name("up") == "KEY_UP" and padkeys.key_name("ctrl") == "KEY_LEFTCTRL"
    assert padkeys.key_name("mouse_left") == "BTN_LEFT"
    assert padkeys.key_name("n'importe quoi") is None


def test_two_sources_on_same_key_release_only_when_both_up():
    t = padkeys.Translator(padkeys.parse_gptk(GPTK))
    assert t.set_source("p", "a", 1.0) == [("key", "KEY_F1", 1)]
    assert t.set_source("p", "b", 1.0) == []
    assert t.set_source("p", "a", 0.0) == []
    assert t.set_source("p", "b", 0.0) == [("key", "KEY_F1", 0)]


def test_dpad_and_stick_share_a_key():
    t = padkeys.Translator(padkeys.parse_gptk(GPTK))
    assert t.set_source("p", "up", 1.0) == [("key", "KEY_UP", 1)]
    assert t.set_source("p", "left_analog_up", 0.9) == []
    assert t.set_source("p", "up", 0.0) == []
    assert t.set_source("p", "left_analog_up", 0.0) == [("key", "KEY_UP", 0)]
    assert t.set_source("p", "back", 1.0) == [("key", "KEY_F10", 1)]


def test_repeated_press_without_change_emits_nothing_and_unmapped_is_ignored():
    t = padkeys.Translator(padkeys.parse_gptk(GPTK))
    assert t.set_source("p", "l1", 1.0) == [("key", "KEY_E", 1)]
    assert t.set_source("p", "l1", 1.0) == []
    assert t.set_source("p", "y", 1.0) == []


def test_mouse_and_wheel():
    t = padkeys.Translator(padkeys.parse_gptk(GPTK))
    assert t.set_source("p", "r1", 1.0) == [("key", "BTN_LEFT", 1)]
    assert t.set_source("p", "r2", 1.0) == [("wheel", 1, 1)]
    assert t.set_source("p", "r2", 0.0) == []
    t.set_source("p", "right_analog_left", 0.5)
    assert t.mouse_vector() == (-0.5, 0.0)
    assert t.uses_mouse_move() and t.uses_wheel()
    assert {"KEY_ENTER", "BTN_LEFT"} <= t.used_keys()


def test_release_all_on_exit():
    t = padkeys.Translator(padkeys.parse_gptk(GPTK))
    t.set_source("p", "a", 1.0)
    t.set_source("q", "start", 1.0)
    assert sorted(t.release_all()) == [("key", "KEY_ENTER", 0), ("key", "KEY_F1", 0)]
    assert t.release_all() == []


def test_axis_strengths():
    # stick 8 bits: 0..255, centre 127.5
    assert padkeys.axis_strengths("l", "r", 255, 0, 255) == {"l": 0.0, "r": 1.0}
    assert padkeys.axis_strengths("l", "r", 0, 0, 255) == {"l": 1.0, "r": 0.0}
    assert padkeys.axis_strengths("l", "r", 140, 0, 255) == {"l": 0.0, "r": 0.0}
    # croix (hat) -1..1
    assert padkeys.axis_strengths("l", "r", -1, -1, 1) == {"l": 1.0, "r": 0.0}
    assert padkeys.axis_strengths("l", "r", 0, -1, 1) == {"l": 0.0, "r": 0.0}
    # gâchette 0..1023
    assert padkeys.axis_strengths(None, "l2", 1023, 0, 1023) == {"l2": 1.0}
    assert padkeys.axis_strengths(None, "l2", 100, 0, 1023) == {"l2": 0.0}


def test_main_still_runs_game_when_translation_unavailable(tmp_path, monkeypatch, capsys):
    gptk = tmp_path / "g.gptk"
    gptk.write_text("a = enter\n")

    def boom(*args, **kwargs):
        raise PermissionError("/dev/uinput")

    monkeypatch.setattr(padkeys, "translate", boom)
    assert padkeys.main([str(gptk), "--", sys.executable, "-c", "raise SystemExit(7)"]) == 7
    assert "indisponible" in capsys.readouterr().err


def test_main_without_mapping_file_still_runs_game(tmp_path, capsys):
    assert padkeys.main([str(tmp_path / "absent.gptk"), "--", sys.executable, "-c", "pass"]) == 0
    assert "indisponible" in capsys.readouterr().err


def test_handle_event_writes_keys_for_buttons_hat_and_stick():
    from types import SimpleNamespace
    from evdev import ecodes

    class FakeUinput:
        def __init__(self):
            self.writes = []

        def write(self, kind, code, value):
            self.writes.append((kind, code, value))

        def syn(self):
            pass

    t = padkeys.Translator(padkeys.parse_gptk(GPTK))
    pads = SimpleNamespace(axes={"/dev/input/event9": {
        ecodes.ABS_HAT0Y: ("up", "down", -1, 1), ecodes.ABS_Y: ("left_analog_up", "left_analog_down", 0, 255)}})
    ui = FakeUinput()
    ev = lambda kind, code, value: SimpleNamespace(type=kind, code=code, value=value)
    path = "/dev/input/event9"
    padkeys._handle_event(t, pads, path, ev(ecodes.EV_KEY, ecodes.BTN_SOUTH, 1), ui)
    padkeys._handle_event(t, pads, path, ev(ecodes.EV_ABS, ecodes.ABS_HAT0Y, -1), ui)
    padkeys._handle_event(t, pads, path, ev(ecodes.EV_ABS, ecodes.ABS_Y, 0), ui)  # stick en haut: même touche, rien de plus
    padkeys._handle_event(t, pads, path, ev(ecodes.EV_ABS, ecodes.ABS_HAT0Y, 0), ui)
    padkeys._handle_event(t, pads, path, ev(ecodes.EV_ABS, ecodes.ABS_Y, 127), ui)
    padkeys._handle_event(t, pads, path, ev(ecodes.EV_KEY, ecodes.BTN_SOUTH, 0), ui)
    assert ui.writes == [(ecodes.EV_KEY, ecodes.KEY_F1, 1), (ecodes.EV_KEY, ecodes.KEY_UP, 1),
                         (ecodes.EV_KEY, ecodes.KEY_UP, 0), (ecodes.EV_KEY, ecodes.KEY_F1, 0)]
