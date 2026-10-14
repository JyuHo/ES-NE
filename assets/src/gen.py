G = {
 "E": ["11111","10000","10000","11110","10000","10000","11111"],
 "S": ["01111","10000","10000","01110","00001","00001","11110"],
 "N": ["10001","11001","10101","10101","10011","10001","10001"],
 "-": ["000","000","000","111","000","000","000"],
}
BG1, BG2 = "#1a1f3d", "#0b0e22"
CY, MG, WH = "#27e3ff", "#b05cff", "#f4f7ff"

def defs(uid=""):
    return f'''<defs>
<linearGradient id="bg{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG1}"/><stop offset="1" stop-color="{BG2}"/></linearGradient>
<linearGradient id="ac{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CY}"/><stop offset="1" stop-color="{MG}"/></linearGradient>
</defs>'''

def icon_body(x=0, y=0, s=512, uid="", bg=True):
    k = s/512
    o = []
    if bg:
        o.append(f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{112*k}" fill="url(#bg{uid})"/>')
        o.append(f'<rect x="{x+6*k}" y="{y+6*k}" width="{s-12*k}" height="{s-12*k}" rx="{106*k}" fill="none" stroke="url(#ac{uid})" stroke-opacity=".55" stroke-width="{4*k}"/>')
    o.append(f'<g transform="translate({x+256*k:.2f} {y+256*k:.2f}) scale(1.32) translate({-285*k:.2f} {-268*k:.2f})">')
    # croix directionnelle en pixels (gauche) et deux boutons (droite): une manette, pas une croix médicale
    u, g = 58*k, 6*k
    cx, cy = x+188*k, y+262*k
    for dx, dy in [(0,-1),(0,0),(0,1),(-1,0),(1,0)]:
        px, py = cx+dx*u-u/2+g/2, cy+dy*u-u/2+g/2
        o.append(f'<rect x="{px:.2f}" y="{py:.2f}" width="{u-g:.2f}" height="{u-g:.2f}" rx="{12*k:.2f}" fill="url(#ac{uid})"/>')
    o.append(f'<rect x="{cx-u/2+g/2+10*k:.2f}" y="{cy-u/2+g/2+10*k:.2f}" width="{u-g-20*k:.2f}" height="{u-g-20*k:.2f}" rx="{7*k:.2f}" fill="{BG2}" fill-opacity=".55"/>')
    for bx, by in ((338, 300), (404, 232)):
        o.append(f'<circle cx="{x+bx*k:.2f}" cy="{y+by*k:.2f}" r="{36*k:.2f}" fill="url(#ac{uid})"/>')
        o.append(f'<circle cx="{x+bx*k:.2f}" cy="{y+by*k:.2f}" r="{14*k:.2f}" fill="{BG2}" fill-opacity=".45"/>')
    o.append('</g>')
    return "\n".join(o)

def word(px=24, x=0, y=0, uid="", color_a=WH):
    gap = px*0.14
    out = []
    cx = x
    seq = "ES-NE"
    for i, ch in enumerate(seq):
        fill = color_a if i < 2 else (f"url(#ac{uid})" if i >= 3 else CY)
        if ch == "-": fill = CY
        rows = G[ch]
        for r, row in enumerate(rows):
            for c, v in enumerate(row):
                if v == "1":
                    out.append(f'<rect x="{cx+c*px+gap/2:.2f}" y="{y+r*px+gap/2:.2f}" width="{px-gap:.2f}" height="{px-gap:.2f}" rx="{px*0.2:.2f}" fill="{fill}"/>')
        cx += len(rows[0])*px + px*0.9
    return "\n".join(out), cx - px*0.9 - x

def svg_icon(bg=True):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">\n<title>ES-NE</title>\n{defs()}\n{icon_body(0,0,512,"",bg)}\n</svg>\n'

def svg_logo(dark_bg=True, bg_rect=False):
    px = 22
    w, wordw = word(px, 0, 0, "", WH if dark_bg else "#10142e")
    icon = 7*px + 56   # hauteur de l'icône = hauteur du texte + marge
    H = icon
    W = icon + 36 + wordw
    ty = (H - 7*px)/2
    w, wordw = word(px, icon+36, ty, "", WH if dark_bg else "#10142e")
    bgr = f'<rect width="{W:.0f}" height="{H}" fill="{BG2}"/>' if bg_rect else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H}" width="{W:.0f}" height="{H}">\n<title>ES-NE</title>\n{defs()}\n{bgr}\n{icon_body(0,0,icon,"",True)}\n{w}\n</svg>\n'

open("es-ne-icon.svg","w").write(svg_icon(True))
open("es-ne-icon-nobg.svg","w").write(svg_icon(False))
open("es-ne-logo.svg","w").write(svg_logo(True))
open("es-ne-logo-light.svg","w").write(svg_logo(False))
open("es-ne-logo-banner.svg","w").write(svg_logo(True, True))

# ---- v2: monogramme ES ----
def mono(variant, bg=True):
    s = 512
    px = 36
    gap = px*0.14
    w_cols = 11
    x0 = (s - w_cols*px)/2
    y0 = 92 if variant == "b" else 118
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">', '<title>ES-NE</title>', defs()]
    if bg:
        o.append(f'<rect width="512" height="512" rx="112" fill="url(#bg)"/>')
        o.append(f'<rect x="6" y="6" width="500" height="500" rx="106" fill="none" stroke="url(#ac)" stroke-opacity=".55" stroke-width="4"/>')
    for gi, ch in enumerate("ES"):
        fill = WH if gi == 0 else "url(#ac)"
        for r, row in enumerate(G[ch]):
            for c, v in enumerate(row):
                if v == "1":
                    X = x0 + (gi*6 + c)*px + gap/2
                    Y = y0 + r*px + gap/2
                    o.append(f'<rect x="{X:.2f}" y="{Y:.2f}" width="{px-gap:.2f}" height="{px-gap:.2f}" rx="{px*0.2:.2f}" fill="{fill}"/>')
    if variant == "b":
        # petite manette sous les lettres: croix directionnelle + 2 boutons
        u, g = 20, 3
        cx, cy = 176, 396
        for dx, dy in [(0,-1),(0,0),(0,1),(-1,0),(1,0)]:
            o.append(f'<rect x="{cx+dx*u-u/2+g/2:.2f}" y="{cy+dy*u-u/2+g/2:.2f}" width="{u-g}" height="{u-g}" rx="4" fill="{CY}"/>')
        for bx, by in ((322, 405), (358, 387)):
            o.append(f'<circle cx="{bx}" cy="{by}" r="14" fill="url(#ac)"/>')
        o.append(f'<rect x="236" y="398" width="40" height="8" rx="4" fill="{CY}" fill-opacity=".8"/>')
    o.append('</svg>')
    return "\n".join(o) + "\n"

open("es-ne-icon-mono-a.svg","w").write(mono("a"))
open("es-ne-icon-mono-b.svg","w").write(mono("b"))

# ---- v3: manette avec ES dessus ----
BODY = ("M150 150 H362 C420 150 450 182 466 252 L482 336 C488 382 452 406 418 392 "
        "C388 380 374 352 350 338 H162 C138 352 124 380 94 392 C60 406 24 382 30 336 "
        "L46 252 C62 182 92 150 150 150 Z")

def pad(bg=True, mode="fill"):
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">', '<title>ES-NE</title>', defs()]
    if bg:
        o.append('<rect width="512" height="512" rx="112" fill="url(#bg)"/>')
        o.append('<rect x="6" y="6" width="500" height="500" rx="106" fill="none" stroke="url(#ac)" stroke-opacity=".55" stroke-width="4"/>')
        o.append('<g transform="translate(256 262) scale(.92) translate(-256 -262)">')
    else:
        o.append('<g>')
    ink = BG2
    o.append(f'<path d="{BODY}" fill="url(#ac)"/>')
    # lettres ES en pixels (encre sombre), centrées sur le corps
    px = 20; gap = px*0.14
    x0 = 256 - 11*px/2; y0 = 262 - 7*px/2 - 10
    for gi, ch in enumerate("ES"):
        for r, row in enumerate(G[ch]):
            for c, v in enumerate(row):
                if v == "1":
                    o.append(f'<rect x="{x0+(gi*6+c)*px+gap/2:.2f}" y="{y0+r*px+gap/2:.2f}" width="{px-gap:.2f}" height="{px-gap:.2f}" rx="{px*.2:.2f}" fill="{ink}"/>')
    # croix directionnelle (gauche) et deux boutons (droite), en creux
    u, g = 17, 3
    cx, cy = 92, 258
    for dx, dy in [(0,-1),(0,0),(0,1),(-1,0),(1,0)]:
        o.append(f'<rect x="{cx+dx*u-u/2+g/2:.2f}" y="{cy+dy*u-u/2+g/2:.2f}" width="{u-g}" height="{u-g}" rx="3.5" fill="{ink}"/>')
    for bx, by in ((412, 276), (444, 242)):
        o.append(f'<circle cx="{bx}" cy="{by}" r="14" fill="{ink}"/>')
    # petits boutons centraux
    o.append(f'<rect x="228" y="190" width="22" height="8" rx="4" fill="{ink}" fill-opacity=".0"/>')
    o.append('</g></svg>')
    return "\n".join(o) + "\n"

open("es-ne-icon-pad.svg","w").write(pad(True))
open("es-ne-icon-pad-nobg.svg","w").write(pad(False))

# ---- logo horizontal final (manette ES + mot-symbole) ----
def pad_inner(bg=True):
    s = pad(bg)
    s = s[s.index("</defs>")+7:]
    return s[:s.rindex("</svg>")]

def logo_pad(dark=True, banner=False):
    px = 22
    H = 7*px + 70
    _, wordw = word(px, 0, 0, "")
    W = H + 40 + wordw + (40 if banner else 0)
    ox = 20 if banner else 0
    ty = (H - 7*px)/2
    w, _ = word(px, ox+H+40, ty, "", WH if dark else "#10142e")
    bgr = f'<rect width="{W:.0f}" height="{H}" fill="{BG2}"/>' if banner else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H}" width="{W:.0f}" height="{H}">\n<title>ES-NE</title>\n{defs()}\n{bgr}\n'
            f'<svg x="{ox}" y="0" width="{H}" height="{H}" viewBox="0 0 512 512">{pad_inner(True)}</svg>\n{w}\n</svg>\n')

open("es-ne-logo-pad.svg","w").write(logo_pad(True))
open("es-ne-logo-pad-light.svg","w").write(logo_pad(False))
open("es-ne-logo-pad-banner.svg","w").write(logo_pad(True, True))
