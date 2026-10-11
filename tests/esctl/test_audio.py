from esne.esctl.cli import main
from esne.esctl.commands import audio

SINK_ALSA = "alsa_output.pci-0000_00_1f.3.analog-stereo"


def test_derive_card_name():
    assert audio.derive_card_name(SINK_ALSA) == "alsa_card.pci-0000_00_1f.3"
    assert audio.derive_card_name("alsa_output.usb-Foo_Bar-00.analog-stereo") == "alsa_card.usb-Foo_Bar-00"
    assert audio.derive_card_name("bluez_output.AA_BB_CC_DD_EE_FF.1") == "bluez_card.AA_BB_CC_DD_EE_FF"
    assert audio.derive_card_name("combined") == ""


def test_list_format(pulse, capsys):
    assert main(["audio", "list"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "auto\tAuto"
    assert lines[1] == f"{SINK_ALSA}\tBuilt-in Audio Analog Stereo"
    assert len(lines) == 4
    for line in lines:
        assert line.count("\t") == 1, line          # contrat: ID<TAB>LIBELLÉ, une seule tabulation
    assert "GA104 High Definition Audio Controller Digital Stereo (HDMI)" in lines[2]   # tabulation du libellé nettoyée


def test_get(pulse, capsys):
    assert main(["audio", "get"]) == 0
    assert capsys.readouterr().out == SINK_ALSA + "\n"


def test_get_without_default_sink(fake, capsys):
    fake.tools.add("pactl")
    fake.answer(["pactl", "get-default-sink"], "", returncode=1)
    assert main(["audio", "get"]) == 1
    assert capsys.readouterr().out == ""


def test_set_auto_is_a_noop(pulse):
    assert main(["audio", "set", "auto"]) == 0
    assert not any(c[:2] == ["pactl", "set-default-sink"] for c in pulse.calls)


def test_set_sink(pulse):
    pulse.answer(["pactl", "set-default-sink", "bluez_output.AA_BB_CC_DD_EE_FF.1"])
    assert main(["audio", "set", "bluez_output.AA_BB_CC_DD_EE_FF.1"]) == 0
    assert pulse.calls[-1] == ["pactl", "set-default-sink", "bluez_output.AA_BB_CC_DD_EE_FF.1"]


def test_set_unknown_sink_fails(pulse, capsys):
    pulse.answer(["pactl", "set-default-sink", "nope"], "", returncode=1, stderr="Failure: No such entity\n")
    assert main(["audio", "set", "nope"]) == 1
    assert "No such entity" in capsys.readouterr().err


def test_list_profiles_skips_unavailable(pulse, capsys):
    assert main(["audio", "list-profiles"]) == 0
    lines = capsys.readouterr().out.splitlines()
    ids = [line.split("\t")[0] for line in lines]
    assert ids == ["auto", "off", "output:analog-stereo", "output:analog-stereo+input:analog-stereo"]
    assert "output:iec958-stereo" not in ids        # available: false
    assert all(line.count("\t") == 1 for line in lines)


def test_profiles_follow_the_default_sink(pulse, capsys):
    pulse.answer(["pactl", "get-default-sink"], "bluez_output.AA_BB_CC_DD_EE_FF.1\n")
    assert main(["audio", "list-profiles"]) == 0
    ids = [line.split("\t")[0] for line in capsys.readouterr().out.splitlines()]
    assert ids == ["auto", "a2dp-sink", "headset-head-unit"]
    assert main(["audio", "get-profile"]) == 0
    assert capsys.readouterr().out.strip() == "a2dp-sink"


def test_get_profile(pulse, capsys):
    assert main(["audio", "get-profile"]) == 0
    assert capsys.readouterr().out.strip() == "output:analog-stereo+input:analog-stereo"


def test_get_profile_without_card_is_auto(pulse, capsys):
    pulse.answer(["pactl", "get-default-sink"], "null-sink\n")
    assert main(["audio", "get-profile"]) == 0
    assert capsys.readouterr().out.strip() == "auto"


def test_set_profile(pulse):
    pulse.answer(["pactl", "set-card-profile", "alsa_card.pci-0000_00_1f.3", "output:analog-stereo"])
    assert main(["audio", "set-profile", "output:analog-stereo"]) == 0
    assert pulse.calls[-1] == ["pactl", "set-card-profile", "alsa_card.pci-0000_00_1f.3", "output:analog-stereo"]


def test_set_profile_auto_and_no_card(pulse, capsys):
    assert main(["audio", "set-profile", "auto"]) == 0
    pulse.answer(["pactl", "get-default-sink"], "null-sink\n")
    assert main(["audio", "set-profile", "off"]) == 1


def test_unreadable_pactl_output(pulse, capsys):
    pulse.answer(["pactl", "--format=json", "list", "sinks"], "Sink #52\n\tState: RUNNING\n")
    assert main(["audio", "list"]) == 1
    assert "pactl >= 16" in capsys.readouterr().err


def test_pactl_missing(fake):
    assert not audio.available()
    assert main(["has", "audio"]) == 1
    fake.tools.add("pactl")
    assert main(["has", "audio"]) == 0


def test_usage_errors(pulse):
    assert main(["audio"]) == 2
    assert main(["audio", "set"]) == 2
    assert main(["audio", "get", "extra"]) == 2
    assert main(["audio", "volume"]) == 2


def test_label_ignore_description_null():
    from esne.esctl.commands import audio

    sink = {"name": "x", "description": "(null)", "properties": {"alsa.card_name": "HDA NVidia"}}
    assert audio._label(sink) == "HDA NVidia"
    assert audio._label({"name": "x", "description": "(null)"}) == "x"
    assert audio._label({"name": "x", "description": "Carte"}) == "Carte"
