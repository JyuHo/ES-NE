# SPDX-License-Identifier: GPL-3.0-or-later
import xml.etree.ElementTree as ET
from types import SimpleNamespace

from esne.esctl.cli import main
from esne.esctl.commands import padsinfo, timezone


# ---- timezone ---------------------------------------------------------------

def test_valid_zone_must_exist_and_stay_in_zoneinfo(tmp_path):
    (tmp_path / "Europe").mkdir()
    (tmp_path / "Europe" / "Paris").write_text("")
    assert timezone.valid("Europe/Paris", tmp_path)
    assert not timezone.valid("Europe/Atlantis", tmp_path)
    assert not timezone.valid("../etc/passwd", tmp_path)
    assert not timezone.valid("/etc/passwd", tmp_path)
    assert not timezone.valid("", tmp_path)


def test_set_timezone_calls_timedatectl(tmp_path):
    (tmp_path / "Europe").mkdir()
    (tmp_path / "Europe" / "Paris").write_text("")
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    assert timezone.set_timezone("Europe/Paris", fake_run, tmp_path) == 0
    assert calls == [["timedatectl", "set-timezone", "Europe/Paris"]]


def test_set_timezone_rejects_unknown_without_running(tmp_path, capsys):
    ran = []
    assert timezone.set_timezone("Nope/Zone", lambda *a, **k: ran.append(1), tmp_path) == 1
    assert not ran and "inconnu" in capsys.readouterr().err


def test_set_timezone_reports_polkit_failure(tmp_path, capsys):
    (tmp_path / "UTC").write_text("")
    fail = lambda argv, **k: SimpleNamespace(returncode=1, stdout="", stderr="Interactive authentication required.")
    assert timezone.set_timezone("UTC", fail, tmp_path) == 1
    assert "polkit" in capsys.readouterr().err


def test_current_uses_timedatectl_then_localtime_link(tmp_path, monkeypatch):
    monkeypatch.setattr(timezone.shutil, "which", lambda name: "/usr/bin/timedatectl")
    ok = lambda argv, **k: SimpleNamespace(returncode=0, stdout="Europe/Paris\n", stderr="")
    assert timezone.current(ok, tmp_path / "localtime") == "Europe/Paris"

    zone = tmp_path / "usr" / "share" / "zoneinfo" / "Asia" / "Tokyo"
    zone.parent.mkdir(parents=True)
    zone.write_text("")
    link = tmp_path / "localtime"
    link.symlink_to(zone)
    bad = lambda argv, **k: SimpleNamespace(returncode=1, stdout="", stderr="")
    assert timezone.current(bad, link) == "Asia/Tokyo"


def test_esctl_timezone_unknown_action_is_usage_error():
    assert main(["timezone", "bogus"]) == 2


# ---- padsinfo ---------------------------------------------------------------

def make_event(root, number, name, caps="7fdb000000000000 0 0 0 0", vendor="054c", uniq="", power=None):
    device = root / f"event{number}" / "device"
    (device / "capabilities").mkdir(parents=True)
    (device / "id").mkdir()
    (device / "name").write_text(name + "\n")
    (device / "capabilities" / "key").write_text(caps + "\n")
    (device / "id" / "vendor").write_text(vendor + "\n")
    (device / "uniq").write_text(uniq + "\n")
    if power:
        supply = device / "power_supply" / "ps-controller-battery"
        supply.mkdir(parents=True)
        (supply / "capacity").write_text(power[0] + "\n")
        (supply / "status").write_text(power[1] + "\n")


def test_find_pads_filters_sensors_touchpad_and_non_gamepads(tmp_path):
    make_event(tmp_path, 3, "Razer Keyboard", caps="120000 0 0 0 0")
    make_event(tmp_path, 14, "Wireless Controller", power=("80", "Charging"))
    make_event(tmp_path, 15, "Wireless Controller Motion Sensors")
    make_event(tmp_path, 16, "Wireless Controller Touchpad")
    pads = padsinfo.find_pads(tmp_path, "/dev/input", tmp_path / "power")
    assert len(pads) == 1
    pad = pads[0]
    assert (pad["device"], pad["id"], pad["name"]) == ("ps4", 0, "Wireless Controller")
    assert (pad["battery"], pad["status"], pad["path"]) == ("80", "Charging", "/dev/input/event14")


def test_battery_from_global_power_supply_matching_uniq(tmp_path):
    make_event(tmp_path, 5, "Wireless Controller", uniq="aa:bb:cc:dd:ee:ff")
    power = tmp_path / "power"
    supply = power / "ps-controller-battery-aa:bb:cc:dd:ee:ff"
    supply.mkdir(parents=True)
    (supply / "capacity").write_text("55\n")
    (supply / "status").write_text("Discharging\n")
    pad = padsinfo.find_pads(tmp_path, "/dev/input", power)[0]
    assert (pad["battery"], pad["status"]) == ("55", "Discharging")


def test_render_matches_what_es_parses(tmp_path):
    make_event(tmp_path, 14, 'Pad "A" <1>')
    root = ET.fromstring(padsinfo.render(padsinfo.find_pads(tmp_path, "/dev/input", tmp_path / "power")))
    pad = root.find("pad")
    assert root.tag == "pads" and pad.get("name") == 'Pad "A" <1>' and pad.get("id") == "0"
    assert pad.get("battery") is None  # attribut omis sans batterie


def test_pad_types():
    assert padsinfo.pad_type("Xbox Wireless Controller") == "xbox"
    assert padsinfo.pad_type("Wireless Controller", "054c") == "ps4"
    assert padsinfo.pad_type("Pro Controller") == "switch"
    assert padsinfo.pad_type("Mystery Pad") == "generic"


def test_commands_registered():
    from esne.esctl.commands import COMMANDS
    assert "timezone" in COMMANDS and "padsinfo" in COMMANDS


def test_xbox_pads_are_recognised_by_name_or_vendor():
    for name in ("Microsoft X-Box 360 pad", "Xbox 360 Controller", "Xbox One Wireless Controller", "Xbox Series X Controller"):
        assert padsinfo.pad_type(name) == "xbox"
    assert padsinfo.pad_type("Generic USB Joystick", "045e") == "xbox"
