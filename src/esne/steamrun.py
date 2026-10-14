# SPDX-License-Identifier: GPL-3.0-or-later
"""esne-steam-run <appid> -- <commande de lancement>

Steam rend la main dès qu'il a transmis le jeu à son client: ES reprendrait donc tout de suite la main pendant la partie.
Cet utilitaire lance la commande (détachée de ce processus), attend que le jeu démarre (processus ``reaper`` de Steam portant
``AppId=<appid>``), puis attend sa fin. Un SIGTERM (raccourci de sortie d'ES-NE) ferme le jeu.
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


def run(appid: str, command: list[str], proc: Path = Path("/proc"), popen=subprocess.Popen, sleep=time.sleep,
        clock=time.monotonic, kill=os.kill) -> int:
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True
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
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) < 3 or args[1] != "--" or not args[0].isdigit():
        print("usage: esne-steam-run <appid> -- <commande de lancement>", file=sys.stderr)
        return 2
    return run(args[0], args[2:])


if __name__ == "__main__":
    raise SystemExit(main())
