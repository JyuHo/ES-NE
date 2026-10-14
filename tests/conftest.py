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


@pytest.fixture(autouse=True)
def no_network_for_bezels(monkeypatch):
    """Les tests ne téléchargent jamais de bezels (The Bezel Project): le réseau est « indisponible »."""
    import urllib.error

    from esne import tbp

    def offline(url, timeout=0):
        raise urllib.error.URLError("hors ligne (tests)")

    monkeypatch.setattr(tbp, "fetch", offline)
