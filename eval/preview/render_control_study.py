"""Native-component control study, rendered as an explicitly labelled browser approximation."""
import argparse, json
from pathlib import Path
from playwright.sync_api import sync_playwright
import render_harbor as host
ROOT = Path(__file__).resolve().parents[2]
host.ROOT = ROOT
OUT = ROOT / 'results/control-depth-study-2026-10-14'
parser = argparse.ArgumentParser(); parser.add_argument('--browser', required=True); args = parser.parse_args()
fonts = ''.join(f'@font-face{{font-family:{name};src:url({host.data(ROOT / "app/assets/fonts" / (name + ".ttf"))})}}' for name in ('InterRegular', 'InterMedium', 'InterSemiBold'))
with sync_playwright() as p:
 browser = p.chromium.launch(headless=True, executable_path=args.browser)
 for height in (1080,720):
  width=height*16//9; unit=height/1080; folder=OUT/str(height); folder.mkdir(parents=True,exist_ok=True)
  page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
  bounds={};names=[]
  for name in ['controls','selected-rows','home-default','home-focus','settings-group']:
   tree=json.loads((ROOT/'app/build/control-study'/str(height)/(name+'.json')).read_text())
   if name=='selected-rows':
    body=f'<main class="view" style="padding:{54*unit}px {96*unit}px"><h1 style="font:{64*unit}px/{76*unit}px InterRegular;margin:0">Selection and focus</h1><p style="font:{32*unit}px/{42*unit}px InterRegular;color:#bdd0cf;margin:{12*unit}px 0 {20*unit}px">Actual selected settings row · browser rendering · native pixels pending</p>'
    for item in tree:
     body+=f'<section class="view" style="margin-bottom:0"><span style="font:{28*unit}px/{34*unit}px InterRegular;color:#bdd0cf;margin-bottom:{6*unit}px">{item["state"]}</span>{host.render(item["tree"])}</section>'
    body+='</main>'
   else: body=host.render(tree)
   page.set_content(f'''<!doctype html><style>{fonts}
*{{box-sizing:border-box}}html,body{{margin:0;width:{width}px;height:{height}px;background:#102f3a;color:#f3e8d3}}body{{display:flex;flex-direction:column;overflow:hidden}}
.view{{display:flex;flex-direction:column;position:relative;flex-shrink:0;min-height:0;min-width:0;border-style:solid;border-width:0}}
.text{{display:block;position:relative;flex-shrink:0;white-space:pre-wrap;border-style:solid;border-width:0}}img{{display:block;flex-shrink:0}}.scroll{{overflow:auto;scrollbar-width:none}}
</style>{body}''')
   page.evaluate('document.fonts.ready');page.evaluate('Promise.all(Array.from(document.images, image=>image.decode()))')
   if name=='settings-group':
    page.locator('.scroll').first.evaluate('(e,y)=>e.scrollTop+=y',page.locator('[data-testid="parent-area-preset-wcag"]').bounding_box()['y']-height*.11)
   page.screenshot(path=str(folder/(name+'.png')));names.append(name)
   bounds[name]=page.locator('[data-testid]').evaluate_all('es=>es.filter(e=>e.dataset.testid).map(e=>{const r=e.getBoundingClientRect();return {id:e.dataset.testid,x:r.x,y:r.y,width:r.width,height:r.height}})')
   if name=='settings-group':
    group=page.locator('[data-testid="parent-area-preset-wcag"]').locator('..').bounding_box()
    assert group and group['y'] >= 0 and group['y']+group['height'] < height
    page.screenshot(path=str(folder/'settings-group-closeup.png'),clip=group);names.append('settings-group-closeup')
   if name.startswith('home'):
    first=page.locator('[data-testid="kid-home-watch"]').bounding_box();last=page.locator('[data-testid="kid-home-more-info"]').bounding_box()
    clip={'x':first['x']-12*unit,'y':first['y']-12*unit,'width':last['x']+last['width']-first['x']+24*unit,'height':max(first['height'],last['height'])+24*unit}
    page.screenshot(path=str(folder/(name+'-pair.png')),clip=clip);names.append(name+'-pair')
   if name=='controls':
    for kind in ['Primary','Secondary','Tertiary','Keypad']:
     suffix='-key-1' if kind=='Keypad' else ''
     controls=[page.locator(f'[data-testid="study-{kind}-{state}{suffix}"]').bounding_box() for state in ['Default','Focus','Pressed','Disabled']]
     assert all(c and c['height']>=58*unit and c['y']+c['height']<=height*.96 for c in controls), (kind, controls)
     left=min(c['x'] for c in controls);top=min(c['y'] for c in controls);right=max(c['x']+c['width'] for c in controls);bottom=max(c['y']+c['height'] for c in controls)
     page.screenshot(path=str(folder/(kind.lower()+'-states.png')),clip={'x':left-8*unit,'y':top-8*unit,'width':right-left+16*unit,'height':bottom-top+16*unit});names.append(kind.lower()+'-states')
  (folder/'bounds.json').write_text(json.dumps(bounds,indent=2)+'\n')
  (folder/'index.html').write_text('<!doctype html><meta name="viewport" content="width=device-width"><style>body{background:#102f3a;color:#f3e8d3;font:18px sans-serif}img{max-width:100%}a{color:#e6a957}</style><h1>Control depth study</h1><p>Actual opt-in React Native components, browser approximation. No native validation or live browser app.</p>'+''.join(f'<h2>{name}</h2><a href="{name}.png"><img src="{name}.png"></a>' for name in names))
  page.close()
 browser.close()
print(OUT)
