"""Measure every background pixel behind the home parental-control label (Pillow)."""
import json
from pathlib import Path
from PIL import Image

OUT = Path(__file__).resolve().parents[2] / 'results/whole-flow-2026-10-14/checks'

def luminance(rgb):
    channels = [v / 255 for v in rgb[:3]]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
    return sum(v * weight for v, weight in zip(linear, [.2126, .7152, .0722]))

def contrast(a, b):
    low, high = sorted([luminance(a), luminance(b)])
    return (high + .05) / (low + .05)

result = {}
for path in sorted(OUT.glob('parent-label-background-*.png')):
    picture = Image.open(path).convert('RGB')
    pixels = list(picture.getdata())
    minimum = min(contrast((243, 232, 211), pixel) for pixel in pixels)
    result[path.name] = {'minimumTextContrast': minimum, 'pixelsSampled': len(pixels), 'passes4_5': minimum >= 4.5}
    assert minimum >= 4.5
assert len(result) == 4
result['focusRingOnFill'] = contrast((230, 169, 87), (35, 75, 85))
assert result['focusRingOnFill'] >= 3
(OUT / 'home-refinement-contrast.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
