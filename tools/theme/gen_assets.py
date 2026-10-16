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
    "psx": ("PLAYSTATION", "SONY · 1994", -28, "PS"),
    "ps2": ("PLAYSTATION 2", "SONY · 2000", -12, "PS2"),
    "ps3": ("PLAYSTATION 3", "SONY · 2006", 0, "PS3"),
    "psp": ("PSP", "SONY · 2004", 72, "PSP"),
    "nes": ("NES", "NINTENDO · 1983", -35, "NES"),
    "snes": ("SUPER NINTENDO", "NINTENDO · 1990", -18, "SNES"),
    "gb": ("GAME BOY", "NINTENDO · 1989", 90, "GB"),
    "gbc": ("GAME BOY COLOR", "NINTENDO · 1998", 84, "GBC"),
    "gba": ("GAME BOY ADVANCE", "NINTENDO · 2001", 76, "GBA"),
    "mastersystem": ("MASTER SYSTEM", "SEGA · 1985", -45, "SMS"),
    "megadrive": ("MEGA DRIVE", "SEGA · 1988", -8, "MD"),
    "gamegear": ("GAME GEAR", "SEGA · 1990", 60, "GG"),
    "dreamcast": ("DREAMCAST", "SEGA · 1998", 15, "DC"),
    "n64": ("NINTENDO 64", "NINTENDO · 1996", -22, "64"),
    "gc": ("GAMECUBE", "NINTENDO · 2001", 30, "GC"),
    "wii": ("WII", "NINTENDO · 2006", 0, "WII"),
    "wiiu": ("WII U", "NINTENDO · 2012", -4, "WII U"),
    "switch": ("SWITCH", "NINTENDO · 2017", -90, "NS"),
    "nds": ("NINTENDO DS", "NINTENDO · 2004", 66, "DS"),
    "pcengine": ("PC ENGINE", "NEC · 1987", -55, "PCE"),
    "atari2600": ("ATARI 2600", "ATARI · 1977", -70, "2600"),
    "arcade": ("ARCADE", "VARIOUS · 1978", -14, "ARCADE"),
    "xbox": ("XBOX", "MICROSOFT · 2001", 20, "XBOX"),
    "xbox360": ("XBOX 360", "MICROSOFT · 2005", 12, "360"),
    "steam": ("STEAM", "VALVE · 2003", -30, "STEAM"),
    "windows": ("WINDOWS", "MICROSOFT · 1985", 0, "PC"),
    "ports": ("PORTS", "DIVERS", -6, "PORTS"),
    "auto-favorites": ("FAVORITES", "COLLECTION", -12, "FAV"),
    "auto-allgames": ("ALL GAMES", "COLLECTION", -12, "ALL"),
    "auto-lastplayed": ("LAST PLAYED", "COLLECTION", -12, "NEW"),
}

SYSTEM_XML = """<theme>
	<formatVersion>7</formatVersion>
	<include>./../theme.xml</include>
	<view name="system">
		<image name="logo">
			<path>./../art/logo/{sid}.png</path>
		</image>
		<image name="bg" extra="true">
			<path>./../art/bg/{sid}-${{subset.colorset}}.jpg</path>
			<pos>0 0</pos>
			<size>1 1</size>
			<zIndex>0</zIndex>
		</image>
	</view>
	<view name="basic, detailed">
		<image name="background">
			<path>./../art/bg/{sid}-${{subset.colorset}}.jpg</path>
		</image>
		<image name="logo">
			<path>./../art/logo/{sid}.png</path>
		</image>
	</view>
</theme>
"""

BG = """<html><style>
@font-face{{font-family:R;src:url('{font}')}}
html,body{{margin:0;width:1280px;height:800px;overflow:hidden;background:linear-gradient({top},{bot})}}
.bar{{position:absolute;top:-200px;height:1300px;transform:rotate({ang}deg);
 background:linear-gradient(to bottom,transparent,{c1}55 40%,{c2}33 70%,transparent)}}
.glow{{position:absolute;left:-200px;bottom:-400px;width:1700px;height:700px;border-radius:50%;
 background:radial-gradient(closest-side,{c1}40,transparent)}}
.name{{position:absolute;right:40px;bottom:-30px;font:700 {wm}px R;color:#fff;opacity:.035;white-space:nowrap}}
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


SRC = ROOT / "art" / "logo-src"   # logos monochromes tiers (voir themes/es-ne/art/logo-src/README.md)
LOGO_SVG = """<html><style>html,body{{margin:0;width:800px;height:220px;background:transparent}}
.w{{width:800px;height:220px;display:flex;align-items:center;justify-content:center}}
img{{max-width:620px;max-height:150px}}</style><body><div class=w><img src="{src}"></div></body></html>"""


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


# --- icônes de touches (aide) : blanc pur, teintées par iconColor dans le thème ---
BTN = """<html><style>
@font-face{{font-family:R;src:url('{font}')}}
html,body{{margin:0;width:{w}px;height:96px;background:transparent}}
.c{{box-sizing:border-box;width:88px;height:88px;margin:4px;border:10px solid #fff;border-radius:50%;
 display:flex;align-items:center;justify-content:center;color:#fff;font:700 56px R}}
.p{{box-sizing:border-box;width:{pw}px;height:60px;margin:18px 4px;border:9px solid #fff;border-radius:{r}px;
 display:flex;align-items:center;justify-content:center;color:#fff;font:700 38px R}}
svg{{width:52px;height:52px;fill:none;stroke:#fff;stroke-width:11;stroke-linejoin:round}}
</style><body>{body}</body></html>"""

SYM = {
    "cross": '<svg viewBox="0 0 52 52"><path d="M8 8L44 44M44 8L8 44"/></svg>',
    "circle": '<svg viewBox="0 0 52 52"><circle cx="26" cy="26" r="19"/></svg>',
    "square": '<svg viewBox="0 0 52 52"><rect x="8" y="8" width="36" height="36"/></svg>',
    "triangle": '<svg viewBox="0 0 52 52"><path d="M26 6L47 44H5Z"/></svg>',
    "menu": '<svg viewBox="0 0 52 52" style="stroke-width:7"><path d="M8 14H44M8 26H44M8 38H44"/></svg>',
    "view": '<svg viewBox="0 0 52 52" style="stroke-width:6"><rect x="6" y="14" width="26" height="24"/><path d="M38 20V44H16"/></svg>',
    "share": '<svg viewBox="0 0 52 52" style="stroke-width:6"><path d="M6 36V14H46V36ZM18 26H34"/></svg>',
}
ICONS = {  # (fichier, type, contenu)
    "xbox-a": ("c", "A"), "xbox-b": ("c", "B"), "xbox-x": ("c", "X"), "xbox-y": ("c", "Y"),
    "xbox-lb": ("p", "LB"), "xbox-rb": ("p", "RB"), "xbox-menu": ("c", SYM["menu"]), "xbox-view": ("c", SYM["view"]),
    "psx-cross": ("c", SYM["cross"]), "psx-circle": ("c", SYM["circle"]), "psx-square": ("c", SYM["square"]),
    "psx-triangle": ("c", SYM["triangle"]), "psx-l1": ("p", "L1"), "psx-r1": ("p", "R1"),
    "psx-options": ("p", SYM["menu"].replace('viewBox="0 0 52 52"', 'viewBox="0 0 52 52" style="width:44px;height:44px;stroke-width:8"', 1).replace(' style="stroke-width:7"', "")), "psx-share": ("p", "SHARE"),
}


def buttons(page):
    d = ROOT / "art" / "buttons"
    d.mkdir(parents=True, exist_ok=True)
    for name, (kind, content) in ICONS.items():
        if kind == "c":
            w, body = 96, f'<div class=c>{content}</div>'
        else:
            w, body = 140, f'<div class=p>{content}</div>'
        html = BTN.format(font=FONT, w=w, pw=w - 8, r=30, body=body)
        shot(page, html, w, 96, True).save(d / f"{name}.png", optimize=True)


def main():
    only = sys.argv[1:] or list(SYSTEMS)
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page()
        for sid in only:
            name, sub, ang, wmark = SYSTEMS[sid]
            for amb, (c1, c2, top, bot) in AMBIANCES.items():
                html = BG.format(font=FONT, top=top, bot=bot, c1=c1, c2=c2, ang=ang,
                                 bars=bars(c1, c2, sid), name=wmark, wm=260 if len(wmark) < 5 else 170)
                im = shot(page, html, 1280, 800).convert("RGB")
                im.save(ROOT / "art" / "bg" / f"{sid}-{amb}.jpg", quality=82, optimize=True)
            svg = SRC / f"{sid}.svg"
            if svg.exists():
                tmp = ROOT / "art" / "logo" / f"_{sid}.html"
                tmp.write_text(LOGO_SVG.format(src=svg.as_uri()))
                page.goto(tmp.as_uri()); page.wait_for_timeout(200)
                lg = Image.open(io.BytesIO(page.screenshot(omit_background=True)))
                tmp.unlink()
                lg = lg.crop(lg.getbbox())
            else:
                lg = shot(page, LOGO.format(font=FONT, name=name, sub=sub), 800, 220, True)
            lg.save(ROOT / "art" / "logo" / f"{sid}.png", optimize=True)
            (ROOT / sid).mkdir(exist_ok=True)
            (ROOT / sid / "theme.xml").write_text(SYSTEM_XML.format(sid=sid))
        buttons(page)
        b.close()


if __name__ == "__main__":
    main()
