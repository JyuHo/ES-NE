import asyncio, pathlib
from playwright.async_api import async_playwright
D = pathlib.Path(__file__).resolve().parent
jobs = [("es-ne-icon-pad.svg",[512,256,128,64,48],"icon"),("es-ne-icon-pad-nobg.svg",[512],"icon-nobg"),("es-ne-logo-pad.svg",[1200],"logo"),("es-ne-logo-pad-light.svg",[1200],"logo-light"),("es-ne-logo-pad-banner.svg",[1200],"banner")]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f, sizes, tag in jobs:
            for s in sizes:
                pg = await b.new_page(viewport={"width":s,"height":s})
                await pg.goto((D/f).as_uri())
                await pg.evaluate("""(s) => {const e=document.documentElement; const vb=e.viewBox.baseVal; e.setAttribute('width', s); e.setAttribute('height', s*vb.height/vb.width);}""", s)
                el = await pg.query_selector("svg")
                name = f"es-ne-{tag}-{s}.png" if tag.startswith("icon") else f"es-ne-{tag}.png"
                await el.screenshot(path=str(D/name), omit_background=True)
                await pg.close()
        await b.close()
asyncio.run(main())
