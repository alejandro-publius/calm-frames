# Calm Frames mark: a calm monk inside a rounded "frame", with an aura of plain concentric lines.
TEAL="#1F4D5C"; CREAM="#F3E8D3"; SAFF="#E6A957"; SAFFD="#B87A2C"; INK="#17323C"

# The app's UI font. Vega draws React Native text in Amazon Ember, and
# src/components/rotator/AutoRotator.tsx names it outright, so the wordmark asks
# for it first. Ember is Amazon's and is not on this machine, so the PNG checked
# in beside this script is rendered in the first fallback that is. Anything with
# Ember installed, including the device, gets the real thing from the SVG.
UI_FONT = "Amazon Ember, Amazon Ember Display, Helvetica Neue, Arial, sans-serif"

def aura(cx, cy, radii, stroke=9, opacity=0.30, color=CREAM):
    return "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-opacity="{opacity}" stroke-width="{stroke}"/>' for r in radii)

def face(cx, cy, r, ink=INK, smile=True):
    ex=r*0.36; ey=cy-r*0.02; w=r*0.30; sw=max(6,r*0.085)
    s=f'<path d="M{cx-ex-w/2} {ey} q{w/2} {r*0.12} {w} 0" fill="none" stroke="{ink}" stroke-width="{sw}" stroke-linecap="round"/>'
    s+=f'<path d="M{cx+ex-w/2} {ey} q{w/2} {r*0.12} {w} 0" fill="none" stroke="{ink}" stroke-width="{sw}" stroke-linecap="round"/>'
    if smile:
        s+=f'<path d="M{cx-r*0.17} {cy+r*0.40} q{r*0.17} {r*0.13} {r*0.34} 0" fill="none" stroke="{ink}" stroke-width="{sw*0.85}" stroke-linecap="round"/>'
    return s

def bust(cx, head_cy, hr, bottom=1100):
    top=head_cy+hr*1.02
    body=f'M{cx-hr*1.75} {bottom} C{cx-hr*1.75} {top+hr*0.85}, {cx-hr*0.95} {top}, {cx} {top} C{cx+hr*0.95} {top}, {cx+hr*1.75} {top+hr*0.85}, {cx+hr*1.75} {bottom} Z'
    s=f'<clipPath id="bodyclip"><path d="{body}"/></clipPath>'
    s+=f'<path d="{body}" fill="{SAFF}"/>'
    s+=f'<path clip-path="url(#bodyclip)" d="M{cx-hr*0.55} {top+hr*0.02} C{cx-hr*0.1} {top+hr*0.7}, {cx+hr*0.9} {top+hr*1.2}, {cx+hr*1.75} {top+hr*1.9}" fill="none" stroke="{SAFFD}" stroke-width="{hr*0.10}" stroke-linecap="round"/>'
    s+=f'<circle cx="{cx}" cy="{head_cy}" r="{hr}" fill="{CREAM}"/>'
    s+=face(cx, head_cy, hr)
    return s

def frame(inner, bg=TEAL, size=1024, radius=210):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">'
            f'<defs><clipPath id="fr"><rect width="{size}" height="{size}" rx="{radius}"/></clipPath></defs>'
            f'<rect width="{size}" height="{size}" rx="{radius}" fill="{bg}"/>'
            f'<g clip-path="url(#fr)">{inner}</g></svg>')

B = frame(aura(512, 470, [260, 340, 420, 500]) + bust(512, 470, 172))

def head_only():
    cx=512; cy=500; hr=200
    s=aura(cx, cy, [285, 370, 455], stroke=14, opacity=0.34)
    s+=f'<path d="M180 1100 C180 900, 330 790, 512 790 C694 790, 844 900, 844 1100 Z" fill="{SAFF}"/>'
    s+=f'<circle cx="{cx}" cy="{cy}" r="{hr}" fill="{CREAM}"/>'+face(cx, cy, hr)
    return s
C = frame(head_only())

def tile():
    inner = aura(300, 330, [170, 225, 280], stroke=8) + bust(300, 330, 118, bottom=800)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">'
            f'<rect width="1280" height="720" fill="{TEAL}"/>'
            f'<g>{inner}</g>'
            f'<text x="620" y="330" font-family="{UI_FONT}" font-weight="bold" font-size="112" fill="{CREAM}">Calm</text>'
            f'<text x="620" y="450" font-family="{UI_FONT}" font-weight="bold" font-size="112" fill="{CREAM}">Frames</text>'
            f'<text x="624" y="520" font-family="{UI_FONT}" font-size="34" fill="{CREAM}" fill-opacity="0.75">Flash-safe movies for kids</text>'
            f'</svg>')
T = tile()

for name, svg in [("calm-frames-mark-bust.svg", B), ("calm-frames-mark-head.svg", C), ("calm-frames-tile-1280x720.svg", T)]:
    open(name, "w").write(svg)
print("written")
