"""Targeted home capture and text/background samples; browser evidence, not Vega."""
import argparse, json
from pathlib import Path
from playwright.sync_api import sync_playwright
import render_harbor as host

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/whole-flow-2026-10-14'
parser = argparse.ArgumentParser()
parser.add_argument('--browser', required=True)
args = parser.parse_args()
fonts = ''.join(f'@font-face{{font-family:{name};src:url({host.data(ROOT / "app/assets/fonts" / (name + ".ttf"))})}}' for name in ('InterRegular', 'InterMedium', 'InterSemiBold'))
checks = {}
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=args.browser)
    for height in (1080, 720):
        width = height * 16 // 9
        page = browser.new_page(viewport={'width': width, 'height': height}, device_scale_factor=1)
        folder = ROOT / 'app/build/home-preview'
        if height == 720:
            folder /= '720'
        resolution = OUT / str(height)
        checks[str(height)] = {}
        for name in ('home', 'home-parent-focused', 'how-it-works'):
            tree = json.loads((folder / (name + '.json')).read_text())
            page.set_content(f'''<!doctype html><style>{fonts}
*{{box-sizing:border-box}}html,body{{margin:0;width:{width}px;height:{height}px;background:#102f3a}}body{{display:flex;flex-direction:column;overflow:hidden}}
.view{{display:flex;flex-direction:column;position:relative;flex-shrink:0;min-height:0;min-width:0;border-style:solid;border-width:0}}
.text{{display:block;position:relative;flex-shrink:0;white-space:pre-wrap;border-style:solid;border-width:0}}img{{display:block;flex-shrink:0}}.scroll{{overflow:auto;scrollbar-width:none}}
</style>{host.render(tree)}''')
            page.evaluate('document.fonts.ready')
            page.evaluate('Promise.all(Array.from(document.images, image => image.decode()))')
            page.screenshot(path=str(resolution / ('01-' + name + '.png')))
            ids = page.locator('[data-testid]').evaluate_all('els => els.filter(e=>e.dataset.testid).map(e=>{const r=e.getBoundingClientRect();return {id:e.dataset.testid,x:r.x,y:r.y,width:r.width,height:r.height}})')
            bounds_path = resolution / 'bounds.json'
            bounds = json.loads(bounds_path.read_text())
            bounds['01-' + name] = ids
            bounds_path.write_text(json.dumps(bounds, indent=2) + '\n')
            if name == 'how-it-works':
                continue
            label = page.locator('[data-testid="kid-home-parent-area-label"]')
            label_style = label.evaluate('e=>{const s=getComputedStyle(e);return {color:s.color,textShadow:s.textShadow}}')
            assert label_style == {'color': 'rgb(243, 232, 211)', 'textShadow': 'none'}
            control = page.locator('[data-testid="kid-home-parent-area"]')
            control_box = control.bounding_box()
            assert control_box['height'] >= round(88 * height / 1080)
            assert control_box['x'] >= width * .05 and control_box['x'] + control_box['width'] <= width * .95 + 1
            description = page.get_by_text('Supported titles use a still picture during marked scenes while sound continues.', exact=True)
            lines = description.evaluate('e=>{const r=document.createRange();r.selectNodeContents(e);return Array.from(r.getClientRects(),r=>({x:r.x,y:r.y,width:r.width,height:r.height}))}')
            watch = page.locator('[data-testid="kid-home-watch"]').bounding_box()
            assert len(lines) <= 3 and all(line['y'] + line['height'] < watch['y'] for line in lines)
            benefit = page.get_by_text('Watch with fewer flashes.', exact=True)
            assert benefit.is_visible() and page.get_by_text('Details', exact=True).is_visible()
            checks[str(height)][name] = {'parentTarget': control_box, 'labelStyle': label_style, 'descriptionLines': lines, 'controlStyle': control.evaluate('e=>{const s=getComputedStyle(e);return {fill:s.backgroundColor,border:s.borderColor,borderWidth:s.borderWidth}}')}
            # Hide only the glyphs, retaining exact layout, then sample every background pixel under them.
            label.evaluate('e=>e.style.visibility="hidden"')
            page.screenshot(path=str(OUT / 'checks' / f'parent-label-background-{height}-{name}.png'), clip=label.bounding_box())
        page.close()
    browser.close()
(OUT / 'checks/home-refinement-layout.json').write_text(json.dumps(checks, indent=2) + '\n')
print(json.dumps(checks, indent=2))
