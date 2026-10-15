"""Retrouve le chemin evdev (/dev/input/eventN) d'une manette à partir de son GUID SDL.

ES ne transmet ``-p<N>path`` que sous Windows; sous Linux seuls index et GUID arrivent.
Le GUID SDL (hex, 16 octets) contient bus (0-1), vendor (4-5), product (8-9) et version (12-13)
en petit-boutisme; on les compare à /proc/bus/input/devices.
"""
from __future__ import annotations

import re
from pathlib import Path

PROC_DEVICES = Path("/proc/bus/input/devices")


def guid_ids(guid: str) -> tuple[int, int] | None:
    """(vendor, product) d'un GUID SDL, ou None s'il n'en porte pas (GUID synthétique)."""
    if len(guid) != 32:
        return None
    try:
        raw = bytes.fromhex(guid)
    except ValueError:
        return None
    vendor = raw[4] | raw[5] << 8
    product = raw[8] | raw[9] << 8
    return (vendor, product) if vendor or product else None


def joystick_nodes(text: str) -> list[tuple[int, int, str]]:
    """[(vendor, product, /dev/input/eventN)] des périphériques ayant un handler jsN, triés par eventN."""
    nodes = []
    for block in text.split("\n\n"):
        ident = re.search(r"Vendor=([0-9a-fA-F]{4}) Product=([0-9a-fA-F]{4})", block)
        handlers = re.search(r"Handlers=(.*)", block)
        if not ident or not handlers or not re.search(r"\bjs\d+\b", handlers.group(1)):
            continue
        event = re.search(r"\bevent(\d+)\b", handlers.group(1))
        if event:
            nodes.append((int(ident.group(1), 16), int(ident.group(2), 16), int(event.group(1))))
    return [(v, p, f"/dev/input/event{n}") for v, p, n in sorted(nodes, key=lambda item: item[2])]


SYS_HIDRAW = Path("/sys/class/hidraw")
HIDRAW_FIRST = {0x054C, 0x057E}  # Sony, Nintendo: SDL les ouvre par le pilote HIDAPI (hidraw)


def hidraw_nodes() -> list[tuple[int, int, str]]:
    """[(vendor, product, /dev/hidrawN)] d'après /sys/class/hidraw/*/device/uevent."""
    nodes = []
    try:
        entries = sorted(SYS_HIDRAW.iterdir(), key=lambda e: int(re.sub(r"\D", "", e.name) or 0))
    except OSError:
        return nodes
    for entry in entries:
        try:
            match = re.search(r"HID_ID=[0-9A-Fa-f]+:([0-9A-Fa-f]+):([0-9A-Fa-f]+)", (entry / "device" / "uevent").read_text())
        except OSError:
            continue
        if match:
            nodes.append((int(match.group(1), 16), int(match.group(2), 16), f"/dev/{entry.name}"))
    return nodes


def resolve_paths(pads: list, text: str | None = None, hidraw: list | None = None, known: set | None = None) -> None:
    """Renseigne ``pad.path`` des manettes qui n'en ont pas.

    SDL3 donne à RMG tantôt /dev/hidrawN (Sony, Nintendo), tantôt /dev/input/eventN: on prend d'abord un chemin
    déjà présent dans la config de l'émulateur (``known``), sinon hidraw pour Sony/Nintendo, sinon evdev.
    Deux manettes identiques se suivent par ordre d'index.
    """
    if text is None:
        try:
            text = PROC_DEVICES.read_text(errors="replace")
        except OSError:
            text = ""
    if hidraw is None:
        hidraw = hidraw_nodes()
    known = known or set()
    nodes = joystick_nodes(text)
    taken: set[str] = set()
    for pad in sorted((p for p in pads if not p.path), key=lambda p: (p.index is None, p.index or 0)):
        ids = guid_ids(pad.guid)
        if ids is None:
            continue
        candidates = [path for v, pr, path in nodes if (v, pr) == ids]
        raw = [path for v, pr, path in hidraw if (v, pr) == ids]
        candidates = raw + candidates if ids[0] in HIDRAW_FIRST else candidates + raw
        candidates = [c for c in candidates if c not in taken]
        preferred = [c for c in candidates if c in known]
        chosen = (preferred or candidates or [""])[0]
        if chosen:
            pad.path = chosen
            taken.add(chosen)
