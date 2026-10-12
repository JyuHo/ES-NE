"""Source unique de vérité pour les chemins (XDG, surchargeables)."""
import os
from pathlib import Path


def _xdg(var: str, default: str) -> Path:
    return Path(os.environ.get(var) or Path.home() / default)


def config_dir() -> Path:
    return Path(os.environ.get("ESNE_CONFIG_DIR") or _xdg("XDG_CONFIG_HOME", ".config") / "esne")


def data_dir() -> Path:
    """Roms, bios, saves, thèmes, décorations...: ~/esne (visible et facile à sauvegarder)."""
    return Path(os.environ.get("ESNE_DATA_DIR") or Path.home() / "esne")


def share_dir() -> Path:
    """Données en lecture seule installées par le paquet (même défaut que le frontend ES)."""
    return Path(os.environ.get("ESNE_SHARE_DIR") or "/usr/share/esne")


def state_dir() -> Path:
    """Journaux et état (même disposition que le frontend ES: <state>/logs)."""
    return Path(os.environ.get("ESNE_STATE_DIR") or _xdg("XDG_STATE_HOME", ".local/state") / "esne")


def cache_dir() -> Path:
    return Path(os.environ.get("ESNE_CACHE_DIR") or _xdg("XDG_CACHE_HOME", ".cache") / "esne")


def conf_file() -> Path:
    return config_dir() / "esne.conf"


def roms_dir() -> Path:
    return data_dir() / "roms"


def bios_dir() -> Path:
    return data_dir() / "bios"


def emulator_pid_file() -> Path:
    return state_dir() / "emulator.pid"
