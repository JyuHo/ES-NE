# SPDX-License-Identifier: GPL-3.0-or-later
"""Installation de jeux libres depuis le catalogue PortMaster (https://github.com/PortsMaster/PortMaster-New).

On ne reprend que le dossier du jeu (binaires, bibliothèques, données, licences): le script de lancement
PortMaster (``Jeu.sh``) dépend du dossier de contrôle de PortMaster et n'est pas utilisé. ``es-genconfig``
crée son propre lanceur (voir ``systemscfg.seed_ports``). Bibliothèque standard uniquement.
"""
from __future__ import annotations

import hashlib
import io
import json
import platform
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

CATALOG_URL = "https://github.com/PortsMaster/PortMaster-New/releases/latest/download/ports.json"
EXECUTABLE_SUFFIXES = (".x86_64", ".aarch64", ".armhf", ".sh")
TIMEOUT = 60
CHUNK = 1 << 20


class PortmasterError(Exception):
    pass


def machine() -> str:
    return platform.machine()


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "es-ne"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read()
    except OSError as exc:
        raise PortmasterError(f"téléchargement impossible ({url}): {exc}") from exc


def find_port(catalog: dict, zip_name: str) -> dict:
    port = (catalog.get("ports") or {}).get(zip_name)
    if not isinstance(port, dict):
        raise PortmasterError(f"{zip_name}: absent du catalogue PortMaster")
    return port


def extract_game(data: bytes, game_dir: str, dest: Path) -> list[str]:
    """Extrait uniquement ``<game_dir>/`` du zip dans ``dest``. Refuse les chemins qui sortent de ``dest``."""
    written = []
    root = dest.resolve()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for info in archive.infolist():
            parts = PurePosixPath(info.filename).parts
            if not parts or parts[0] != game_dir or ".." in parts or PurePosixPath(info.filename).is_absolute():
                continue
            target = (dest / info.filename).resolve()
            if root not in target.parents and target != root:
                raise PortmasterError(f"chemin refusé dans l'archive: {info.filename}")
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
            # le zip PortMaster ne garde pas le bit d'exécution: PortMaster le remet au lancement, nous à l'installation
            executable = (info.external_attr >> 16) & 0o111 or target.suffix in EXECUTABLE_SUFFIXES
            target.chmod(0o755 if executable else 0o644)
            written.append(info.filename)
    return written


def install(zip_name: str, game_dir: str, roms_ports: Path, fetch=_download) -> list[str]:
    """Télécharge ``zip_name`` (vérifie le md5 du catalogue) et installe ``game_dir`` dans ``roms_ports``."""
    port = find_port(json.loads(fetch(CATALOG_URL).decode("utf-8")), zip_name)
    arch = machine()
    if arch not in (port.get("attr") or {}).get("arch", [arch]):
        raise PortmasterError(f"{zip_name}: pas de version {arch}")
    source = port.get("source") or {}
    if not source.get("url"):
        raise PortmasterError(f"{zip_name}: URL absente du catalogue")
    data = fetch(source["url"])
    if source.get("md5") and hashlib.md5(data).hexdigest() != source["md5"]:
        raise PortmasterError(f"{zip_name}: somme de contrôle incorrecte")
    written = extract_game(data, game_dir, roms_ports)
    if not written:
        raise PortmasterError(f"{zip_name}: le dossier « {game_dir} » est absent de l'archive")
    return written
