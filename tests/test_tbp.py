# SPDX-License-Identifier: GPL-3.0-or-later
import json
import urllib.error


from esne import bezels, tbp
from esne.esctl.commands import thebezelproject
from esne.generators import retroarch
from esne.generators.base import Context

NAMES = ["Zelda no Densetsu (Japan)", "Legend of Zelda, The - A Link to the Past (USA)", "Legend of Zelda, The - A Link to the Past (Europe)",
         "Legend of Zelda, The - A Link to the Past (Europe) (Rev 1)", "Super Mario World (USA)", "Super Mario World (USA) (Alt)",
         "Donkey Kong Country (Europe) (En,Fr,De)"]
PNG = b"\x89PNG\r\n\x1a\nxxxx"


def test_match_exact_then_case_then_title_with_region():
    assert tbp.match(NAMES, "Super Mario World (USA)") == "Super Mario World (USA)"
    assert tbp.match(NAMES, "super mario world (usa)") == "Super Mario World (USA)"
    # région absente du dépôt: même titre, USA préféré
    assert tbp.match(NAMES, "Super Mario World (Europe)") == "Super Mario World (USA)"
    assert tbp.match(NAMES, "Legend of Zelda, The - A Link to the Past (Europe) (Fr)") == "Legend of Zelda, The - A Link to the Past (Europe)"
    # même région que la ROM, sans la variante « Rev 1 »
    assert tbp.match(NAMES, "Legend of Zelda, The - A Link to the Past (Europe) (Rev 2)") == "Legend of Zelda, The - A Link to the Past (Europe)"
    assert tbp.match(NAMES, "Un jeu inconnu (USA)") is None
    assert tbp.match(NAMES, "(USA)") is None


def fake(files, calls=None):
    def get(url, timeout=0):
        if calls is not None:
            calls.append(url)
        for key, value in files.items():
            if key in url:
                if isinstance(value, Exception):
                    raise value
                return value
        raise urllib.error.URLError("404")
    return get


def tree(names):
    return json.dumps({"tree": [{"path": n + ".png", "type": "blob"} for n in names] + [{"path": n + ".cfg", "type": "blob"} for n in names]}).encode()


def test_index_is_cached_and_refreshed(esne_env, monkeypatch):
    calls = []
    get = fake({"git/trees": tree(NAMES)}, calls)
    start = 1_800_000_000.0
    assert tbp.load_index("snes", get, now=lambda: start) == sorted(NAMES)
    assert tbp.load_index("snes", get, now=lambda: start + 86400) == sorted(NAMES) and len(calls) == 1
    assert tbp.load_index("snes", get, now=lambda: start + 31 * 86400) == sorted(NAMES) and len(calls) == 2
    assert tbp.load_index("inconnu", get) is None


def test_index_failure_is_not_retried_for_an_hour(esne_env):
    calls = []
    get = fake({"git/trees": urllib.error.URLError("hors ligne")}, calls)
    assert tbp.load_index("snes", get, now=lambda: 1000.0) is None and len(calls) == 1
    assert tbp.load_index("snes", get, now=lambda: 1500.0) is None and len(calls) == 1
    assert tbp.load_index("snes", get, now=lambda: 5000.0) is None and len(calls) == 2


def test_ensure_game_downloads_once_under_the_rom_name(esne_env):
    calls = []
    get = fake({"git/trees": tree(NAMES), "Super%20Mario%20World%20%28USA%29.png": PNG}, calls)
    path = tbp.ensure_game("snes", "Super Mario World (Europe)", get)
    assert path == tbp.game_file("snes", "Super Mario World (Europe)") and path.read_bytes() == PNG
    count = len(calls)
    assert tbp.ensure_game("snes", "Super Mario World (Europe)", get) == path and len(calls) == count
    assert tbp.ensure_game("snes", "Sans bezel (USA)", get) is None


def test_ensure_game_rejects_non_png_and_offline(esne_env):
    assert tbp.ensure_game("snes", "Super Mario World (USA)", fake({"git/trees": tree(NAMES), "Mario": b"<html>"})) is None
    assert tbp.ensure_game("snes", "Super Mario World (USA)") is None  # réseau coupé par la fixture


def test_find_image_prefers_game_bezel(tmp_path):
    base = tmp_path / "tbp"
    (base / "systems").mkdir(parents=True)
    (base / "games" / "snes").mkdir(parents=True)
    (base / "systems" / "snes.png").write_bytes(b"")
    (base / "games" / "snes" / "Zelda (USA).png").write_bytes(b"")
    assert bezels.find_image("tbp", "snes", [tmp_path], rom="Zelda (USA)").parent.name == "snes" and \
        bezels.find_image("tbp", "snes", [tmp_path], rom="Zelda (USA)").parent.parent.name == "games"
    assert bezels.find_image("tbp", "snes", [tmp_path], rom="Autre").name == "snes.png"
    assert bezels.find_image("tbp", "snes", [tmp_path]).name == "snes.png"


class Cfg:
    def __init__(self, values): self.values = values
    def get(self, key, default=None): return self.values.get(key, default)


def test_bezel_settings_downloads_and_uses_the_game_bezel(esne_env, monkeypatch):
    from tests.test_bezels import make_bezel
    monkeypatch.setattr(retroarch, "screen_size", lambda: (1920, 1080))
    make_bezel(esne_env / "data" / "decorations" / "thebezelproject" / "systems" / "snes.png")
    seen = []

    def fake_ensure(system, stem, get=None, base=None):
        seen.append((system, stem))
        path = tbp.game_file(system, stem)
        make_bezel(path)
        return path

    monkeypatch.setattr(tbp, "ensure_game", fake_ensure)
    ctx = Context(system="snes", rom="/roms/snes/Zelda (USA).sfc", config=Cfg({"bezel": "thebezelproject"}), core="snes9x")
    settings = retroarch.bezel_settings(ctx)
    assert seen == [("snes", "Zelda (USA)")]
    assert "games/snes/Zelda (USA).png" in open(settings["input_overlay"]).read()
    seen.clear()
    ctx = Context(system="snes", rom="/roms/snes/Zelda (USA).sfc", config=Cfg({"bezel": "thebezelproject", "bezel_games": "0"}), core="snes9x")
    assert "systems/snes.png" in open(retroarch.bezel_settings(ctx)["input_overlay"]).read() and seen == []


def test_esctl_games_prefetches_rom_bezels(esne_env, monkeypatch, capsys):
    roms = esne_env / "roms"
    (roms / "snes").mkdir(parents=True)
    for name in ("Super Mario World (USA).sfc", "Super Mario World (USA).srm", "Inconnu (USA).sfc", "gamelist.xml", ".hidden"):
        (roms / "snes" / name).write_bytes(b"x")
    assert thebezelproject.rom_stems("snes", roms) == ["Inconnu (USA)", "Super Mario World (USA)"]
    get = fake({"git/trees": tree(NAMES), "Super%20Mario%20World%20%28USA%29.png": PNG})
    assert thebezelproject.games("snes", get, roms) == 0
    assert "1 bezels de jeu en place, 1 jeux sans bezel" in capsys.readouterr().out
    assert thebezelproject.games("inconnu", get, roms) == 1


def test_install_keeps_game_bezels_and_remove_deletes_them(esne_env):
    base = esne_env / "data" / "decorations" / "thebezelproject"
    (base / "games" / "snes").mkdir(parents=True)
    (base / "games" / "snes" / "A.png").write_bytes(PNG)
    (base / "games" / "nes").mkdir(parents=True)
    (base / "games" / "nes" / "B.png").write_bytes(PNG)
    thebezelproject.cleanup(base)
    assert (base / "games" / "snes" / "A.png").exists()
    thebezelproject.remove("snes", base)
    assert not (base / "games" / "snes").exists() and (base / "games" / "nes" / "B.png").exists()
