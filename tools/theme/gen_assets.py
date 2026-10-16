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

DESC = {
 "nes": [
  "Console 8 bits de Nintendo (Famicom au Japon dès 1983). Elle a relancé le jeu de salon avec Super Mario Bros. et The Legend of Zelda.",
  "Nintendo's 8-bit console (Famicom in Japan from 1983). It revived home gaming with Super Mario Bros. and The Legend of Zelda."
 ],
 "snes": [
  "La 16 bits de Nintendo (1990). Super Mario World, A Link to the Past, Chrono Trigger et le fameux Mode 7.",
  "Nintendo's 16-bit console (1990). Super Mario World, A Link to the Past, Chrono Trigger and the famous Mode 7."
 ],
 "gb": [
  "La portable à écran monochrome de Nintendo (1989). Tetris et Pokémon en ont fait une légende.",
  "Nintendo's monochrome handheld (1989). Tetris and Pokémon made it a legend."
 ],
 "gbc": [
  "La Game Boy en couleurs (1998), compatible avec les jeux de la Game Boy d'origine.",
  "The Game Boy in color (1998), compatible with original Game Boy games."
 ],
 "gba": [
  "Portable 32 bits de Nintendo (2001), à écran horizontal, compatible Game Boy et Game Boy Color.",
  "Nintendo's 32-bit handheld (2001), with a horizontal screen, compatible with Game Boy and Game Boy Color."
 ],
 "mastersystem": [
  "Console 8 bits de Sega (1985). Alex Kidd et Phantasy Star ; très populaire en Europe et au Brésil.",
  "Sega's 8-bit console (1985). Alex Kidd and Phantasy Star; hugely popular in Europe and Brazil."
 ],
 "megadrive": [
  "La 16 bits de Sega (1988, Genesis en Amérique du Nord). Sonic the Hedgehog et Streets of Rage.",
  "Sega's 16-bit console (1988, Genesis in North America). Sonic the Hedgehog and Streets of Rage."
 ],
 "gamegear": [
  "Portable couleur rétroéclairée de Sega (1990), basée sur le matériel de la Master System.",
  "Sega's backlit color handheld (1990), built on Master System hardware."
 ],
 "dreamcast": [
  "La dernière console de Sega (1998), première à intégrer un modem. Shenmue, Jet Set Radio, Sonic Adventure.",
  "Sega's last console (1998), the first with a built-in modem. Shenmue, Jet Set Radio, Sonic Adventure."
 ],
 "n64": [
  "Console 64 bits de Nintendo (1996) à cartouches, avec stick analogique et quatre ports manettes. Super Mario 64, Ocarina of Time.",
  "Nintendo's 64-bit cartridge console (1996), with an analog stick and four controller ports. Super Mario 64, Ocarina of Time."
 ],
 "gc": [
  "Console compacte de Nintendo (2001) à mini-disques. Super Smash Bros. Melee, The Wind Waker.",
  "Nintendo's compact console (2001) using mini discs. Super Smash Bros. Melee, The Wind Waker."
 ],
 "wii": [
  "Console de Nintendo (2006) misant sur la télécommande à détection de mouvement. Wii Sports, Mario Kart Wii.",
  "Nintendo's 2006 console built around a motion-sensing remote. Wii Sports, Mario Kart Wii."
 ],
 "wiiu": [
  "Console de Nintendo (2012) avec la manette GamePad à écran tactile, compatible avec les jeux Wii.",
  "Nintendo's 2012 console with a touchscreen GamePad, compatible with Wii games."
 ],
 "switch": [
  "Console hybride de Nintendo (2017), de salon ou portable, avec ses manettes Joy-Con amovibles.",
  "Nintendo's hybrid console (2017), home or handheld, with detachable Joy-Con controllers."
 ],
 "nds": [
  "Portable de Nintendo (2004) à deux écrans dont un tactile. Pokémon, Nintendogs, New Super Mario Bros.",
  "Nintendo's dual-screen handheld (2004), one touch-sensitive. Pokémon, Nintendogs, New Super Mario Bros."
 ],
 "pcengine": [
  "Console de NEC et Hudson Soft (1987) : processeur 8 bits, graphismes 16 bits. TurboGrafx-16 en Amérique du Nord.",
  "NEC and Hudson Soft's console (1987): 8-bit CPU, 16-bit graphics. Sold as the TurboGrafx-16 in North America."
 ],
 "atari2600": [
  "La console Atari à cartouches (1977), alors appelée Video Computer System. Pitfall!, Space Invaders, Adventure.",
  "Atari's cartridge console (1977), then called the Video Computer System. Pitfall!, Space Invaders, Adventure."
 ],
 "arcade": [
  "Les bornes d'arcade, de l'âge d'or des années 1970-80 à nos jours, émulées via MAME et FinalBurn.",
  "Arcade cabinets, from the golden age of the 1970s-80s to today, emulated with MAME and FinalBurn."
 ],
 "xbox": [
  "La première console de Microsoft (2001), avec disque dur intégré et Xbox Live. Halo : Combat Evolved.",
  "Microsoft's first console (2001), with a built-in hard drive and Xbox Live. Halo: Combat Evolved."
 ],
 "xbox360": [
  "Console de Microsoft (2005) : haute définition, succès et Xbox Live Arcade.",
  "Microsoft's 2005 console: high definition, achievements and Xbox Live Arcade."
 ],
 "steam": [
  "La plateforme de jeux PC de Valve (2003). Les jeux de votre bibliothèque Steam, lancés depuis l'interface.",
  "Valve's PC gaming platform (2003). The games from your Steam library, launched from the interface."
 ],
 "windows": [
  "Les jeux PC Windows, lancés sous Linux grâce à une couche de compatibilité.",
  "Windows PC games, launched on Linux through a compatibility layer."
 ],
 "ports": [
  "Ports natifs et réimplémentations de jeux, lancés directement sous Linux.",
  "Native ports and reimplementations of games, launched directly on Linux."
 ],
 "psx": [
  "La première PlayStation (1994). Elle a imposé le CD-ROM et la 3D : Final Fantasy VII, Metal Gear Solid, Gran Turismo.",
  "The first PlayStation (1994). It established CD-ROM and 3D: Final Fantasy VII, Metal Gear Solid, Gran Turismo."
 ],
 "ps2": [
  "La console la plus vendue de l'histoire (2000), lecteur DVD intégré et compatible avec les jeux PlayStation.",
  "The best-selling console ever (2000), with a built-in DVD drive and PlayStation game compatibility."
 ],
 "ps3": [
  "Console de Sony (2006) : processeur Cell, Blu-ray et PlayStation Network.",
  "Sony's 2006 console: Cell processor, Blu-ray and the PlayStation Network."
 ],
 "psp": [
  "Portable de Sony (2004) à grand écran large et disques UMD. God of War: Chains of Olympus, Monster Hunter.",
  "Sony's widescreen handheld (2004) using UMD discs. God of War: Chains of Olympus, Monster Hunter."
 ]
}

SYSTEM_XML = """<theme>
	<formatVersion>7</formatVersion>
	<include>./../theme.xml</include>
	<view name="system">
		<image name="logo">
			<path>./../art/logo/{sid}.png</path>
		</image>
{desc}		<image name="bg" extra="true">
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


def desc_xml(sid, sub):
    from xml.sax.saxutils import escape
    if sid not in DESC:
        return ""
    fr, en = DESC[sid]
    return f"""		<text name="sysmaker" extra="true">
			<text>{escape(sub)}</text>
			<pos>0.5 0.24</pos>
			<origin>0.5 0.5</origin>
			<size>0.6 0.04</size>
			<alignment>center</alignment>
			<fontPath>${{fontBold}}</fontPath>
			<fontSize>0.03</fontSize>
			<color>${{accent2}}</color>
			<zIndex>45</zIndex>
		</text>
		<text name="sysdesc" extra="true">
			<text>{escape(en)}</text>
			<text lang="fr">{escape(fr)}</text>
			<pos>0.5 0.34</pos>
			<origin>0.5 0.5</origin>
			<size>0.56 0.16</size>
			<alignment>center</alignment>
			<fontPath>${{font}}</fontPath>
			<fontSize>0.036</fontSize>
			<lineSpacing>1.2</lineSpacing>
			<color>${{text}}</color>
			<zIndex>45</zIndex>
		</text>
"""


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



# --- pastilles d'information (blanc pur, teintées dans le thème) ---
BADGES = {
    "pad": (128, 80, """<defs><mask id=m><rect width=128 height=80 fill=#fff />
<path d="M24 28h12M30 22v12" stroke=#000 stroke-width=6 />
<circle cx=96 cy=24 r=5 /><circle cx=106 cy=34 r=5 /><circle cx=96 cy=44 r=5 /><circle cx=86 cy=34 r=5 />
<circle cx=50 cy=48 r=7 /><circle cx=78 cy=48 r=7 /></mask></defs>
<path mask=url(#m) d="M30 10H98C113 10 121 23 125 48C128 66 123 75 112 75C101 75 97 66 91 58H37C31 66 27 75 16 75C5 75 0 66 3 48C7 23 15 10 30 10Z" fill=#fff />"""),
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
    for name, (w, h, body) in BADGES.items():
        html = (f"<html><body style='margin:0;background:transparent'><svg xmlns='http://www.w3.org/2000/svg' "
                f"width={w * 2} height={h * 2} viewBox='0 0 {w} {h}'>{body}</svg></body></html>")
        shot(page, html, w * 2, h * 2, True).save(d / f"{name}.png", optimize=True)


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
            (ROOT / sid / "theme.xml").write_text(SYSTEM_XML.format(sid=sid, desc=desc_xml(sid, sub)))
        buttons(page)
        badges(page)
        b.close()


if __name__ == "__main__":
    main()
