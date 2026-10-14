# SPDX-License-Identifier: GPL-3.0-or-later
"""esne-steam-run [--close] <appid> -- <commande de lancement>

Steam rend la main dès qu'il a transmis le jeu à son client: ES reprendrait donc tout de suite la main pendant la partie.
Cet utilitaire lance la commande (détachée de ce processus), attend que le jeu démarre (processus ``reaper`` de Steam portant
``AppId=<appid>``), puis attend sa fin. Un SIGTERM (raccourci de sortie d'ES-NE) ferme le jeu.

Avec ``--close``, le client Steam est fermé (``steam -shutdown``) à la fin de la partie s'il n'était pas déjà ouvert quand
le jeu a été lancé: Steam ne reste pas en arrière-plan et ne peut pas repasser au premier plan.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

START_TIMEOUT = 240.0  # Steam peut devoir démarrer et mettre le jeu à jour
POLL = 1.0
CLOSE_TIMEOUT = 30.0  # attente de la fermeture du client Steam


def game_pids(appid: str, proc: Path = Path("/proc")) -> list[int]:
    """Processus ``reaper`` de Steam lancés pour ce jeu (ligne de commande: ``... reaper SteamLaunch AppId=<appid> -- ...``)."""
    pids = []
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            words = (entry / "cmdline").read_bytes().decode("utf-8", "ignore").split("\0")
        except OSError:
            continue
        if "SteamLaunch" in words and f"AppId={appid}" in words:
            pids.append(int(entry.name))
    return pids


def steam_running(proc: Path = Path("/proc")) -> bool:
    """Le client Steam (processus ``steam``) tourne-t-il?"""
    for entry in proc.iterdir():
        if entry.name.isdigit():
            try:
                if (entry / "comm").read_text().strip() == "steam":
                    return True
            except OSError:
                continue
    return False


def shutdown_command(command: list[str]) -> list[str]:
    """``steam -silent steam://...`` -> ``steam -shutdown`` (même programme, ex. flatpak run com.valvesoftware.Steam)."""
    return [word for word in command if word != "-silent" and not word.startswith("steam://")] + ["-shutdown"]


def run(appid: str, command: list[str], proc: Path = Path("/proc"), popen=subprocess.Popen, sleep=time.sleep,
        clock=time.monotonic, kill=os.kill, close: bool = False) -> int:
    stopping = False
    already_open = steam_running(proc) if close else True

    def stop(signum=None, *_):
        nonlocal stopping
        stopping = True
        print(f"esne-steam-run: signal {signum} reçu", file=sys.stderr, flush=True)
        for pid in game_pids(appid, proc):
            try:
                kill(pid, signal.SIGTERM)
            except OSError:
                pass

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    popen(command, start_new_session=True)  # le client Steam reste ouvert après la partie (relancement plus rapide)
    deadline = clock() + START_TIMEOUT
    while not game_pids(appid, proc):
        if stopping:
            return 0
        if clock() > deadline:
            print(f"esne-steam-run: le jeu {appid} ne s'est pas lancé", file=sys.stderr)
            return 1
        sleep(POLL)
    while game_pids(appid, proc):
        sleep(POLL)
        if stopping and not game_pids(appid, proc):
            break
    if close and not already_open:
        popen(shutdown_command(command), start_new_session=True)
        deadline = clock() + CLOSE_TIMEOUT
        while steam_running(proc) and clock() < deadline:
            sleep(POLL)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    close = bool(args) and args[0] == "--close"
    if close:
        args = args[1:]
    if len(args) < 3 or args[1] != "--" or not args[0].isdigit():
        print("usage: esne-steam-run [--close] <appid> -- <commande de lancement>", file=sys.stderr)
        return 2
    return run(args[0], args[2:], close=close)


if __name__ == "__main__":
    raise SystemExit(main())
