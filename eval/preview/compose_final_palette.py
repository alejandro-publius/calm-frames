"""Matched previous/current static component captures; media remains a substitute."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

import render_harbor as host

ROOT=Path(__file__).resolve().parents[2];host.ROOT=ROOT
BASE=ROOT/'results/control-depth-integration-2026-10-14/1080'
CURRENT=ROOT/'results/dusk-coast-integration-2026-10-14/1080'
OUT=CURRENT.parent/'comparisons';OUT.mkdir(parents=True,exist_ok=True)
groups={
    'library-and-help': [('Home','01-home'),('Details','02-details-harbor'),('Settings','04-household'),('Help','01-how-it-works')],
    'startup-and-setup': [('Startup','01-bootstrap'),('Player opening','01-opening'),('Parent PIN','04-locked'),('First-run setup','05-setup-preset')],
    'player-and-captions': [('Player controls','03-controls-back'),('Paused playback','03-paused-story'),('Hold + caption menu + multiline cue','03-hold-caption-menu'),('Recoverable error','03-error')],
}
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/Users/alexvintera/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell')
    page=browser.new_page(viewport={'width':1920,'height':2400},device_scale_factor=1)
    for group,states in groups.items():
        body='<header><h1>Calm Frames / '+group.replace('-',' ')+'</h1><p>Before left · approved dusk coast right · matched 1920 × 1080 states shown at 50%.</p><p>Static component renders. Native video, captions and seekbar are substitutes; native verification pending.</p></header>'
        for label,name in states:
            body+='<h2>'+label+'</h2><div class="pair">'+''.join(f'<img src="{host.data(folder/(name+".png"))}">' for folder in (BASE,CURRENT))+'</div>'
        page.set_content('<style>body{margin:0;background:#151C26;color:#F4ECDD;font:23px Arial}header{height:120px;padding:16px 32px}h1{margin:0 0 8px;font-size:32px}p{margin:0 0 5px}h2{margin:0;height:30px;padding:3px 32px;background:#303B48;font-size:22px}.pair{display:flex}img{display:block;width:960px;height:540px}</style>'+body)
        page.screenshot(path=str(OUT/(group+'.png')))
    fonts=''.join(f'@font-face{{font-family:{n};src:url({host.data(ROOT/"app/assets/fonts"/(n+".ttf"))})}}' for n in ('CalmSansRegular','CalmSansSemibold','CalmDisplaySemibold'))
    page.set_viewport_size({'width':1920,'height':430})
    page.set_content('<style>'+fonts+'*{box-sizing:border-box}html,body{margin:0;width:1920px;height:430px;background:#151C26}body{display:flex;flex-direction:column;overflow:hidden}.view{display:flex;flex-direction:column;position:relative;flex-shrink:0;min-width:0;border-style:solid;border-width:0}.text{display:block;position:relative;white-space:pre-wrap;flex-shrink:0;border-style:solid;border-width:0}</style>'+host.render(json.loads((ROOT/'app/build/dusk-palette-study/states.json').read_text())))
    page.evaluate('document.fonts.ready');page.screenshot(path=str(OUT/'final-control-states.png'))
    page.set_viewport_size({'width':1920,'height':1620})
    page.set_content('<style>body{margin:0;background:#151C26;color:#F4ECDD;font:24px Arial}header{height:110px;padding:20px 32px}h1{font-size:32px;margin:0 0 10px}p{margin:0}img{display:block;width:1920px}</style><header><h1>Final palette / loading and shared control states</h1><p>Static component renders; native loading/video/input unverified. Existing loading behavior preserved.</p></header>'+f'<img src="{host.data(CURRENT/"03-loading.png")}"><img src="{host.data(OUT/"final-control-states.png")}">')
    page.screenshot(path=str(OUT/'loading-and-control-states.png'));browser.close()
(OUT/'index.html').write_text('<!doctype html><title>Approved dusk coast integration</title><style>body{background:#151C26;color:#F4ECDD;font:20px sans-serif}img{width:100%}</style><h1>Approved palette: matched static component captures</h1><p>Native appearance is unverified. Video, captions and seekbar are substitutes.</p>'+''.join(f'<h2>{name}</h2><a href="{name}.png"><img src="{name}.png"></a>' for name in [*groups,'loading-and-control-states']))
print(OUT)
