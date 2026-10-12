# SPDX-License-Identifier: GPL-3.0-or-later
"""Exécution d'un jeu: choix de l'émulateur, génération de la commande, lancement, code de sortie."""
from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import threading
import traceback

from . import catalog, hotkey, paths
from .errors import (
    EMULATOR_EXITED, OTHER_ERROR, UNKNOWN_EMULATOR, LaunchError, launch_error_file,
)
from .generators import load_generator
from .generators.base import Context

log = logging.getLogger("es-launcher")

# Nom d'émulateur (ES, catalogue) -> module de génération
GENERATORS = {"libretro": "retroarch"}


def setup_logging() -> None:
    """Journal dans <state>/logs/es-launcher.log, et sur stderr (ES le redirige vers son propre journal)."""
    log.setLevel(logging.DEBUG)
    for handler in list(log.handlers):   # appel répété (tests, rechargement): repartir de zéro
        log.removeHandler(handler)
        handler.close()
    stderr = logging.StreamHandler(sys.stderr)
    stderr.setLevel(logging.INFO)
    stderr.setFormatter(logging.Formatter("es-launcher: %(message)s"))
    log.addHandler(stderr)
    try:
        directory = paths.state_dir() / "logs"
        directory.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(directory / "es-launcher.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(handler)
    except OSError:
        pass  # journal facultatif


def resolve_choice(ctx: Context) -> None:
    """Complète ctx.emulator / ctx.core: arguments d'ES, puis configuration, puis catalogue."""
    default_emulator, default_core = catalog.default_choice(ctx.system)

    if not ctx.emulator:
        ctx.emulator = ctx.setting("emulator") or default_emulator or ""
    if not ctx.emulator:
        raise LaunchError(UNKNOWN_EMULATOR, f"aucun émulateur défini pour le système '{ctx.system}'")

    if not ctx.core:
        # le core par défaut du catalogue n'a de sens que pour l'émulateur par défaut
        fallback = default_core if ctx.emulator == default_emulator else None
        ctx.core = ctx.setting("core") or fallback


def report(error: LaunchError) -> int:
    log.error("%s (code %d)", error.message, error.code)
    if error.code == OTHER_ERROR:
        try:
            launch_error_file().write_text(error.message + "\n", encoding="utf-8")
        except OSError:
            pass
    return error.code


def _write_pid(pid: int) -> None:
    try:
        target = paths.emulator_pid_file()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"{pid}\n", encoding="utf-8")
    except OSError:
        pass


def _clear_pid() -> None:
    try:
        paths.emulator_pid_file().unlink()
    except OSError:
        pass


def run_command(command, ctx: Context, generator) -> subprocess.CompletedProcess:
    """Lance l'émulateur dans son propre groupe de processus (``esctl swissknife --emukill`` le ferme grâce au fichier pid).
    Les émulateurs sans raccourci propre sont fermés par Select + Start (manette)."""
    env = {**os.environ, **command.env}
    codes = hotkey.required_codes(ctx.setting) if getattr(generator, "external_hotkey", False) else None

    child = subprocess.Popen(command.argv, env=env, cwd=command.cwd, start_new_session=True)
    _write_pid(child.pid)
    watcher = None

    def close_emulator():
        log.info("raccourci manette: fermeture de l'émulateur")
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except OSError:
            return
        threading.Timer(5.0, lambda: child.poll() is None and _kill(child)).start()

    if codes is not None:
        watcher = hotkey.Watcher(codes, close_emulator)
        watcher.start()
    try:
        returncode = child.wait()
    finally:
        if watcher is not None:
            watcher.stop()
        _clear_pid()
    # fermé volontairement par le raccourci: ce n'est pas une erreur
    return subprocess.CompletedProcess(command.argv, 0 if watcher is not None and watcher.triggered else returncode)


def _kill(child) -> None:
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except OSError:
        pass


def launch(ctx: Context) -> int:
    try:
        resolve_choice(ctx)
        module = GENERATORS.get(ctx.emulator)
        if module is None and (catalog.emulator_info(ctx.emulator) or {}).get("args"):
            module = "standalone"  # émulateur autonome décrit dans emulators.yml
        if module is None:
            raise LaunchError(UNKNOWN_EMULATOR, f"émulateur inconnu: '{ctx.emulator}'")

        generator = load_generator(module)
        command = generator.generate(ctx)

        log.info("système=%s émulateur=%s core=%s", ctx.system, ctx.emulator, ctx.core)
        log.info("commande: %s", " ".join(command.argv))

        try:
            process = run_command(command, ctx, generator)
        except OSError as exc:
            raise LaunchError(OTHER_ERROR, f"impossible de lancer {command.argv[0]}: {exc}") from exc
        finally:
            try:
                generator.post_run(ctx)
            except Exception:  # le nettoyage ne doit jamais masquer le résultat du jeu
                log.debug("post_run: %s", traceback.format_exc())

        if process.returncode != 0:
            log.warning("%s s'est terminé avec le code %d", command.argv[0], process.returncode)
            return EMULATOR_EXITED
        return 0

    except LaunchError as error:
        return report(error)
    except Exception as exc:  # bogue du lanceur: ES affichera le message
        log.error("erreur inattendue: %s", traceback.format_exc())
        return report(LaunchError(OTHER_ERROR, f"erreur inattendue d'es-launcher: {exc}"))
