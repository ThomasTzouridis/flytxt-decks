# -*- coding: utf-8 -*-
"""Render every slide of a built deck to PNG for checking.  Usage: py tools/render.py <slug> <outdir>"""
import asyncio, pathlib, sys
from playwright.async_api import async_playwright

slug, out = sys.argv[1], pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
page_url = (pathlib.Path(__file__).resolve().parent.parent.parent / slug / "index.html").as_uri()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1600, "height": 900})
        await pg.goto(page_url); await pg.wait_for_timeout(1200)
        n = await pg.evaluate("Reveal.getTotalSlides()")
        for i in range(n):
            await pg.evaluate("Reveal.slide(0,%d)" % i); await pg.wait_for_timeout(2200)
            await pg.screenshot(path=str(out / ("%s_%d.png" % (slug, i + 1))))
        print("rendered", n, "slides to", out)
        await b.close()
asyncio.run(main())
