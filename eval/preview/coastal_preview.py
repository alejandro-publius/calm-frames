"""Export actual native component host trees as a local browser preview. No capture."""
import base64
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def flatten(value):
    if isinstance(value, list):
        result = {}
        for item in value:
            result.update(flatten(item))
        return result
    return value if isinstance(value, dict) else {}


def style(value):
    values = flatten(value).copy()
    for prefix in ("padding", "margin"):
        for direction, sides in (("Horizontal", ("Left", "Right")), ("Vertical", ("Top", "Bottom"))):
            key = prefix + direction
            if key in values:
                v = values.pop(key)
                for side in sides:
                    values.setdefault(prefix + side, v)
    if values.get("flex") == 1:
        values["flex"] = "1 1 0%"
        values["minHeight"] = 0
        values["minWidth"] = 0
    css = []
    unitless = {"flex", "flexGrow", "flexShrink", "opacity", "zIndex", "fontWeight", "order"}
    for key, value in values.items():
        if value is None or key in {"elevation", "shadowOffset", "shadowColor", "shadowRadius", "shadowOpacity"}:
            continue
        if key == "transform":
            value = " ".join(f"{k}({v}{'px' if k.startswith('translate') else ''})" for t in value for k, v in t.items())
        elif isinstance(value, (int, float)) and key not in unitless:
            value = f"{value}px"
        css.append(re.sub(r"[A-Z]", lambda m: "-" + m[0].lower(), key) + ":" + str(value))
    return ";".join(css)


def data(path):
    mime = "font/ttf" if path.suffix == ".ttf" else "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def render(node):
    if node is None:
        return ""
    if isinstance(node, list):
        return "".join(render(item) for item in node)
    if isinstance(node, str):
        return html.escape(node)
    kind, props = node["type"], node.get("props", {})
    css = style(props.get("style"))
    identity = html.escape(props.get("testID", ""), quote=True)
    if kind == "Image":
        source = props.get("source", {})
        if isinstance(source, list):
            source = source[0]
        uri = source.get("testUri", "")
        if "assets/" not in uri:
            raise ValueError(f"Unresolved preview image: {source}")
        path = ROOT / "app/assets" / uri.split("assets/", 1)[1]
        fit = "cover" if props.get("resizeMode") == "cover" else "contain"
        return f'<img data-testid="{identity}" style="{css};object-fit:{fit}" src="{data(path)}">'
    if kind == "LinearGradient":
        start, end = props.get("start", {"x": 0, "y": 0}), props.get("end", {"x": 0, "y": 1})
        if start["x"] == end["x"]:
            direction = "to bottom" if end["y"] > start["y"] else "to top"
        elif start["y"] == end["y"]:
            direction = "to right" if end["x"] > start["x"] else "to left"
        else:
            raise ValueError("Diagonal gradients need a separate browser approximation.")
        colors = props["colors"]
        if props.get("locations"):
            colors = [f"{color} {stop * 100}%" for color, stop in zip(colors, props["locations"])]
        css += f';background:linear-gradient({direction},{",".join(colors)})'
    tag = "span" if kind == "Text" else "div"
    role = ' role="button" tabindex="0"' if props.get("accessibilityRole") == "button" else ""
    cls = "text" if kind == "Text" else "view"
    if kind in {"ScrollView", "RCTScrollView"}:
        cls += " scroll"
        child_nodes = node.get("children", [])
        if len(child_nodes) == 1 and isinstance(child_nodes[0], dict):
            child_nodes = [{**child_nodes[0], "props": {**child_nodes[0].get("props", {}), "style": props.get("contentContainerStyle", {})}}]
        children = render(child_nodes)
    else:
        children = render(node.get("children"))
    return f'<{tag} class="{cls}"{role} data-testid="{identity}" style="{css}">{children}</{tag}>'


def main():
    out = ROOT / 'build/coastal-preview'
    out.mkdir(parents=True, exist_ok=True)
    fonts = ''.join(f'@font-face{{font-family:{name};src:url({data(ROOT / "app/assets/fonts" / (name + ".ttf"))})}}' for name in ('CalmSansRegular', 'CalmSansSemibold', 'CalmDisplaySemibold'))
    css = """*{box-sizing:border-box}html,body{margin:0;background:#f5ebdd;color:#193234;font-family:CalmSansRegular,sans-serif}body{overflow:hidden}.stage{position:absolute;width:1920px;height:1080px;display:flex;flex-direction:column;transform-origin:top left}.view{display:flex;flex-direction:column;position:relative;flex-shrink:0;min-height:0;min-width:0;border-style:solid;border-width:0}.text{display:block;position:relative;flex-shrink:0;white-space:pre-wrap;border-style:solid;border-width:0}img{display:block;flex-shrink:0}.scroll{overflow:auto;scrollbar-width:none}[role=button]{cursor:pointer}[role=button]:focus-visible{outline:6px solid #193b3c;outline-offset:2px}[data-testid=kid-home-watch]:focus-visible,[data-testid=title-details-play]:focus-visible{outline-color:#c16c45}[role=button]:focus-visible .text{text-decoration:underline}.badge{position:fixed;bottom:4px;right:8px;font:12px sans-serif;background:#f5ebdd;padding:4px 8px;border-radius:8px}#note{position:fixed;bottom:32px;left:50%;transform:translateX(-50%);background:#193234;color:#f5ebdd;padding:14px 22px;border-radius:12px;font:16px sans-serif;display:none}"""
    js = """const stage=document.querySelector('.stage');function fit(){let s=Math.min(innerWidth/1920,innerHeight/1080);stage.style.transform=`scale(${s})`;stage.style.left=((innerWidth-1920*s)/2)+'px';stage.style.top=((innerHeight-1080*s)/2)+'px'}addEventListener('resize',fit);fit();document.querySelectorAll('[role=button]').forEach(el=>{el.addEventListener('click',()=>{const routes={'kid-home-more-info':'details.html','kid-home-demo':'practice.html','kid-home-learn':'help.html','kid-home-parent-area':'settings.html','picture-hold-demo-details':'practice.html'};const id=el.dataset.testid;if(routes[id]){location.href=routes[id];return}if(id?.includes('back')||id==='picture-hold-dismiss'){location.href='index.html';return}if(id==='title-details-show-info'){document.querySelector('[data-testid=title-details-info]')?.scrollIntoView({block:'start'});return}const n=document.querySelector('#note');n.textContent='Component preview: native app actions run on the Vega device.';n.style.display='block';setTimeout(()=>n.style.display='none',2600)});el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();el.click()}})});document.addEventListener('keydown',e=>{if(['ArrowRight','ArrowDown','ArrowLeft','ArrowUp'].includes(e.key)){e.preventDefault();const all=[...document.querySelectorAll('[role=button]')];let i=all.indexOf(document.activeElement);i=(i+(e.key==='ArrowLeft'||e.key==='ArrowUp'?-1:1)+all.length)%all.length;all[i]?.focus()}});"""
    for name in ('home', 'details', 'practice', 'help', 'settings'):
        tree = json.loads((ROOT / f'app/build/composition-preview/1080/{name}.json').read_text())
        filename = 'index.html' if name == 'home' else name + '.html'
        (out/filename).write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Calm Frames | Coastal component preview</title><style>'+fonts+css+'</style></head><body><main class="stage">'+render(tree)+'</main><div class="badge">Native component preview · Browser layout · No playback</div><div id="note" role="status"></div><script>'+js+'</script></body></html>')
    print(out / 'index.html')

if __name__ == '__main__':
    main()
