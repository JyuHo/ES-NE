# SPDX-License-Identifier: GPL-3.0-or-later
"""esctl padsinfo

Liste les manettes connectées pour l'écran « Manettes » d'ES, au format attendu par ``ApiSystem::getPadsInfo``::

    <pads><pad device="ps4" id="0" name="Wireless Controller" battery="80" status="Charging" path="/dev/input/event14"/></pads>

``battery`` (pourcentage) et ``status`` ne sont renseignés que si le noyau expose une batterie pour la manette.
"""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import quoteattr

from ... import hotkey

NAME = "padsinfo"

SYS_INPUT = Path("/sys/class/input")
SYS_POWER = Path("/sys/class/power_supply")
_IGNORED = ("motion sensors", "touchpad")


def available() -> bool:
    return SYS_INPUT.is_dir()


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def pad_type(name: str, vendor: str = "") -> str:
    lowered = name.lower()
    if "xbox" in lowered or "x-box" in lowered or vendor == "045e":
        return "xbox"
    if "dualsense" in lowered:
        return "ps5"
    if "wireless controller" in lowered or "dualshock" in lowered or "playstation" in lowered or vendor == "054c":
        return "ps4"
    if "nintendo" in lowered or "pro controller" in lowered or "joy-con" in lowered or vendor == "057e":
        return "switch"
    return "generic"


def battery_for(device: Path, power_root: Path = SYS_POWER) -> tuple[str, str]:
    """(pourcentage, état) de la batterie liée à la manette, ou ("", "")."""
    candidates: list[Path] = []
    try:
        real = device.resolve()
    except OSError:
        real = device
    for parent in [real, *list(real.parents)[:5]]:
        candidates += sorted((parent / "power_supply").glob("*")) if (parent / "power_supply").is_dir() else []

    # Bluetooth/uhid: la batterie est un power_supply global dont le nom contient l'adresse (uniq) de la manette
    uniq = _read(device / "uniq").lower().replace(":", "")
    if uniq and power_root.is_dir():
        for supply in sorted(power_root.glob("*")):
            if uniq in supply.name.lower().replace(":", "").replace("-", "").replace("_", ""):
                candidates.append(supply)

    for supply in candidates:
        capacity = _read(supply / "capacity")
        if capacity.isdigit():
            return capacity, _read(supply / "status")
    return "", ""


def find_pads(sys_input: Path = SYS_INPUT, dev_root: str = "/dev/input", power_root: Path = SYS_POWER) -> list[dict]:
    pads = []
    for event in sorted(sys_input.glob("event*"), key=lambda p: int(p.name[5:]) if p.name[5:].isdigit() else 0):
        device = event / "device"
        name = _read(device / "name")
        if not name or any(token in name.lower() for token in _IGNORED):
            continue
        caps = _read(device / "capabilities" / "key")
        if not caps or not hotkey._is_gamepad(caps):
            continue
        battery, status = battery_for(device, power_root)
        pads.append({
            "device": pad_type(name, _read(device / "id" / "vendor").lower()),
            "id": len(pads),
            "name": name,
            "battery": battery,
            "status": status,
            "path": f"{dev_root}/{event.name}",
        })
    return pads


def render(pads: list[dict]) -> str:
    lines = ["<pads>"]
    for pad in pads:
        attrs = " ".join(f"{key}={quoteattr(str(value))}" for key, value in pad.items() if value != "")
        lines.append(f"  <pad {attrs} />")
    lines.append("</pads>")
    return "\n".join(lines)


def run(args: list[str]) -> int:
    print(render(find_pads()))
    return 0
