"""Dusk lantern Home and Details: browser renders of the actual component trees.

Static evidence only. It reuses the composition export (eval/preview/export_composition.py
writes app/build/composition-preview/{1080,720}/{home,details}.json) and the same host
renderer as the earlier studies, then writes matched 1080p and 720p captures, a
before-and-after sheet against the immersive study renders this branch started from,
control bounds inside the 5 per cent safe area, and the synopsis contrast over the scene.
These are not simulator screenshots.
"""
import json
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

import render_harbor as host

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/dusk-lantern-2026-10-14'
BEFORE = ROOT / 'results/immersive-composition-2026-10-14'
CHROME = ('/Users/alexvintera/Library/Caches/ms-playwright/chromium_headless_shell-1243/'
          'chrome-headless-shell-mac-arm64/chrome-headless-shell')
PIL_PYTHON = '/Users/alexvintera/calm-frames/.venv/bin/python'
FONTS = ''.join(
    f'@font-face{{font-family:{name};src:url({host.data(ROOT / "app/assets/fonts" / (name + ".ttf"))})}}'
    for name in ('CalmSansRegular', 'CalmSansSemibold', 'CalmDisplaySemibold'))
PAGE_CSS = ('*{box-sizing:border-box}html,body{margin:0;width:%dpx;height:%dpx;background:#151c26}'
            'body{display:flex;flex-direction:column;overflow:hidden}'
            '.view{display:flex;flex-direction:column;position:relative;flex-shrink:0;min-height:0;min-width:0;border-style:solid;border-width:0}'
            '.text{display:block;position:relative;flex-shrink:0;white-space:pre-wrap;border-style:solid;border-width:0}'
            'img{display:block;flex-shrink:0}.scroll{overflow:auto;scrollbar-width:none}')
CONTRAST = """import io,sys,json
from PIL import Image
def lum(rgb):
 v=[c/255 for c in rgb[:3]]; v=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in v];return sum(a*b for a,b in zip(v,(.2126,.7152,.0722)))
f=lum((189,194,201));im=Image.open(io.BytesIO(sys.stdin.buffer.read())).convert('RGB');m=min((max(f,lum(c))+.05)/(min(f,lum(c))+.05) for c in im.getdata()); print(json.dumps(m))
"""
TARGETS = {
    'home': ['kid-home-watch', 'kid-home-more-info', 'kid-home-demo', 'kid-home-learn', 'kid-home-parent-area', 'kid-home-no-holds'],
    'details': ['title-details-play', 'title-details-show-info', 'title-details-meta'],
}
# Text whose background is measured against TEXT_DIM, because it sits over the scene.
DIM_TEXT = {'home': ['kid-home-no-holds'], 'details': ['title-details-description']}

bounds = {}
contrast = {}
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True, executable_path=CHROME)
    page = browser.new_page()
    for height in (1080, 720):
        width = height * 16 // 9
        out = OUT / str(height)
        out.mkdir(parents=True, exist_ok=True)
        page.set_viewport_size({'width': width, 'height': height})
        for name in ('home', 'details'):
            tree = json.loads((ROOT / f'app/build/composition-preview/{height}/{name}.json').read_text())
            page.set_content(f'<style>{FONTS}{PAGE_CSS % (width, height)}</style>' + host.render(tree))
            page.evaluate('document.fonts.ready')
            page.screenshot(path=str(out / (name + '.png')))
            for test_id in DIM_TEXT[name]:
                node = page.locator(f'[data-testid="{test_id}"]')
                box = node.bounding_box()
                node.evaluate("e=>e.style.visibility='hidden'")
                pixels = page.screenshot(clip=box)
                node.evaluate("e=>e.style.visibility='visible'")
                ratio = json.loads(subprocess.check_output([PIL_PYTHON, '-c', CONTRAST], input=pixels))
                contrast[f'{height}-{test_id}'] = ratio
                assert ratio >= 4.5, (height, test_id, 'background contrast under TEXT_DIM', ratio)
            bounds[f'{height}-{name}'] = page.locator('[data-testid]').evaluate_all(
                'es=>es.filter(e=>e.dataset.testid).map(e=>({id:e.dataset.testid,...e.getBoundingClientRect().toJSON()}))')
            for target in TARGETS[name]:
                rect = page.locator(f'[data-testid="{target}"]').bounding_box()
                assert rect, (height, name, target, 'not rendered')
                inside = (rect['x'] >= width * .05 - 1 and rect['x'] + rect['width'] <= width * .95 + 1
                          and rect['y'] >= height * .05 - 1 and rect['y'] + rect['height'] <= height * .95 + 1)
                assert inside, (height, target, rect)
            # The lighthouse stays clear: nothing with a test id covers its lamp.
            if name == 'home':
                lamp = {'x': width * .80, 'y': height * .15, 'w': width * .09, 'h': height * .30}
                for entry in bounds[f'{height}-{name}']:
                    if entry['id'] in ('kid-home', 'home-harbor-scene', 'home-water-ripples'):
                        continue
                    overlaps = not (entry['x'] + entry['width'] < lamp['x'] or entry['x'] > lamp['x'] + lamp['w']
                                    or entry['y'] + entry['height'] < lamp['y'] or entry['y'] > lamp['y'] + lamp['h'])
                    assert not overlaps or entry['width'] == 0, (height, 'covers the lighthouse', entry)
        if height == 1080:
            page.set_viewport_size({'width': 1920, 'height': 1208})
            cells = []
            for title, name in (('Home', 'home'), ('Details', 'details')):
                for label, file in (('Before: f95a366 immersive study', BEFORE / f'1080/{name}.png'),
                                    ('After: dusk lantern', out / f'{name}.png')):
                    cells.append(f'<figure><figcaption>{title} · {label}</figcaption><img src="{host.data(file)}"></figure>')
            page.set_content('<style>body{margin:0;background:#151c26;color:#f4ecdd;font:24px sans-serif;display:grid;grid-template-columns:960px 960px}'
                             'figure{margin:0;height:604px}figcaption{padding:20px 28px;height:64px}img{width:960px;height:540px}</style>' + ''.join(cells))
            page.screenshot(path=str(OUT / 'before-after.png'))
    browser.close()
(OUT / 'bounds.json').write_text(json.dumps(bounds, indent=2) + '\n')
(OUT / 'contrast.json').write_text(json.dumps(contrast, indent=2) + '\n')
print(OUT)
