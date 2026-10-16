#!/usr/bin/env python3
"""Aperçu du thème : lance ES sous Xvfb avec le thème du dépôt et prend des captures.

Usage : python3 tools/theme/preview.py <emulationstation> <dossier-sortie> [ambiance] [systeme ...]
Nécessite xvfb-run, ImageMagick (import) et python-xlib.
"""
import os, sys, subprocess, tempfile, time, pathlib, shutil

ES, OUT = sys.argv[1], pathlib.Path(sys.argv[2])
BTNS = os.environ.get("BTNS", "default")
AMB = sys.argv[3] if len(sys.argv) > 3 else "nuit"
SYSTEMS = sys.argv[4:] or ["ps2"]
REPO = pathlib.Path(__file__).resolve().parents[2]
OUT.mkdir(parents=True, exist_ok=True)

import yaml
_c = yaml.safe_load((REPO / "src/esne/data/systems.yml").read_text())
CAT = _c.get("systems", _c)
tmp = pathlib.Path(tempfile.mkdtemp(prefix="esne-prev-"))
share, cfg, data = tmp / "share", tmp / "cfg", tmp / "data"
for d in (share, cfg, data / "roms"):
    d.mkdir(parents=True)
(share / "themes").symlink_to(REPO / "themes")
for s in SYSTEMS:
    (data / "roms" / s).mkdir()
    ext = (CAT.get(s, {}).get("extensions") or ["iso"])[0].lstrip(".")
    for g in ("Demo Game One", "Demo Game Two", "Another Demo"):
        (data / "roms" / s / f"{g}.{ext}").write_text("x")
    from PIL import Image, ImageDraw
    (data / "roms" / s / "images").mkdir()
    im = Image.new("RGB", (640, 480), (60, 90, 140)); ImageDraw.Draw(im).rectangle((20, 20, 620, 460), outline=(255, 255, 255), width=6)
    im.save(data / "roms" / s / "images" / "shot.png")
    games = "".join(
        f"<game><path>./{g}.{ext}</path><name>{g}</name><image>./images/shot.png</image><rating>0.8</rating>"
        f"<genre>Action</genre><favorite>true</favorite><players>2</players><region>eu</region><desc>Description de démonstration. " + "Texte de remplissage. " * 12 + "</desc></game>"
        for g in ("Demo Game One", "Demo Game Two", "Another Demo"))
    (data / "roms" / s / "gamelist.xml").write_text(f"<gameList>{games}</gameList>")
(cfg / "es_settings.cfg").write_text(
    '<?xml version="1.0"?>\n<config>\n'
    '<string name="ThemeSet" value="es-ne" />\n'
    f'<string name="ThemeColorSet" value="{AMB}" />\n<string name="subset.buttons" value="{BTNS}" />\n'
    '<string name="Language" value="fr_FR" />\n'
    '<bool name="ShowHelpPrompts" value="true" />\n</config>\n')
def _k(n, i):
    return f'<input name="{n}" type="key" id="{i}" value="1" />'
(cfg / "es_input.cfg").write_text(
    '<?xml version="1.0"?>\n<inputList>\n<inputConfig type="keyboard" deviceName="Keyboard" deviceGUID="-1">\n'
    + "\n".join(_k(n, i) for n, i in [("a", 13), ("b", 8), ("up", 1073741906), ("down", 1073741905),
        ("left", 1073741904), ("right", 1073741903), ("start", 115), ("select", 32), ("pageup", 1073741899),
        ("pagedown", 1073741902)]) + "\n</inputConfig>\n</inputList>\n")
(cfg / "esne.conf").write_text(f"system.language={os.environ.get('ESLANG', 'en_US')}\n")
sys.path.insert(0, str(REPO / "src"))
from esne import systemscfg
catalog = __import__("yaml").safe_load((REPO / "src/esne/data/systems.yml").read_text())
(cfg / "es_systems.cfg").write_text(systemscfg.render(
    {k: v for k, v in (catalog.get("systems") or catalog).items() if k in SYSTEMS}, data / "roms"))

env = dict(os.environ, ESNE_SHARE_DIR=str(share), ESNE_CONFIG_DIR=str(cfg), ESNE_DATA_DIR=str(data),
           ESNE_STATE_DIR=str(tmp / "state"), HOME=str(tmp), SDL_AUDIODRIVER="dummy")
runner = pathlib.Path(__file__).with_name("_drive.py")
subprocess.run(["xvfb-run", "-a", "-s", "-screen 0 1280x800x24", sys.executable, str(runner), ES, str(OUT), *SYSTEMS],
               env=env, check=False)
print("log:", tmp / "state/logs")
