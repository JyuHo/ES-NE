"""Source unique de vérité pour les chemins (XDG, surchargeables)."""
import os
from pathlib import Path


def _xdg(var: str, default: str) -> Path:
    return Path(os.environ.get(var) or Path.home() / default)


def config_dir() -> Path:
    return Path(os.environ.get("ESNE_CONFIG_DIR") or _xdg("XDG_CONFIG_HOME", ".config") / "esne")


def data_dir() -> Path:
    return Path(os.environ.get("ESNE_DATA_DIR") or _xdg("XDG_DATA_HOME", ".local/share") / "esne")


def cache_dir() -> Path:
    return Path(os.environ.get("ESNE_CACHE_DIR") or _xdg("XDG_CACHE_HOME", ".cache") / "esne")


def conf_file() -> Path:
    return config_dir() / "esne.conf"


def roms_dir() -> Path:
    return data_dir() / "roms"


def bios_dir() -> Path:
    return data_dir() / "bios"
