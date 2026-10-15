"""Review real React Native host trees. Media, captions and seekbar are labelled substitutes."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

import render_harbor as host

ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--browser',required=True);parser.add_argument('--output',default='results/whole-flow-2026-10-14');parser.add_argument('--height',type=int,default=1080,choices=(1080,720));args=parser.parse_args()
HEIGHT=args.height;WIDTH=HEIGHT*16//9
OUT=ROOT/args.output/str(HEIGHT)
OUT.mkdir(parents=True,exist_ok=True)
host.ROOT=ROOT
# Deliberately long two-line fixture cue: checks competing layers, not native caption layout.
original_render=host.render
def render(node):
 if isinstance(node,dict):
  props=node.get('props',{});kind=node['type'];css=host.style(props.get('style'))
  if kind=='PreviewMaterialIcon':
   glyphs=json.loads((ROOT/'app/node_modules/@amazon-devices/react-native-vector-icons/glyphmaps/MaterialIcons.json').read_text())
   return f'<span style="font-family:MaterialIcons;font-size:{props["size"]}px;color:{props["color"]}">&#{glyphs[props["name"]]};</span>'
  if kind=='PreviewVideoSurface':
   return f'<img style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;{css}" src="{host.data(ROOT/"app/assets/image/tv/harbor-cinematic.png")}">'
  if kind=='Image' and props.get('source',{}).get('uri','').startswith('data:image/'):
   return f'<img style="{css};width:100%;height:100%;object-fit:contain" src="{props["source"]["uri"]}">'
  if kind=='PreviewNativeSeekBar':
   return '<div style="height:12px;background:#667777;border-radius:6px"><div style="width:30%;height:100%;background:#f4ecdd"></div></div>'
 if isinstance(node,dict) and node['type']=='PreviewNativeCaptions':
  props=node.get('props',{})
  if not props.get('show'): return ''
  css=host.style(props.get('style'))
  return f'<div data-testid="multiline-caption-substitute" style="{css};display:flex;align-items:center;justify-content:flex-end;flex-direction:column"><span data-testid="multiline-cue-substitute" style="font:{32*HEIGHT/1080}px CalmSansRegular;line-height:{42*HEIGHT/1080}px;color:#f4ecdd;background:black;padding:8px 16px;text-align:center">A small boat rests beside the lighthouse.<br>The evening light moves softly across the water.</span></div>'
 return original_render(node)
host.render=render
fonts=''.join(f'@font-face{{font-family:{n};src:url({host.data(ROOT / "app/assets/fonts" / (n+".ttf"))})}}' for n in ('CalmSansRegular','CalmSansSemibold','CalmDisplaySemibold'))
fonts+=f'@font-face{{font-family:MaterialIcons;src:url({host.data(ROOT/"app/node_modules/@amazon-devices/react-native-vector-icons/Fonts/MaterialIcons.ttf")})}}'
inputs=[]
for directory,prefix in [('home-preview','01'),('design-preview/after','02'),('playback-preview/after/1080','03'),('parent-preview/after/1080','04'),('utility-preview','05'),('unavailable-preview/after/1080','06')]:
 if HEIGHT==720:
  directory = directory.replace('/1080','/720') if '/1080' in directory else directory+'/720'
 for file in sorted((ROOT/'app/build'/directory).glob('*.json')):
  if file.stem=='library' or file.stem.endswith('-info'):continue
  inputs.append((prefix+'-'+file.stem,file))
bounds={};captures=[]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path=args.browser)
 page=browser.new_page(viewport={'width':WIDTH,'height':HEIGHT},device_scale_factor=1)
 for name,file in inputs:
  tree=json.loads(file.read_text())
  html=f'''<!doctype html><html><head><title>{name}: browser approximation</title><style>{fonts}
*{{box-sizing:border-box}}html,body{{margin:0;width:{WIDTH}px;height:{HEIGHT}px;background:#151c26}}body{{display:flex;flex-direction:column;overflow:hidden}}
.view{{display:flex;flex-direction:column;position:relative;flex-shrink:0;min-height:0;min-width:0;border-style:solid;border-width:0}}
.text{{display:block;position:relative;flex-shrink:0;white-space:pre-wrap;border-style:solid;border-width:0}}img{{display:block;flex-shrink:0}}.scroll{{overflow:auto;scrollbar-width:none}}
</style></head><body>{render(tree)}</body></html>'''
  page.set_content(html);page.evaluate('document.fonts.ready')
  page.screenshot(path=str(OUT/(name+'.png')));captures.append(name)
  bounds[name]=page.locator('[data-testid]').evaluate_all('els => els.filter(e=>e.dataset.testid).map(e=>{const r=e.getBoundingClientRect();return {id:e.dataset.testid,x:r.x,y:r.y,width:r.width,height:r.height}})')
  if name in ('03-hold-caption-menu','03-hold-controls'):
   cue=page.locator('[data-testid="multiline-cue-substitute"]').bounding_box()
   card=page.locator('[data-testid="calm-card"]').bounding_box()
   controls=page.locator('[data-testid="control-bar"]').bounding_box()
   assert cue and card and controls
   assert card['y']+card['height'] < cue['y'], (name,card,cue)
   assert cue['y']+cue['height'] < controls['y'], (name,cue,controls)
   if name.endswith('caption-menu'):
    menu=page.get_by_text('Captions',exact=True).locator('..').bounding_box()
    assert menu and menu['y']+menu['height'] <= cue['y'], (name,menu,cue)
  safe_targets={'01-how-it-works':'picture-hold-playback-check','05-setup-pin':'first-run-key-delete','04-locked':'parent-area-key-delete'}
  if name in safe_targets:
   control=page.locator('[data-testid="'+safe_targets[name]+'"]').bounding_box()
   assert control and control['y']+control['height'] <= HEIGHT*.95+1, (name,control,HEIGHT)
  scroll=page.locator('.scroll').first
  if scroll.count():
   size=scroll.evaluate('e=>({height:e.clientHeight,total:e.scrollHeight})')
   for i,y in enumerate(range(HEIGHT*5//6,size['total']-size['height']+HEIGHT*5//6,HEIGHT*5//6),1):
    scroll.evaluate('(e,y)=>e.scrollTop=y',y)
    shot=name+f'-scroll-{i:02d}'
    page.screenshot(path=str(OUT/(shot+'.png')));captures.append(shot)
 # Contact sheets are browser layout, with full-size PNG links in the review index.
 for chunk in range(0,len(captures),16):
  subset=captures[chunk:chunk+16]
  page.set_viewport_size({'width':1280,'height':400*((len(subset)+1)//2)})
  page.set_content('<style>body{margin:0;background:#151c26;color:#f4ecdd;font:20px sans-serif;display:grid;grid-template-columns:640px 640px}figure{margin:0;height:400px}img{width:640px;height:360px}figcaption{padding:10px}</style>'+''.join(f'<figure><img src="{host.data(OUT/(n+".png"))}"><figcaption>{n}</figcaption></figure>' for n in subset))
  page.screenshot(path=str(OUT/f'contact-sheet-{chunk//16+1:02d}.png'))
 browser.close()
(OUT/'bounds.json').write_text(json.dumps(bounds,indent=2)+'\n')
(OUT/'index.html').write_text('<!doctype html><title>Calm Frames full flow browser review</title><style>body{background:#151c26;color:#f4ecdd;font:20px sans-serif}img{width:100%;max-width:1920px}figure{margin:40px 0}</style><h1>Full flow: browser approximation</h1><p>Actual component host trees. Video, native captions and native seekbar are substitutes. No native input or VoiceView pass is implied.</p>'+''.join(f'<figure><figcaption>{n}</figcaption><a href="{n}.png"><img src="{n}.png"></a></figure>' for n in captures))
print(f'{len(inputs)} states; {len(captures)} captures; {OUT}')
