import os
import stat

import pytest
import yaml


@pytest.fixture
def emulation(esne_env, monkeypatch):
    """Faux RetroArch (script shell qui enregistre ses arguments) et faux core, visibles du lanceur."""
    root = esne_env
    bin_dir = root / "bin"
    bin_dir.mkdir()
    core_dir = root / "cores"
    core_dir.mkdir()
    (core_dir / "snes9x_libretro.so").write_text("")
    (core_dir / "bsnes_libretro.so").write_text("")

    record = root / "retroarch.args"
    script = bin_dir / "retroarch"
    script.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$@" > "{record}"\n'
        'exit "${FAKE_RETROARCH_EXIT:-0}"\n'
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)

    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    (esne_env / "config" / "emulators.yml").write_text(
        yaml.safe_dump({"libretro": {"binary": ["retroarch"], "core_dirs": [str(core_dir)]}})
    )

    class Emulation:
        pass

    result = Emulation()
    result.root, result.record, result.core_dir, result.bin_dir = root, record, core_dir, bin_dir
    result.args = lambda: record.read_text().splitlines()
    return result
