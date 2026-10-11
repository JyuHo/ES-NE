import pytest

from esne.esctl import runner
from esne.esctl.runner import Result

XRANDR = """\
Screen 0: minimum 320 x 200, current 3840 x 1080, maximum 16384 x 16384
HDMI-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 527mm x 296mm
   1920x1080     60.00*+  50.00    59.94  
   1920x1080i    60.00    50.00  
   1680x1050     59.88  
   1280x720      60.00    50.00    59.94  
DP-1 connected 1920x1080+1920+0 (normal left inverted right x axis y axis) 527mm x 296mm
   1920x1080     60.00*+
   1024x768      60.00  
HDMI-2 disconnected (normal left inverted right x axis y axis)
"""

WLR_RANDR = """\
DP-2 "Dell Inc. DELL U2415 ABC123 (DP-2)"
  Physical size: 520x320 mm
  Enabled: yes
  Modes:
    1920x1200 px, 59.950001 Hz (preferred, current)
    1920x1080 px, 60.000000 Hz
    1280x720 px, 60.000000 Hz
  Position: 0,0
  Transform: normal
  Scale: 1.000000
HDMI-A-1 "Unknown TV (HDMI-A-1)"
  Enabled: no
  Modes:
    1920x1080 px, 60.000000 Hz (preferred)
"""

KSCREEN = """{
 "outputs": [
  {"name": "DP-1", "connected": true, "enabled": true, "priority": 1, "currentModeId": "1", "preferredModes": ["1"],
   "modes": [
    {"id": "1", "name": "1920x1200@60", "refreshRate": 59.95000076293945, "size": {"width": 1920, "height": 1200}},
    {"id": "2", "name": "1920x1080@60", "refreshRate": 60, "size": {"width": 1920, "height": 1080}},
    {"id": "3", "name": "1920x1080@60", "refreshRate": 60, "size": {"width": 1920, "height": 1080}},
    {"id": "4", "name": "1920x1080@50", "refreshRate": 50, "size": {"width": 1920, "height": 1080}}]},
  {"name": "HDMI-A-1", "connected": true, "enabled": false, "priority": 2, "currentModeId": "9",
   "modes": [{"id": "9", "name": "1280x720@60", "refreshRate": 60, "size": {"width": 1280, "height": 720}}]}
 ]
}"""

SINKS = """[
 {"index": 52, "state": "RUNNING", "name": "alsa_output.pci-0000_00_1f.3.analog-stereo",
  "description": "Built-in Audio Analog Stereo", "properties": {"alsa.card": "0", "device.id": "49"}},
 {"index": 60, "state": "SUSPENDED", "name": "alsa_output.pci-0000_01_00.1.hdmi-stereo",
  "description": "GA104 High Definition Audio\\tController Digital Stereo (HDMI)", "properties": {"alsa.card": "1"}},
 {"index": 70, "state": "IDLE", "name": "bluez_output.AA_BB_CC_DD_EE_FF.1",
  "description": "Casque BT", "properties": {}}
]"""

CARDS = """[
 {"index": 0, "name": "alsa_card.pci-0000_00_1f.3", "properties": {"alsa.card": "0"},
  "active_profile": "output:analog-stereo+input:analog-stereo",
  "profiles": {
    "off": {"description": "Off", "available": true},
    "output:analog-stereo": {"description": "Analog Stereo Output", "available": true},
    "output:analog-stereo+input:analog-stereo": {"description": "Analog Stereo Duplex", "available": true},
    "output:iec958-stereo": {"description": "Digital Stereo (IEC958) Output", "available": false}}},
 {"index": 1, "name": "alsa_card.pci-0000_01_00.1", "properties": {"alsa.card": "1"},
  "active_profile": "output:hdmi-stereo",
  "profiles": {"output:hdmi-stereo": {"description": "Digital Stereo (HDMI) Output", "available": true}}},
 {"index": 5, "name": "bluez_card.AA_BB_CC_DD_EE_FF", "properties": {},
  "active_profile": "a2dp-sink",
  "profiles": {"a2dp-sink": {"description": "High Fidelity Playback (A2DP Sink)", "available": true},
               "headset-head-unit": {"description": "Headset Head Unit (HSP/HFP)", "available": true}}}
]"""


class FakeRunner:
    """Remplace esne.esctl.runner: outils installés et réponses par ligne de commande exacte."""

    def __init__(self):
        self.tools: set[str] = set()
        self.responses: dict[tuple, Result] = {}
        self.calls: list[list[str]] = []

    def answer(self, argv, stdout="", returncode=0, stderr=""):
        self.responses[tuple(argv)] = Result(returncode, stdout, stderr)

    def which(self, name):
        return f"/usr/bin/{name}" if name in self.tools else None

    def run(self, argv, timeout=10.0):
        self.calls.append(list(argv))
        return self.responses.get(tuple(argv), Result(127, "", f"{argv[0]}: réponse non prévue\n"))


@pytest.fixture
def fake(monkeypatch):
    runner_fake = FakeRunner()
    monkeypatch.setattr(runner, "which", runner_fake.which)
    monkeypatch.setattr(runner, "run", runner_fake.run)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    return runner_fake


@pytest.fixture
def xrandr(fake):
    fake.tools.add("xrandr")
    fake.answer(["xrandr"], XRANDR)
    return fake


@pytest.fixture
def pulse(fake):
    fake.tools.add("pactl")
    fake.answer(["pactl", "--format=json", "list", "sinks"], SINKS)
    fake.answer(["pactl", "--format=json", "list", "cards"], CARDS)
    fake.answer(["pactl", "get-default-sink"], "alsa_output.pci-0000_00_1f.3.analog-stereo\n")
    return fake
