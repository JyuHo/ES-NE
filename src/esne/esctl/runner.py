# SPDX-License-Identifier: GPL-3.0-or-later
"""Exécution de programmes externes. Seul point d'accès aux sous-processus (les tests le remplacent)."""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

NOT_FOUND = 127


@dataclass
class Result:
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def which(name: str) -> str | None:
    return shutil.which(name)


def run(argv: list[str], timeout: float = 10.0) -> Result:
    """Lance ``argv`` sans shell. Ne lève jamais: programme absent => 127, délai dépassé => 124."""
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return Result(NOT_FOUND, "", f"{argv[0]}: commande introuvable\n")
    except subprocess.TimeoutExpired:
        return Result(124, "", f"{argv[0]}: délai dépassé ({timeout}s)\n")
    except OSError as exc:  # permission refusée, format d'exécutable...
        return Result(126, "", f"{argv[0]}: {exc}\n")
    return Result(proc.returncode, proc.stdout, proc.stderr)
