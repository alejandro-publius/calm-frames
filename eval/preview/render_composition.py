"""Bounded Home/Details browser study, paired with the accepted component captures."""
import json, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
import render_harbor as host
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/immersive-composition-2026-10-14'
fonts=''.join(f'@font-face{{font-family:{n};src:url({host.data(ROOT/"app/assets/fonts"/(n+".ttf"))})}}' for n in ('CalmSansRegular','CalmSansSemibold','CalmDisplaySemibold'))
bounds={};contrast={}
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/Users/alexvintera/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell')
 page=browser.new_page()
 for height in (1080,720):
  width=height*16//9; out=OUT/str(height);out.mkdir(parents=True,exist_ok=True)
  page.set_viewport_size({'width':width,'height':height})
  for name in ('home','details'):
   tree=json.loads((ROOT/f'app/build/composition-preview/{height}/{name}.json').read_text())
   page.set_content(f'<style>{fonts}*{{box-sizing:border-box}}html,body{{margin:0;width:{width}px;height:{height}px;background:#151c26}}body{{display:flex;flex-direction:column;overflow:hidden}}.view{{display:flex;flex-direction:column;position:relative;flex-shrink:0;min-height:0;min-width:0;border-style:solid;border-width:0}}.text{{display:block;position:relative;flex-shrink:0;white-space:pre-wrap;border-style:solid;border-width:0}}img{{display:block;flex-shrink:0}}.scroll{{overflow:auto;scrollbar-width:none}}</style>'+host.render(tree))
   page.evaluate('document.fonts.ready');page.screenshot(path=str(out/(name+'.png')))
   if name=='details':
    description=page.locator('[data-testid="title-details-description"]')
    box=description.bounding_box(); description.evaluate("e=>e.style.visibility='hidden'")
    pixels=page.screenshot(clip=box)
    description.evaluate("e=>e.style.visibility='visible'")
    calculation="""import io,sys,json
from PIL import Image
def lum(rgb):
 v=[c/255 for c in rgb[:3]]; v=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in v];return sum(a*b for a,b in zip(v,(.2126,.7152,.0722)))
f=lum((189,194,201));im=Image.open(io.BytesIO(sys.stdin.buffer.read())).convert('RGB');m=min((max(f,lum(c))+.05)/(min(f,lum(c))+.05) for c in im.getdata()); print(json.dumps(m))
"""
    ratio=json.loads(subprocess.check_output(['/Users/alexvintera/calm-frames/.venv/bin/python','-c',calculation],input=pixels))
    contrast[str(height)]=ratio
    assert ratio>=4.5,(height,'synopsis background contrast',ratio)
   bounds[f'{height}-{name}']=page.locator('[data-testid]').evaluate_all('es=>es.filter(e=>e.dataset.testid).map(e=>({id:e.dataset.testid,...e.getBoundingClientRect().toJSON()}))')
   targets=['kid-home-watch','kid-home-more-info','kid-home-learn'] if name=='home' else ['title-details-play','title-details-show-info']
   for target in targets:
    r=page.locator('[data-testid="'+target+'"]').bounding_box()
    assert r and r['x']>=width*.05-1 and r['x']+r['width']<=width*.95+1 and r['y']+r['height']<=height*.95+1,(height,target,r)
  if height==1080:
   page.set_viewport_size({'width':1920,'height':1208})
   cells=[]
   for title,old,new in [('Home','01-home','home'),('Details','02-details-harbor','details')]:
    for label,file in [('Approved candidate',ROOT/f'results/dusk-coast-integration-2026-10-14/1080/{old}.png'),('Alternative composition',out/(new+'.png'))]:
     cells.append(f'<figure><figcaption>{title} · {label}</figcaption><img src="{host.data(file)}"></figure>')
   page.set_content('<style>body{margin:0;background:#151c26;color:#f4ecdd;font:24px sans-serif;display:grid;grid-template-columns:960px 960px}figure{margin:0;height:604px}figcaption{padding:20px 28px;height:64px}img{width:960px;height:540px}</style>'+''.join(cells))
   page.screenshot(path=str(OUT/'before-after.png'))
 browser.close()
(OUT/'bounds.json').write_text(json.dumps(bounds,indent=2)+'\n')
(OUT/'synopsis-contrast.json').write_text(json.dumps(contrast,indent=2)+'\n')
print(OUT)
