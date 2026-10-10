# Calm Frames mark: a peaceful monk and one open halo inside a rounded frame.
TEAL="#1F4D5C"; CREAM="#F3E8D3"; SAFF="#E6A957"; SAFFD="#B87A2C"; INK="#17323C"

# The app's UI font. Vega draws React Native text in Amazon Ember, and
# src/components/rotator/AutoRotator.tsx names it outright, so the wordmark asks
# for it first. Ember is Amazon's and is not on this machine, so the PNG checked
# in beside this script is rendered in the first fallback that is. Anything with
# Ember installed, including the device, gets the real thing from the SVG.
UI_FONT = "Amazon Ember, Amazon Ember Display, Helvetica Neue, Arial, sans-serif"

def halo(cx, cy, radius, stroke=18):
    # An open lower arc leaves breathing room around the robe. One line keeps
    # the silhouette legible at small sizes without a repeated ring pattern.
    from math import cos, sin, radians
    left = (cx + radius * cos(radians(140)), cy + radius * sin(radians(140)))
    right = (cx + radius * cos(radians(40)), cy + radius * sin(radians(40)))
    return (f'<path d="M{left[0]} {left[1]} A{radius} {radius} 0 1 1 {right[0]} {right[1]}" '
            f'fill="none" stroke="{CREAM}" stroke-width="{stroke}" stroke-linecap="round"/>')

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
    s=f'<path d="{body}" fill="{SAFF}"/>'
    s+=f'<path d="M{cx-hr*0.45} {top+hr*0.18} C{cx-hr*0.1} {top+hr*0.7}, {cx+hr*0.75} {bottom-hr*0.65}, {cx+hr*1.30} {bottom-hr*0.25}" fill="none" stroke="{SAFFD}" stroke-width="{hr*0.10}" stroke-linecap="round"/>'
    s+=f'<circle cx="{cx}" cy="{head_cy}" r="{hr}" fill="{CREAM}"/>'
    s+=face(cx, head_cy, hr)
    return s

def frame(inner, bg=TEAL, size=1024, radius=210):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">'
            f'<defs><clipPath id="fr"><rect width="{size}" height="{size}" rx="{radius}"/></clipPath></defs>'
            f'<rect width="{size}" height="{size}" rx="{radius}" fill="{bg}"/>'
            f'<g clip-path="url(#fr)">{inner}</g></svg>')

B = frame(halo(512, 435, 310) + bust(512, 435, 172, bottom=920))

def head_only():
    cx=512; cy=500; hr=200
    s=halo(cx, cy, 340, stroke=24)
    s+=f'<path d="M240 920 C240 820, 350 790, 512 790 C674 790, 784 820, 784 920 Z" fill="{SAFF}"/>'
    s+=f'<circle cx="{cx}" cy="{cy}" r="{hr}" fill="{CREAM}"/>'+face(cx, cy, hr)
    return s
C = frame(head_only())

def tile():
    inner = halo(350, 305, 168, stroke=11) + bust(350, 305, 100, bottom=585)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">'
            f'<rect width="1280" height="720" fill="{TEAL}"/>'
            f'<g>{inner}</g>'
            f'<text x="590" y="310" font-family="{UI_FONT}" font-weight="bold" font-size="100" fill="{CREAM}">Calm</text>'
            f'<text x="590" y="420" font-family="{UI_FONT}" font-weight="bold" font-size="100" fill="{CREAM}">Frames</text>'
            f'<text x="594" y="490" font-family="{UI_FONT}" font-size="32" fill="{CREAM}">A calmer way to watch</text>'
            f'</svg>')
T = tile()

for name, svg in [("calm-frames-mark-bust.svg", B), ("calm-frames-mark-head.svg", C), ("calm-frames-tile-1280x720.svg", T)]:
    open(name, "w").write(svg)
print("written")
