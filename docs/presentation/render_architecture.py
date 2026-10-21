"""Render the README architecture as PNG and self-contained SVG. Requires Pillow."""
from pathlib import Path
from html import escape
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SCALE = 2
W, H = 1280, 870
im = Image.new('RGB', (W*SCALE, H*SCALE), '#f7f2e6')
d = ImageDraw.Draw(im)
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
       '<title id="title">Calm Frames: from licensed source to deliberate playback</title>',
       '<desc id="desc">Offline analysis, signed maps, rendering and verification produce an approved packaged library. The native app matches the catalog route, verifies the map, then drives guarded playback. The exact McWay edition ends on its final still until Back. Verification failure keeps the picture covered.</desc>']
INK, MUTED, TEAL, LINE = '#244f4b', '#53645b', '#dce9df', '#b9c8b6'

def rect(x,y,w,h,fill,stroke=None,r=0):
    d.rounded_rectangle((x*SCALE,y*SCALE,(x+w)*SCALE,(y+h)*SCALE),radius=r*SCALE,fill=fill,outline=stroke,width=2*SCALE)
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke or fill}" stroke-width="2"/>')

def text(x,y,value,size=22,color=INK,bold=False,display=False):
    name='CalmDisplaySemibold.ttf' if display else ('CalmSansSemibold.ttf' if bold else 'CalmSansRegular.ttf')
    font=ImageFont.truetype(str(ROOT/'app/assets/fonts'/name),size*SCALE)
    d.text((x*SCALE,y*SCALE),value,font=font,fill=color,anchor='lt')
    family='Georgia,serif' if display else 'Arial,sans-serif'
    svg.append(f'<text x="{x}" y="{y+size*.82}" font-family="{family}" font-size="{size}" font-weight="{600 if bold or display else 400}" fill="{color}">{escape(value)}</text>')

def arrow(points):
    q=[(x*SCALE,y*SCALE) for x,y in points]
    d.line(q,fill=INK,width=2*SCALE)
    x,y=points[-1]; px,py=points[-2]
    head=[(x,y),(x-8,y-5),(x-8,y+5)] if x>px else [(x,y),(x-5,y-8),(x+5,y-8)]
    d.polygon([(a*SCALE,b*SCALE) for a,b in head],fill=INK)
    svg.append('<polyline points="'+' '.join(f'{a},{b}' for a,b in points)+'" fill="none" stroke="'+INK+'" stroke-width="2"/>')
    svg.append('<polygon points="'+' '.join(f'{a},{b}' for a,b in head)+'" fill="'+INK+'"/>')

def card(x,y,w,kicker,title,lines):
    rect(x,y,w,164,'#fffaf0',LINE,15)
    text(x+22,y+19,kicker,16,MUTED,bold=True)
    text(x+22,y+49,title,27,INK,bold=True)
    for n,line in enumerate(lines): text(x+22,y+91+n*26,line,20,MUTED)

rect(0,0,W,H,'#f7f2e6')
text(48,34,'From source to a scene that stays',39,display=True)
text(48,88,'Calm Frames  /  preparation, trust and playback',22,MUTED)
text(48,152,'OFFLINE PREPARATION',17,INK,bold=True)
card(48,187,366,'01 / PROVENANCE','Licensed source',['Credit + source hash + timing','No automatic playback'])
card(457,187,366,'02 / ANALYSIS','Analyze + sign',['flashmap findings and maps','WCAG / broadcast profiles'])
card(866,187,366,'03 / PREPARATION','Render + verify',['Preset outputs + exact reports','Authenticated library export'])
arrow([(414,269),(457,269)]); arrow([(823,269),(866,269)])
arrow([(1049,351),(1049,385),(183,385),(183,450)])
text(48,417,'NATIVE VEGA APP',17,INK,bold=True)
card(48,450,270,'04 / BUILD BOUNDARY','Approved library',['Compiled catalog + hashes','Reports + budget checks'])
card(353,450,270,'05 / WATCH','Route + map checks',['Exact title and edition','Ed25519 verification'])
card(658,450,270,'06 / PLAYBACK','Guarded player',['Cover before seek','Pause / resume / Back'])
card(963,450,270,'07 / MCWAY END','Final frame holds',['Exact edition and still','No repeat or auto-exit'])
for a,b in [(318,353),(623,658),(928,963)]: arrow([(a,532),(b,532)])
rect(48,659,1184,73,TEAL,None,13)
text(70,680,'Unresolved verification keeps the picture covered. New media cannot grant itself trust.',24,INK,bold=True)
text(48,768,'Prepared catalog only. No interception of other apps or streaming services.',22,MUTED)
text(48,802,'Analyzer findings and signatures are technical evidence, not medical or comfort guarantees.',21,MUTED)
svg.append('</svg>')
im.resize((W,H),Image.Resampling.LANCZOS).save(OUT/'architecture.png',optimize=True)
(OUT/'architecture.svg').write_text('\n'.join(svg)+'\n')
