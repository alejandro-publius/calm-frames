"""Render real playback host trees with labelled native substitutes; never Vega proof."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

import render_harbor as host

ROOT = Path(__file__).resolve().parents[2]
base_render = host.render
HEIGHT = 1080


def render(node):
    if not isinstance(node, dict):
        return base_render(node)
    kind, props = node['type'], node.get('props', {})
    css = host.style(props.get('style'))
    identity = html.escape(props.get('testID', ''), quote=True)
    if kind == 'Image' and isinstance(props.get('source'), dict) and props['source'].get('uri', '').startswith('data:image/'):
        return f'<img data-testid="{identity}" style="{css};width:100%;height:100%;object-fit:contain" src="{props["source"]["uri"]}">'
    if kind == 'PreviewMaterialIcon':
        glyphs = json.loads((ROOT / 'app/node_modules/@amazon-devices/react-native-vector-icons/glyphmaps/MaterialIcons.json').read_text())
        return f'<span style="display:block;font-family:MaterialIcons;font-size:{props["size"]}px;line-height:1;color:{props["color"]}">&#{glyphs[props["name"]]};</span>'
    if kind == 'PreviewVideoSurface':
        # Artwork is a stationary stand-in, not a decoded native video frame.
        uri = host.data(ROOT / 'app/assets/image/tv/harbor-cinematic.png')
        return f'<img data-testid="{identity}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;{css}" src="{uri}">'
    if kind == 'PreviewNativeCaptions':
        if not props.get('show'):
            return ''
        cue = html.escape((ROOT / 'app/assets/raw/benign-story/harbor.vtt').read_text().splitlines()[6])
        return f'<div data-testid="{identity}" style="{css};display:flex;align-items:center;justify-content:flex-end;flex-direction:column"><span style="font: {32 * HEIGHT / 1080}px InterRegular;color:white;background:black;padding:8px 16px">{cue}</span></div>'
    if kind == 'PreviewNativeSeekBar':
        return f'<div data-testid="{identity}" style="height:{12 * HEIGHT / 1080}px;background:#667777;border-radius:6px"><div style="width:30%;height:100%;background:#eee"></div></div>'
    return base_render(node)


host.render = render


def main():
    global HEIGHT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('before', 'after'), required=True)
    parser.add_argument('--source-root', type=Path, default=ROOT)
    args = parser.parse_args()
    fonts = ''.join(f'@font-face{{font-family:{name};src:url({host.data(ROOT / "app/assets/fonts" / (name + ".ttf"))})}}' for name in ('InterRegular', 'InterMedium', 'InterSemiBold'))
    fonts += f'@font-face{{font-family:MaterialIcons;src:url({host.data(ROOT / "app/node_modules/@amazon-devices/react-native-vector-icons/Fonts/MaterialIcons.ttf")})}}'
    bounds = {}
    checks = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for height in (1080, 720):
            HEIGHT = height
            width = height * 16 // 9
            page = browser.new_page(viewport={'width': width, 'height': height}, device_scale_factor=1)
            folder = ROOT / f'docs/design/playback-refinement/{args.stage}/{height}'
            folder.mkdir(parents=True, exist_ok=True)
            trees = sorted((args.source_root / f'app/build/playback-preview/{args.stage}/{height}').glob('*.json'))
            assert len(trees) == 8, trees
            for tree_file in trees:
                tree = json.loads(tree_file.read_text())
                page.set_content(f'''<!doctype html><html><head><meta charset="utf-8"><title>{tree_file.stem}: browser approximation</title><style>
{fonts}
*{{box-sizing:border-box}}html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden;background:#000}}
body{{display:flex;font-family:InterRegular}}.view{{display:flex;flex-direction:column;flex-shrink:0;position:relative;min-width:0;border-style:solid;border-width:0}}
.text{{display:block;position:relative;flex-shrink:0;white-space:pre-wrap;border-style:solid;border-width:0}}img{{display:block;flex-shrink:0}}
</style></head><body>{render(tree)}</body></html>''')
                page.evaluate('document.fonts.ready')
                bounds[f'{height}/{tree_file.stem}'] = page.locator('[data-testid]').evaluate_all('els => els.filter(e=>e.dataset.testid).map(e=>{const r=e.getBoundingClientRect();const top=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {id:e.dataset.testid,text:e.innerText?.slice(0,200),x:r.x,y:r.y,width:r.width,height:r.height,centerVisible:!!top&&(e===top||e.contains(top)),zIndex:getComputedStyle(e).zIndex}})')
                page.screenshot(path=str(folder / (tree_file.stem + '.png')))
            def rows(name, height=height):
                return {row['id']: row for row in bounds[f'{height}/{name}']}

            error = rows('error')
            controls = rows('controls-captions')
            menu = rows('caption-menu')
            checks[str(height)] = {
                'error_message_visible': error['error-boundary-label']['centerVisible'],
                'error_back_visible': error.get('player-error-back', {}).get('centerVisible', False),
                'paused_hold_identified': 'player-paused' in rows('paused-hold') and 'Paused.' in rows('paused-hold')['calm-card-detail']['text'],
                'paused_story_identified': 'player-paused' in rows('paused-story'),
                'controls_within_safe_area': all(controls['video-player-caption-btn'][key] >= limit - 1 for key, limit in [('x', width * .05), ('y', height * .05)]) and controls['video-player-caption-btn']['x'] + controls['video-player-caption-btn']['width'] <= width * .95 + 1 and controls['video-player-caption-btn']['y'] + controls['video-player-caption-btn']['height'] <= height * .95 + 1,
                'seekbar_above_caption_button': 'kui-seekbar' in controls and controls['kui-seekbar']['y'] + controls['kui-seekbar']['height'] < controls['video-player-caption-btn']['y'],
                'menu_above_caption_band': menu['caption-menu-focus-element']['y'] + menu['caption-menu-focus-element']['height'] < menu['kepler-captions-view']['y'] + menu['kepler-captions-view']['height'] - height * 60 / 1080,
            }
            for name in ('controls-back', 'controls-captions', 'caption-menu'):
                pixels = Image.open(folder / (name + '.png')).convert('RGB')
                checks[str(height)][name + '_gold_focus_ring'] = sum(count for count, color in pixels.getcolors(width * height) if color == (230, 169, 87)) > 300 * (height / 720) ** 2
            if args.stage == 'after':
                assert all(checks[str(height)].values()), checks[str(height)]
            page.close()
        browser.close()
    (ROOT / f'docs/design/playback-refinement/{args.stage}/checks.json').write_text(json.dumps(checks, indent=2) + '\n')
    (ROOT / f'docs/design/playback-refinement/{args.stage}/bounds.json').write_text(json.dumps(bounds, indent=2) + '\n')


if __name__ == '__main__':
    main()
