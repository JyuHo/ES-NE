import pytest

from esne.esctl.cli import main
from esne.esctl.commands import resolution as res
from esne.esctl.commands import config as cfg
from .conftest import WLR_RANDR, XRANDR


def test_mode_id_and_label():
    mode = res.Mode(1920, 1080, 59.94)
    assert mode.id == "1920x1080.59.94"
    assert mode.label == "1920x1080 59.94 Hz"
    assert ":" not in mode.id
    assert res.Mode(1920, 1080, 60.0).label == "1920x1080 60 Hz"
    assert res.Mode(1920, 1080, 60.0, interlaced=True).id == "1920x1080i.60.00"


def test_parse_mode_id():
    assert res.parse_mode_id("1920x1080.60.00") == (1920, 1080, False, 60.0)
    assert res.parse_mode_id("1920x1080i.59.94") == (1920, 1080, True, 59.94)
    assert res.parse_mode_id("1920x1080") is None
    assert res.parse_mode_id("auto") is None


def test_parse_xrandr():
    outputs = res.parse_xrandr(XRANDR)
    assert [o.name for o in outputs] == ["HDMI-1", "DP-1", "HDMI-2"]
    assert [o.connected for o in outputs] == [True, True, False]
    assert [o.primary for o in outputs] == [True, False, False]
    hdmi = outputs[0]
    assert len(hdmi.modes) == 3 + 2 + 1 + 3
    current = hdmi.current_mode()
    assert (current.width, current.height, current.rate, current.preferred) == (1920, 1080, 60.0, True)
    assert any(m.interlaced and m.width == 1920 for m in hdmi.modes)
    assert outputs[2].modes == []


def test_parse_wlr_randr():
    outputs = res.parse_wlr_randr(WLR_RANDR)
    assert [o.name for o in outputs] == ["DP-2", "HDMI-A-1"]
    assert [o.connected for o in outputs] == [True, False]
    dp = outputs[0]
    assert [(m.width, m.height) for m in dp.modes] == [(1920, 1200), (1920, 1080), (1280, 720)]
    assert dp.current_mode().preferred is True
    assert dp.modes[0].rate == pytest.approx(59.950001)


def test_sorted_modes_dedup_and_order():
    modes = [res.Mode(1280, 720, 60), res.Mode(1920, 1080, 50), res.Mode(1920, 1080, 60),
             res.Mode(1920, 1080, 60), res.Mode(1920, 1080, 60, interlaced=True)]
    ids = [m.id for m in res.sorted_modes(modes)]
    assert ids == ["1920x1080.60.00", "1920x1080i.60.00", "1920x1080.50.00", "1280x720.60.00"]


def test_list_modes_format(xrandr, capsys):
    assert main(["resolution", "listModes"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "1920x1080.60.00:1920x1080 60 Hz"          # sortie primaire (HDMI-1)
    assert "1920x1080.59.94:1920x1080 59.94 Hz" in lines
    assert "1024x768.60.00:1024x768 60 Hz" not in lines           # appartient à DP-1
    for line in lines:
        mode_id, _, label = line.partition(":")
        assert mode_id and label and ":" not in mode_id           # contrat avec le menu d'ES


def test_list_modes_screen(xrandr, capsys):
    assert main(["resolution", "--screen", "DP-1", "listModes"]) == 0
    assert capsys.readouterr().out.splitlines() == ["1920x1080.60.00:1920x1080 60 Hz", "1024x768.60.00:1024x768 60 Hz"]


def test_unknown_or_disconnected_screen(xrandr, capsys):
    assert main(["resolution", "--screen", "DP-9", "listModes"]) == 1
    assert main(["resolution", "--screen", "HDMI-2", "listModes"]) == 1   # déconnectée: filtrée


def test_current_mode(xrandr, capsys):
    assert main(["resolution", "currentMode"]) == 0
    assert capsys.readouterr().out.strip() == "1920x1080.60.00"


def test_set_mode_xrandr(xrandr):
    xrandr.answer(["xrandr", "--output", "HDMI-1", "--mode", "1280x720", "--rate", "50.00"])
    assert main(["resolution", "setMode", "1280x720.50.00"]) == 0
    assert xrandr.calls[-1] == ["xrandr", "--output", "HDMI-1", "--mode", "1280x720", "--rate", "50.00"]


def test_set_mode_errors(xrandr, capsys):
    assert main(["resolution", "setMode"]) == 2
    assert main(["resolution", "setMode", "auto"]) == 2
    assert main(["resolution", "setMode", "800x600.60.00"]) == 1       # mode absent de la sortie
    assert not any(c[:2] == ["xrandr", "--output"] for c in xrandr.calls)   # rien n'est lancé


def test_set_mode_wlr_randr(fake):
    fake.tools.add("wlr-randr")
    fake.answer(["wlr-randr"], WLR_RANDR)
    fake.answer(["wlr-randr", "--output", "DP-2", "--mode", "1920x1080@60.000Hz"])
    assert main(["resolution", "setMode", "1920x1080.60.00"]) == 0
    assert fake.calls[-1] == ["wlr-randr", "--output", "DP-2", "--mode", "1920x1080@60.000Hz"]


def test_backend_order(fake, monkeypatch):
    fake.tools.update({"xrandr", "wlr-randr"})
    assert res.backend_order() == ["xrandr", "wlr-randr"]
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-1")
    assert res.backend_order() == ["wlr-randr", "xrandr"]


def test_fallback_to_next_backend(fake, monkeypatch):
    # Wayland non-wlroots: wlr-randr échoue, xrandr (XWayland) prend le relais
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-1")
    fake.tools.update({"xrandr", "wlr-randr"})
    fake.answer(["wlr-randr"], "", returncode=1, stderr="compositor doesn't support wlr-output-management\n")
    fake.answer(["xrandr"], XRANDR)
    backend, outputs = res.read_outputs()
    assert backend == "xrandr" and len(outputs) == 2


def test_no_backend(fake, capsys):
    assert not res.available()
    assert main(["resolution", "listModes"]) == 1
    assert "xrandr" in capsys.readouterr().err


def test_has_follows_backend(fake):
    assert main(["has", "resolution"]) == 1
    fake.tools.add("xrandr")
    assert main(["has", "resolution"]) == 0


def test_invalid_arguments(xrandr):
    assert main(["resolution"]) == 2
    assert main(["resolution", "frobnicate"]) == 2


def test_config_lsoutputs(xrandr, capsys):
    assert main(["config", "lsoutputs"]) == 0
    assert capsys.readouterr().out.splitlines() == ["HDMI-1", "DP-1"]
    assert main(["config", "storage", "current"]) == 2    # autres verbes de batocera-config: non fournis
    assert cfg.available()
