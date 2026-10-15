"""Matched palette-only static component renders, not native evidence."""
import hashlib
import json
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright

import render_harbor as host

ROOT=Path(__file__).resolve().parents[2]; host.ROOT=ROOT
OUT=ROOT/'results/dusk-coast-palette-study-2026-10-14'; OUT.mkdir(parents=True,exist_ok=True)
BEFORE=ROOT/'results/control-depth-integration-2026-10-14/1080'
fonts=''.join(f'@font-face{{font-family:{n};src:url({host.data(ROOT/"app/assets/fonts"/(n+".ttf"))})}}' for n in ('CalmSansRegular','CalmSansSemibold','CalmDisplaySemibold'))
css=fonts+'''*{box-sizing:border-box}html,body{margin:0;background:#151C26}body{display:flex;flex-direction:column;overflow:hidden}.view{display:flex;flex-direction:column;position:relative;flex-shrink:0;min-height:0;min-width:0;border-style:solid;border-width:0}.text{display:block;position:relative;flex-shrink:0;white-space:pre-wrap;border-style:solid;border-width:0}img{display:block;flex-shrink:0}.scroll{overflow:auto;scrollbar-width:none}'''
states=[('home','home-preview/home.json','01-home.png'),('settings','parent-preview/after/1080/household.json','04-household.png')]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/Users/alexvintera/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell')
    page=browser.new_page(viewport={'width':1920,'height':1080},device_scale_factor=1)
    for name,source,before in states+[('states','dusk-palette-study/states.json',None)]:
        height=430 if name=='states' else 1080
        page.set_viewport_size({'width':1920,'height':height})
        tree=json.loads((ROOT/'app/build'/source).read_text())
        page.set_content(f'<style>{css}html,body{{width:1920px;height:{height}px}}</style>'+host.render(tree)); page.evaluate('document.fonts.ready')
        page.screenshot(path=str(OUT/(name+'-after.png')))
        if before: shutil.copyfile(BEFORE/before,OUT/(name+'-before.png'))
    for name,_,_ in states:
        page.set_viewport_size({'width':3840,'height':1200})
        page.set_content('<style>body{margin:0;background:#151C26;color:#F4ECDD;font:30px Arial}header{height:120px;padding:20px 40px}h1{font-size:36px;margin:0 0 10px}p{margin:0;color:#BDC2C9}.pair{display:flex}img{width:1920px;height:1080px}</style><header><h1>'+name.title()+' · integrated palette / dusk coast study</h1><p>LEFT: current candidate · RIGHT: alternate study · Matched 1920 × 1080 static component renders. Native appearance unverified.</p></header><div class="pair">'+''.join(f'<img src="{host.data(OUT/(name+"-"+stage+".png"))}">' for stage in ('before','after'))+'</div>')
        page.screenshot(path=str(OUT/(name+'-palette-comparison.png')))
    page.set_viewport_size({'width':1920,'height':1660})
    page.set_content('<style>body{margin:0;background:#151C26;color:#F4ECDD;font:24px Arial}header{height:90px;padding:20px 32px}h1{margin:0;font-size:30px}.pair{display:flex}img{display:block}.pair img{width:960px;height:540px}h2{height:30px;margin:0;padding:3px 32px;font-size:22px;background:#303B48}.strip{width:1920px;height:430px}</style><header><h1>Dusk coast study · current palette left / alternate right</h1><span>Same typography, layout, content and original artwork. Static component renders; native appearance unverified.</span></header>'+''.join('<h2>'+name.title()+'</h2><div class="pair">'+''.join(f'<img src="{host.data(OUT/(name+"-"+stage+".png"))}">' for stage in ('before','after'))+'</div>' for name,_,_ in states)+f'<img class="strip" src="{host.data(OUT/"states-after.png")}">')
    page.screenshot(path=str(OUT/'dusk-coast-overview.png')); browser.close()
shutil.copyfile(ROOT/'app/build/dusk-palette-study/palette.json',OUT/'palette.json')
(OUT/'SHA256SUMS').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name+'\n' for f in sorted(OUT.iterdir()) if f.is_file() and f.name!='SHA256SUMS'))
print(OUT)
