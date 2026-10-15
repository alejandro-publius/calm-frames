"""Render the actual home host trees headlessly; this is not native evidence."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

import render_harbor as host

ROOT = Path(__file__).resolve().parents[2]
host.ROOT = ROOT
OUT = ROOT / 'results/home-introduction-2026-10-14'
OUT.mkdir(parents=True, exist_ok=True)
fonts = ''.join(f'@font-face{{font-family:{name};src:url({host.data(ROOT / "app/assets/fonts" / (name + ".ttf"))})}}' for name in ('InterRegular', 'InterMedium', 'InterSemiBold'))
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--browser', default=None, help='Existing headless Chromium executable')
args = parser.parse_args()
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=args.browser)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080}, device_scale_factor=1)
    bounds = {}
    for name in ('home', 'how-it-works', 'loading', 'opening'):
        tree = json.loads((ROOT / f'app/build/home-preview/{name}.json').read_text())
        content = f'''<!doctype html><html><head><style>{fonts}
*{{box-sizing:border-box}}html,body{{margin:0;width:1920px;height:1080px;background:#102f3a}}body{{display:flex;flex-direction:column;overflow:hidden}}
.view{{display:flex;flex-direction:column;position:relative;flex-shrink:0;min-height:0;min-width:0;border-style:solid;border-width:0}}
.text{{display:block;position:relative;flex-shrink:0;white-space:pre-wrap;border-style:solid;border-width:0}}img{{display:block;flex-shrink:0}}.scroll{{overflow:auto;scrollbar-width:none}}
</style></head><body>{host.render(tree)}</body></html>'''
        (ROOT / f'app/build/home-preview/{name}.html').write_text(content)
        page.set_content(content)
        page.evaluate('document.fonts.ready')
        page.screenshot(path=str(OUT / f'{name}-browser.png'))
        bounds[name] = page.locator('[data-testid]').evaluate_all('els => els.map(e=>({id:e.dataset.testid,x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height}))')
    (OUT / 'browser-bounds.json').write_text(json.dumps(bounds, indent=2)+'\n')
    browser.close()
