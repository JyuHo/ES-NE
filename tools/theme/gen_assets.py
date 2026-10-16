#!/usr/bin/env python3
"""Génère les assets du thème ES-NE (fonds statiques + logos) — tout est original.

Usage : python3 -I tools/theme/gen_assets.py [systeme ...]
Rend du HTML/CSS via Playwright (chromium) puis compresse avec PIL.
"""
import sys, io, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2] / "themes" / "es-ne"
import base64
FONT = "data:font/ttf;base64," + base64.b64encode((ROOT / "fonts" / "Rajdhani-Bold.ttf").read_bytes()).decode()

# ambiances : (teinte principale, teinte d'accent, fond sombre haut, fond sombre bas)
AMBIANCES = {
    "nuit":   ("#6a5cff", "#27c4ff", "#10102a", "#05050f"),
    "braise": ("#ff5a36", "#ffb347", "#2a1110", "#0f0505"),
}

# système : (nom affiché, sous-titre, angle des barres lumineuses)
SYSTEMS = {
    "ps2": ("PLAYSTATION 2", "SONY · 2000", -12),
}

BG = """<html><style>
@font-face{{font-family:R;src:url('{font}')}}
html,body{{margin:0;width:1280px;height:800px;overflow:hidden;background:linear-gradient({top},{bot})}}
.bar{{position:absolute;top:-200px;height:1300px;transform:rotate({ang}deg);
 background:linear-gradient(to bottom,transparent,{c1}55 40%,{c2}33 70%,transparent)}}
.glow{{position:absolute;left:-200px;bottom:-400px;width:1700px;height:700px;border-radius:50%;
 background:radial-gradient(closest-side,{c1}40,transparent)}}
.name{{position:absolute;right:40px;bottom:-30px;font:700 260px R;color:#fff;opacity:.035;white-space:nowrap}}
</style><body>
<div class=glow></div>
{bars}
<div class=name>{name}</div>
</body></html>"""

LOGO = """<html><style>
@font-face{{font-family:R;src:url('{font}')}}
html,body{{margin:0;width:800px;height:220px;background:transparent}}
.w{{display:flex;flex-direction:column;align-items:center;justify-content:center;height:220px;color:#fff;font-family:R}}
.n{{font-weight:700;font-size:92px;letter-spacing:6px;line-height:1}}
.s{{font-size:30px;letter-spacing:10px;opacity:.7;margin-top:6px}}
.b{{display:flex;gap:8px;margin-bottom:10px}}.b i{{width:34px;height:6px;background:#fff;transform:skewX(-30deg)}}
</style><body><div class=w><div class=b><i></i><i style="opacity:.6"></i><i style="opacity:.3"></i></div>
<div class=n>{name}</div><div class=s>{sub}</div></div></body></html>"""


def bars(c1, c2, seed):
    import random
    r = random.Random(seed)
    out = []
    for i in range(14):
        x = r.randint(-100, 1300)
        w = r.choice([2, 3, 4, 70, 140, 6])
        op = 0.25 if w < 10 else 0.12
        col = c1 if i % 3 else c2
        out.append(f'<div class=bar style="left:{x}px;width:{w}px;opacity:{op*3 if w<10 else op};'
                   f'background:linear-gradient(to bottom,transparent,{col}aa 45%,transparent)"></div>')
    return "".join(out)


def shot(page, html, w, h, transparent=False):
    page.set_viewport_size({"width": w, "height": h})
    page.set_content(html)
    page.wait_for_timeout(200)
    return Image.open(io.BytesIO(page.screenshot(omit_background=transparent)))


def main():
    only = sys.argv[1:] or list(SYSTEMS)
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page()
        for sid in only:
            name, sub, ang = SYSTEMS[sid]
            for amb, (c1, c2, top, bot) in AMBIANCES.items():
                html = BG.format(font=FONT, top=top, bot=bot, c1=c1, c2=c2, ang=ang,
                                 bars=bars(c1, c2, sid), name=name.split()[-1])
                im = shot(page, html, 1280, 800).convert("RGB")
                im.save(ROOT / "art" / "bg" / f"{sid}-{amb}.jpg", quality=82, optimize=True)
            lg = shot(page, LOGO.format(font=FONT, name=name, sub=sub), 800, 220, True)
            lg.save(ROOT / "art" / "logo" / f"{sid}.png", optimize=True)
        b.close()


if __name__ == "__main__":
    main()
