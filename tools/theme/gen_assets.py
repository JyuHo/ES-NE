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
html,body{{margin:0;width:1280px;height:720px;overflow:hidden;background:linear-gradient({top},{bot})}}
.bar{{position:absolute;top:-200px;height:1300px;transform:rotate({ang}deg);
 background:linear-gradient(to bottom,transparent,{c1}55 40%,{c2}33 70%,transparent)}}
.glow{{position:absolute;left:-200px;bottom:-400px;width:1700px;height:700px;border-radius:50%;
 background:radial-gradient(closest-side,{c1}40,transparent)}}
</style><body>
<div class=glow></div>
{bars}
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
LOGO_SVG = """<html style="zoom:2"><style>html,body{{margin:0;width:800px;height:220px;background:transparent}}
.w{{width:800px;height:220px;display:flex;align-items:center;justify-content:center}}
img{{max-width:620px;max-height:150px}}</style><body><div class=w><img src="{src}"></div></body></html>"""


def dither(im):
    """Léger bruit pour éviter les bandes dans les dégradés sombres (JPEG)."""
    import numpy as np
    a = np.asarray(im).astype("float32")
    rng = np.random.default_rng(7)
    a += rng.normal(0, 1.2, a.shape[:2])[..., None]
    return Image.fromarray(a.clip(0, 255).astype("uint8"))


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


def shot(page, html, w, h, transparent=False, scale=1):
    """Rend du HTML de w×h px (CSS) en image de w*scale × h*scale (zoom CSS, pas de flou)."""
    page.set_viewport_size({"width": int(w * scale), "height": int(h * scale)})
    page.set_content(html.replace("<html>", f"<html style='zoom:{scale}'>", 1))
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


BSRC = ROOT / "art" / "buttons-src"
# fichier de sortie -> icone source (jeu d'icones Input Prompts, CC0, voir docs/THIRD_PARTY.md)
SVG_ICONS = {
    "xbox-a": "xbox_button_a_outline", "xbox-b": "xbox_button_b_outline", "xbox-x": "xbox_button_x_outline",
    "xbox-y": "xbox_button_y_outline", "xbox-lb": "xbox_lb_outline", "xbox-rb": "xbox_rb_outline",
    "xbox-menu": "xbox_button_menu_outline", "xbox-view": "xbox_button_view_outline",
    "psx-cross": "playstation_button_cross_outline", "psx-circle": "playstation_button_circle_outline",
    "psx-square": "playstation_button_square_outline", "psx-triangle": "playstation_button_triangle_outline",
    "psx-l1": "playstation_trigger_l1_outline", "psx-r1": "playstation_trigger_r1_outline",
}
# Options/Share: les SVG Kenney montrent la manette entiere (illisible a petite taille) -> pictos dessines
OWN = {
    "psx-options": '<rect x="4" y="12" width="56" height="40" rx="20" fill="none" stroke="#fff" stroke-width="5"/>'
                   '<path d="M20 25H44M20 32H44M20 39H44" stroke="#fff" stroke-width="4.5" stroke-linecap="round"/>',
    "psx-share": '<rect x="4" y="12" width="56" height="40" rx="20" fill="none" stroke="#fff" stroke-width="5"/>'
                 '<path d="M32 40V22M25 29L32 22L39 29" fill="none" stroke="#fff" stroke-width="4.5" '
                 'stroke-linecap="round" stroke-linejoin="round"/>',
}


def svg_png(page, name, size=192, crop=False):
    html = (f"<html><body style='margin:0;background:transparent'><img src='{(BSRC / (name + '.svg')).as_uri()}' "
            f"width={size} height={size}></body></html>")
    im = shot(page, html, size, size, True)
    if crop:
        bb = im.getbbox()
        pad = max(2, size // 64)
        im = im.crop((bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad))
    return im


def buttons(page):
    d = ROOT / "art" / "buttons"
    d.mkdir(parents=True, exist_ok=True)
    for out, src in SVG_ICONS.items():
        svg_png(page, src, 256, crop=True).save(d / f"{out}.png", optimize=True)
    for out, body in OWN.items():
        html = ("<html><body style='margin:0;background:transparent'><svg xmlns='http://www.w3.org/2000/svg' "
                f"width=256 height=256 viewBox='0 0 64 64'>{body}</svg></body></html>")
        im = shot(page, html, 256, 256, True)
        bb = im.getbbox()
        im.crop((bb[0] - 4, bb[1] - 4, bb[2] + 4, bb[3] + 4)).save(d / f"{out}.png", optimize=True)


# --- pastilles d'information (blanc pur, teintées dans le thème) ---
BADGES = {
    "save": (64, 64, """<defs><mask id=m><rect width=64 height=64 fill=#fff />
<rect x=18 y=6 width=24 height=16 fill=#000 /><rect x=14 y=34 width=36 height=24 rx=3 fill=#000 /></mask></defs>
<path mask=url(#m) d="M6 6H50L58 14V58H6Z" fill=#fff />"""),
    "trophy": (64, 64, """<path d="M18 6H46V26C46 36 40 42 32 42C24 42 18 36 18 26Z M46 12H58C58 26 52 32 44 33 M18 12H6C6 26 12 32 20 33 M28 42H36V50H28Z M18 54H46V60H18Z" fill=#fff stroke=#fff stroke-width=4 stroke-linejoin=round />"""),
    "heart": (64, 64, """<path d="M32 58C10 42 4 30 4 20C4 11 11 5 19 5C25 5 30 8 32 13C34 8 39 5 45 5C53 5 60 11 60 20C60 30 54 42 32 58Z" fill=#fff />"""),
    "pill": (160, 56, """<rect x=2 y=2 width=156 height=52 rx=26 fill=#fff />"""),
}


def badges(page):
    d = ROOT / "art" / "ui"
    d.mkdir(parents=True, exist_ok=True)
    svg_png(page, "controller_playstation4", 256, crop=True).save(d / "pad.png", optimize=True)
    for name, (w, h, body) in BADGES.items():
        html = (f"<html><body style='margin:0;background:transparent'><svg xmlns='http://www.w3.org/2000/svg' "
                f"width={w * 2} height={h * 2} viewBox='0 0 {w} {h}'>{body}</svg></body></html>")
        shot(page, html, w * 2, h * 2, True).save(d / f"{name}.png", optimize=True)


def textboxes():
    """Fonds de la zone de saisie (clavier virtuel): ninepatch 48×48, un jeu par ambiance."""
    from PIL import ImageDraw
    d = ROOT / "art" / "ui"
    fills = {"nuit": ((20, 20, 48, 255), (106, 92, 255, 255)), "braise": ((48, 20, 18, 255), (255, 90, 54, 255))}
    for amb, (fill, edge) in fills.items():
        for kind, border in (("inactive", None), ("active", edge)):
            im = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
            dr = ImageDraw.Draw(im)
            dr.rounded_rectangle((0, 0, 191, 191), radius=32, fill=fill, outline=border, width=8 if border else 0)
            im.resize((48, 48), Image.LANCZOS).save(d / f"textbox-{amb}-{kind}.png", optimize=True)


def main():
    only = sys.argv[1:] or list(SYSTEMS)
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page()
        for sid in only:
            name, sub, ang, wmark = SYSTEMS[sid]
            for amb, (c1, c2, top, bot) in AMBIANCES.items():
                html = BG.format(font=FONT, top=top, bot=bot, c1=c1, c2=c2, ang=ang,
                                 bars=bars(c1, c2, sid), name=wmark)
                im = dither(shot(page, html, 1280, 720, scale=1.5).convert("RGB"))
                im.save(ROOT / "art" / "bg" / f"{sid}-{amb}.jpg", quality=85, optimize=True)
            svg = SRC / f"{sid}.svg"
            if svg.exists():
                tmp = ROOT / "art" / "logo" / f"_{sid}.html"
                tmp.write_text(LOGO_SVG.format(src=svg.as_uri()))
                page.set_viewport_size({"width": 1600, "height": 440})
                page.goto(tmp.as_uri()); page.wait_for_timeout(200)
                lg = Image.open(io.BytesIO(page.screenshot(omit_background=True)))
                tmp.unlink()
                lg = lg.crop(lg.getbbox())
            else:
                lg = shot(page, LOGO.format(font=FONT, name=name, sub=sub), 800, 220, True, scale=2)
            lg.save(ROOT / "art" / "logo" / f"{sid}.png", optimize=True)
            (ROOT / sid).mkdir(exist_ok=True)
            (ROOT / sid / "theme.xml").write_text(SYSTEM_XML.format(sid=sid))
        buttons(page)
        badges(page)
        textboxes()
        b.close()


if __name__ == "__main__":
    main()
