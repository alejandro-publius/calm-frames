"""Assemble matched, unaltered static component captures for design review."""
import base64
import hashlib
import json
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT.parent / 'calm-frames-flow/results/whole-flow-2026-10-14/1080'
CURRENT = ROOT / 'results/control-depth-integration-2026-10-14/1080'
OUT = CURRENT.parent / 'comparison'
OUT.mkdir(parents=True, exist_ok=True)
SCREENS = [('Home', '01-home'), ('Details', '02-details-harbor'), ('Settings', '04-household')]
manifest = {'base_source': 'e49f712b7a0d74b3fbc41a4a0c90e232fa559bdc', 'base_evidence_commit': 'b3bc111bbcded8f9512028c1b2a2c2d9aba35bab', 'candidate_source': '867d4493159b172bcbacce56a1fc7b863439d8f1', 'viewport': [1920, 1080], 'kind': 'static component renders; not native verification', 'pairs': []}
def data(path):
    return 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode()
style = '<style>*{box-sizing:border-box}body{margin:0;background:#102f3a;color:#f3e8d3;font:28px Arial}header{height:140px;padding:24px 40px}h1{font-size:38px;margin:0 0 12px}p{margin:0;color:#c8d6d1}.pair{display:flex}.col{width:1920px}h2{height:72px;margin:0;padding:18px 40px;font-size:28px;background:#183c45}img{display:block;width:100%}</style>'
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path='/Users/alexvintera/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell')
    page = browser.new_page(viewport={'width': 3840, 'height': 1292}, device_scale_factor=1)
    overview = []
    for title, name in SCREENS:
        paths = []
        pair = {'screen': title, 'state': name}
        for label, root in [('before', BASE), ('after', CURRENT)]:
            dest = OUT / f'{title.lower()}-{label}.png'
            shutil.copyfile(root / (name + '.png'), dest)
            paths.append(dest)
            pair[label] = {'file': dest.name, 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()}
        manifest['pairs'].append(pair)
        columns = ''.join(f'<section class="col"><h2>{label}</h2><img src="{data(path)}"></section>' for label, path in zip(['BEFORE · Inter · e49f712', 'AFTER · Fraunces + Source Sans 3 · 867d449'], paths))
        page.set_content(style + f'<header><h1>Calm Frames / {title}</h1><p>Matched 1920 × 1080 static component renders · same scene and state · native appearance unverified</p></header><div class="pair">{columns}</div>')
        page.screenshot(path=str(OUT / f'{title.lower()}-before-after.png'))
        overview.append(f'<h2>{title}</h2><div class="pair">'+''.join(f'<img src="{data(path)}">' for path in paths)+'</div>')
    page.set_viewport_size({'width': 1920, 'height': 1870})
    page.set_content('<style>body{margin:0;background:#102f3a;color:#f3e8d3;font:22px Arial}header{height:148px;padding:24px 32px}h1{margin:0 0 10px;font-size:32px}p{margin:0 0 8px}.labels{display:flex;justify-content:space-between}h2{height:34px;padding:4px 32px;font-size:22px;margin:0;background:#183c45}.pair{display:flex}img{width:960px;height:540px}</style><header><h1>Calm Frames: typography & control comparison</h1><p>Static component renders. Same 1920 × 1080 viewport and state; displayed at 50%. Native appearance unverified.</p><div class="labels"><span>BEFORE · Inter · e49f712</span><span>AFTER · Fraunces + Source Sans 3 · 867d449</span></div></header>'+''.join(overview))
    page.screenshot(path=str(OUT / 'calm-frames-before-after.png'))
    browser.close()
(OUT / 'comparison-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
(OUT / 'index.html').write_text('<!doctype html><title>Calm Frames before and after</title><style>body{background:#102f3a;color:#f3e8d3;font:20px sans-serif}img{width:100%}a{color:#ead39d}</style><h1>Calm Frames: before and after</h1><p>Matched static component renders, not native verification. Before source e49f712; after source 867d449.</p>'+''.join(f'<h2>{title}</h2><a href="{title.lower()}-before-after.png"><img src="{title.lower()}-before-after.png"></a>' for title,_ in SCREENS))
print(OUT)
