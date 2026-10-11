# SPDX-License-Identifier: GPL-3.0-or-later
"""esctl audio list | get | set ID | list-profiles | get-profile | set-profile ID

Passe par ``pactl`` (PulseAudio, ou PipeWire via pipewire-pulse: le cas de CachyOS).
Les identifiants sont les noms stables des nœuds (``alsa_output....``), pas les numéros, qui
changent à chaque démarrage.

Format attendu par le frontend: ``ID<TAB>LIBELLÉ``, une ligne par entrée. L'identifiant
``auto`` signifie « ne rien changer » et est toujours proposé en premier.
"""
from __future__ import annotations

import json
import sys

from .. import runner

NAME = "audio"

AUTO = "auto"


def available() -> bool:
    return runner.which("pactl") is not None


def _clean(text: str) -> str:
    """Le frontend sépare les champs par une tabulation: pas de tabulation ni de retour dans un libellé."""
    return " ".join(str(text).split())


_BAD_LABELS = {"", "(null)", "null", "none"}
_LABEL_PROPS = ("device.description", "alsa.card_name", "node.nick", "node.description", "device.product.name")


def _label(sink: dict) -> str:
    """Libellé lisible: certains pilotes (HDMI NVIDIA) donnent la description '(null)'."""
    candidates = [sink.get("description")]
    props = sink.get("properties")
    if isinstance(props, dict):
        candidates += [props.get(key) for key in _LABEL_PROPS]
    for candidate in candidates:
        if candidate and str(candidate).strip().lower() not in _BAD_LABELS:
            return _clean(candidate)
    return _clean(sink.get("name") or "")


def _list(kind: str) -> list[dict] | None:
    result = runner.run(["pactl", "--format=json", "list", kind])
    if not result.ok:
        sys.stderr.write(result.stderr)
        return None
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("esctl audio: sortie de pactl illisible (pactl >= 16 requis pour --format=json)", file=sys.stderr)
        return None
    return data if isinstance(data, list) else None


def default_sink_name() -> str:
    result = runner.run(["pactl", "get-default-sink"])
    return result.stdout.strip() if result.ok else ""


def derive_card_name(sink_name: str) -> str:
    """alsa_output.pci-0000_00_1f.3.analog-stereo -> alsa_card.pci-0000_00_1f.3"""
    if sink_name.startswith("alsa_output."):
        device = sink_name[len("alsa_output."):]
        if "." in device:
            device = device.rsplit(".", 1)[0]
        return "alsa_card." + device
    if sink_name.startswith("bluez_output."):
        device = sink_name[len("bluez_output."):]
        head, _, tail = device.rpartition(".")
        if head and tail.isdigit():
            device = head
        return "bluez_card." + device
    return ""


def card_for_sink(sink: dict, cards: list[dict]) -> dict | None:
    alsa_card = (sink.get("properties") or {}).get("alsa.card")
    if alsa_card is not None:
        for card in cards:
            if (card.get("properties") or {}).get("alsa.card") == alsa_card:
                return card
    derived = derive_card_name(sink.get("name", ""))
    return next((card for card in cards if derived and card.get("name") == derived), None)


def _current_card() -> dict | None:
    sinks, cards = _list("sinks"), _list("cards")
    if sinks is None or cards is None:
        return None
    name = default_sink_name()
    sink = next((s for s in sinks if s.get("name") == name), None)
    return card_for_sink(sink, cards) if sink else None


# ---------------------------------------------------------------------------------------------

def cmd_list() -> int:
    sinks = _list("sinks")
    if sinks is None:
        return 1
    print(f"{AUTO}\tAuto")
    for sink in sinks:
        name = sink.get("name")
        if name:
            print(f"{name}\t{_label(sink)}")
    return 0


def cmd_get() -> int:
    name = default_sink_name()
    if not name:
        return 1
    print(name)
    return 0


def cmd_set(sink_id: str) -> int:
    if sink_id == AUTO:
        return 0
    result = runner.run(["pactl", "set-default-sink", sink_id])
    if not result.ok:
        sys.stderr.write(result.stderr)
    return result.returncode


def cmd_list_profiles() -> int:
    print(f"{AUTO}\tAuto")
    card = _current_card()
    if card is None:
        return 0  # pas de carte (sortie virtuelle): seul « auto » est proposé
    for profile_id, info in (card.get("profiles") or {}).items():
        if isinstance(info, dict) and info.get("available") is False:
            continue
        description = info.get("description") if isinstance(info, dict) else ""
        print(f"{profile_id}\t{_clean(description or profile_id)}")
    return 0


def cmd_get_profile() -> int:
    card = _current_card()
    print((card or {}).get("active_profile") or AUTO)
    return 0


def cmd_set_profile(profile_id: str) -> int:
    if profile_id == AUTO:
        return 0
    card = _current_card()
    if card is None:
        print("esctl audio: la sortie actuelle n'a pas de profil réglable", file=sys.stderr)
        return 1
    result = runner.run(["pactl", "set-card-profile", card["name"], profile_id])
    if not result.ok:
        sys.stderr.write(result.stderr)
    return result.returncode


def run(args: list[str]) -> int:
    if not args:
        print("usage: esctl audio list|get|set ID|list-profiles|get-profile|set-profile ID", file=sys.stderr)
        return 2
    verb, rest = args[0], args[1:]

    if verb == "list" and not rest:
        return cmd_list()
    if verb == "get" and not rest:
        return cmd_get()
    if verb == "set" and len(rest) == 1:
        return cmd_set(rest[0])
    if verb == "list-profiles" and not rest:
        return cmd_list_profiles()
    if verb == "get-profile" and not rest:
        return cmd_get_profile()
    if verb == "set-profile" and len(rest) == 1:
        return cmd_set_profile(rest[0])

    print(f"esctl audio: usage invalide: {' '.join(args)}", file=sys.stderr)
    return 2
