"""Config clé=valeur au format batocera.conf, avec résolution en couches.

Ordre (le plus spécifique gagne):
  <système>["rom"].clé  >  <système>.clé  >  global.clé  >  défaut
"""
from __future__ import annotations
from pathlib import Path


class Config:
    def __init__(self, values: dict[str, str] | None = None):
        self.values = values or {}

    @classmethod
    def load(cls, path: Path) -> "Config":
        values: dict[str, str] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip()
        return cls(values)

    def get(self, key: str, system: str | None = None, rom: str | None = None, default=None):
        candidates = []
        if system and rom:
            candidates.append(f'{system}["{rom}"].{key}')
        if system:
            candidates.append(f"{system}.{key}")
        candidates.append(f"global.{key}")
        for c in candidates:
            v = self.values.get(c)
            if v not in (None, "", "auto"):
                return v
        return default
