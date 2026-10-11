# SPDX-License-Identifier: GPL-3.0-or-later
"""esctl resolution [--screen SORTIE] listModes | currentMode | setMode ID

Format de ``listModes`` attendu par le frontend: une ligne par mode, ``ID:LIBELLÉ``.
L'ID est stocké dans la configuration (``global.videomode``) puis relu par le lanceur; il ne
contient donc jamais ``:``. Forme: ``LARGEURxHAUTEUR[i].FRÉQUENCE`` (``1920x1080.60.00``).

Outils pris en charge: ``xrandr`` (X11, et XWayland en dernier recours) et ``wlr-randr``
(Wayland wlroots: sway, Hyprland...). KDE Plasma et GNOME sous Wayland ne sont pas encore pris
en charge nativement.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field

from .. import runner

NAME = "resolution"

BACKENDS = ("xrandr", "wlr-randr")


@dataclass(frozen=True)
class Mode:
    width: int
    height: int
    rate: float
    interlaced: bool = False
    current: bool = False
    preferred: bool = False

    @property
    def id(self) -> str:
        return f"{self.width}x{self.height}{'i' if self.interlaced else ''}.{self.rate:.2f}"

    @property
    def label(self) -> str:
        rate = f"{self.rate:.2f}".rstrip("0").rstrip(".")
        return f"{self.width}x{self.height}{'i' if self.interlaced else ''} {rate} Hz"


@dataclass
class Output:
    name: str
    connected: bool = True
    primary: bool = False
    modes: list[Mode] = field(default_factory=list)

    def current_mode(self) -> Mode | None:
        return next((m for m in self.modes if m.current), None)


_MODE_ID = re.compile(r"^(\d+)x(\d+)(i?)\.(\d+(?:\.\d+)?)$")


def parse_mode_id(mode_id: str) -> tuple[int, int, bool, float] | None:
    match = _MODE_ID.match(mode_id)
    if not match:
        return None
    return int(match[1]), int(match[2]), match[3] == "i", float(match[4])


# ---------------------------------------------------------------------------------------------
# Analyse des sorties d'outils
# ---------------------------------------------------------------------------------------------

_XRANDR_OUTPUT = re.compile(r"^(\S+) (connected|disconnected)\b(.*)$")
_XRANDR_MODE = re.compile(r"^\s+(\d+)x(\d+)(i?)\s+(.+)$")
_XRANDR_RATE = re.compile(r"^(\d+(?:\.\d+)?)([*+]*)$")


def parse_xrandr(text: str) -> list[Output]:
    outputs: list[Output] = []
    current: Output | None = None

    for line in text.splitlines():
        header = _XRANDR_OUTPUT.match(line)
        if header:
            current = Output(
                name=header[1],
                connected=header[2] == "connected",
                primary=" primary" in " " + header[3].split("(")[0],
            )
            outputs.append(current)
            continue

        if current is None:
            continue

        mode_line = _XRANDR_MODE.match(line)
        if not mode_line:
            continue

        for token in mode_line[4].split():
            rate = _XRANDR_RATE.match(token)
            if rate:
                current.modes.append(
                    Mode(
                        width=int(mode_line[1]),
                        height=int(mode_line[2]),
                        rate=float(rate[1]),
                        interlaced=mode_line[3] == "i",
                        current="*" in rate[2],
                        preferred="+" in rate[2],
                    )
                )

    return outputs


_WLR_OUTPUT = re.compile(r"^(\S+)(?:\s+\".*\")?\s*$")
_WLR_MODE = re.compile(r"^\s+(\d+)x(\d+) px, (\d+(?:\.\d+)?) Hz(?: \(([^)]*)\))?")
_WLR_ENABLED = re.compile(r"^\s+Enabled:\s*(yes|no)", re.IGNORECASE)


def parse_wlr_randr(text: str) -> list[Output]:
    outputs: list[Output] = []
    current: Output | None = None

    for line in text.splitlines():
        if line and not line[0].isspace():
            header = _WLR_OUTPUT.match(line)
            current = Output(name=header[1]) if header else None
            if current is not None:
                outputs.append(current)
            continue

        if current is None:
            continue

        enabled = _WLR_ENABLED.match(line)
        if enabled:
            current.connected = enabled[1].lower() == "yes"
            continue

        mode_line = _WLR_MODE.match(line)
        if mode_line:
            flags = [f.strip() for f in (mode_line[4] or "").split(",")]
            current.modes.append(
                Mode(
                    width=int(mode_line[1]),
                    height=int(mode_line[2]),
                    rate=float(mode_line[3]),
                    current="current" in flags,
                    preferred="preferred" in flags,
                )
            )

    return outputs


_PARSERS = {"xrandr": parse_xrandr, "wlr-randr": parse_wlr_randr}


# ---------------------------------------------------------------------------------------------
# Sélection de l'outil et de la sortie
# ---------------------------------------------------------------------------------------------

def backend_order(environ=os.environ) -> list[str]:
    """Wayland: wlr-randr d'abord. X11 (ou inconnu): xrandr d'abord. Seuls les outils installés."""
    names = ["wlr-randr", "xrandr"] if environ.get("WAYLAND_DISPLAY") else ["xrandr", "wlr-randr"]
    return [name for name in names if runner.which(name)]


def available() -> bool:
    return bool(backend_order())


def read_outputs() -> tuple[str | None, list[Output]]:
    """Premier outil qui renvoie au moins une sortie connectée avec des modes."""
    for backend in backend_order():
        result = runner.run([backend])
        if not result.ok:
            continue
        outputs = [o for o in _PARSERS[backend](result.stdout) if o.connected and o.modes]
        if outputs:
            return backend, outputs
    return None, []


def pick_output(outputs: list[Output], screen: str | None) -> Output | None:
    if screen:
        return next((o for o in outputs if o.name == screen), None)
    return next((o for o in outputs if o.primary), outputs[0] if outputs else None)


def sorted_modes(modes: list[Mode]) -> list[Mode]:
    seen: set[str] = set()
    unique = []
    for mode in modes:
        if mode.id not in seen:
            seen.add(mode.id)
            unique.append(mode)
    return sorted(unique, key=lambda m: (-(m.width * m.height), -m.rate, m.interlaced))


def set_mode_command(backend: str, output: Output, mode: Mode) -> list[str]:
    size = f"{mode.width}x{mode.height}{'i' if mode.interlaced else ''}"
    if backend == "xrandr":
        return ["xrandr", "--output", output.name, "--mode", size, "--rate", f"{mode.rate:.2f}"]
    return ["wlr-randr", "--output", output.name, "--mode", f"{mode.width}x{mode.height}@{mode.rate:.3f}Hz"]


# ---------------------------------------------------------------------------------------------
# Commande
# ---------------------------------------------------------------------------------------------

def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="esctl resolution", add_help=False)
    parser.add_argument("--screen")
    parser.add_argument("verb", choices=("listModes", "currentMode", "setMode"))
    parser.add_argument("value", nargs="?")
    return parser


def run(args: list[str]) -> int:
    try:
        opts = _parser().parse_args(args)
    except SystemExit as exc:
        return int(exc.code or 2)

    backend, outputs = read_outputs()
    if backend is None:
        print("esctl resolution: aucune sortie vidéo détectée (xrandr ou wlr-randr requis)", file=sys.stderr)
        return 1

    output = pick_output(outputs, opts.screen)
    if output is None:
        print(f"esctl resolution: sortie introuvable: {opts.screen}", file=sys.stderr)
        return 1

    if opts.verb == "listModes":
        for mode in sorted_modes(output.modes):
            print(f"{mode.id}:{mode.label}")
        return 0

    if opts.verb == "currentMode":
        mode = output.current_mode()
        if mode is None:
            return 1
        print(mode.id)
        return 0

    # setMode
    if not opts.value:
        print("usage: esctl resolution [--screen SORTIE] setMode ID", file=sys.stderr)
        return 2
    wanted = parse_mode_id(opts.value)
    if wanted is None:
        print(f"esctl resolution: identifiant de mode invalide: {opts.value}", file=sys.stderr)
        return 2
    mode = next((m for m in output.modes if (m.width, m.height, m.interlaced) == wanted[:3]
                 and abs(m.rate - wanted[3]) < 0.005), None)
    if mode is None:
        print(f"esctl resolution: mode indisponible sur {output.name}: {opts.value}", file=sys.stderr)
        return 1
    result = runner.run(set_mode_command(backend, output, mode))
    if not result.ok:
        sys.stderr.write(result.stderr)
    return result.returncode
