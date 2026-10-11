import pytest


@pytest.fixture
def esne_env(tmp_path, monkeypatch):
    """Dossiers ESNE_* isolés: aucune lecture ni écriture hors de tmp_path."""
    for name in ("CONFIG", "DATA", "SHARE", "STATE", "CACHE"):
        directory = tmp_path / name.lower()
        directory.mkdir()
        monkeypatch.setenv(f"ESNE_{name}_DIR", str(directory))
    monkeypatch.setenv("ESNE_LAUNCH_ERROR_FILE", str(tmp_path / "launch_error.log"))
    return tmp_path
