# SPDX-License-Identifier: GPL-3.0-or-later
"""Modification ciblée d'un fichier ``.ini`` en conservant tout le reste (ordre, commentaires, valeurs exotiques).

Les émulateurs écrivent leur configuration à leur façon (clés avec ``\\`` de Qt, valeurs ``@Variant(...)``, ``Clé = valeur``
avec espaces): ``configparser`` les abîme, on édite donc les lignes. Une clé absente de sa section est ajoutée à la fin de la
section; une section absente est ajoutée à la fin du fichier. Écriture atomique (fichier temporaire puis remplacement).
"""
from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger(__name__)

_ENCODING = {"encoding": "utf-8", "errors": "surrogateescape"}  # un octet illisible est conservé tel quel


def _read(path: Path) -> str:
    return path.read_bytes().decode(**_ENCODING)  # en octets: les fins de ligne \r\n restent intactes


def _is_section(line: str) -> str | None:
    text = line.strip()
    if text.startswith("[") and text.endswith("]"):
        return text[1:-1]
    return None


def patch_ini(path: Path, values: dict[str, dict[str, str]], spaced: bool = False) -> bool:
    """Écrit ``values`` (``{section: {clé: valeur déjà formatée}}``). False si le fichier manque ou si rien n'a changé.

    ``spaced``: écrit ``clé = valeur`` (sinon ``clé=valeur``) pour les lignes ajoutées; les lignes existantes gardent
    leur séparateur d'origine.
    """
    if not values or not path.is_file():
        return False
    try:
        lines = _read(path).splitlines(keepends=True)
    except OSError as exc:
        log.warning("%s illisible, réglages non appliqués: %s", path, exc)
        return False
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    separator = " = " if spaced else "="
    changed = False
    for section, keys in values.items():
        start = next((i for i, line in enumerate(lines) if _is_section(line) == section), None)
        if start is None:
            if lines and lines[-1].strip():
                lines.append("\n")
            lines.append(f"[{section}]\n")
            start = len(lines) - 1
            changed = True
        end = next((i for i in range(start + 1, len(lines)) if _is_section(lines[i]) is not None), len(lines))
        for key, value in keys.items():
            for i in range(start + 1, end):
                text = lines[i]
                name, sep, current = text.partition("=")
                if sep and name.strip() == key:
                    if current.strip() != value:
                        eol = text[len(text.rstrip("\r\n")):] or "\n"  # garde les fins de ligne du fichier
                        lines[i] = f"{name}={current[:len(current) - len(current.lstrip())]}{value}{eol}"
                        changed = True
                    break
            else:
                insert = end
                while insert > start + 1 and not lines[insert - 1].strip():
                    insert -= 1  # avant les lignes vides qui terminent la section
                lines.insert(insert, f"{key}{separator}{value}\n")
                end += 1
                changed = True
    if changed:
        temporary = path.with_name(path.name + ".esne-tmp")
        try:
            temporary.write_bytes("".join(lines).encode(**_ENCODING))
            temporary.replace(path)
        except OSError as exc:  # dossier ou fichier en lecture seule: le jeu doit se lancer quand même
            log.warning("%s non modifiable, réglages non appliqués: %s", path, exc)
            temporary.unlink(missing_ok=True)
            return False
    return changed


def read_section(path: Path, section: str) -> dict[str, str]:
    """Clés brutes (valeurs sans guillemets extérieurs) d'une section, ou ``{}``."""
    result: dict[str, str] = {}
    if not path.is_file():
        return result
    inside = False
    try:
        text = _read(path)
    except OSError:
        return result
    for line in text.splitlines():
        name = _is_section(line)
        if name is not None:
            inside = name == section
        elif inside and "=" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip().strip('"')
    return result
