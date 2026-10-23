"""Render exported React Native host trees in Chromium, explicitly not Vega.

Run the sibling fixture in app/test/calmframes, then run this script. The output
uses the actual styles, text and images. Browser layout still differs from Yoga.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/design/detail-refinement"


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
    cls = "text" if kind == "Text" else "view"
    if kind in {"ScrollView", "RCTScrollView"}:
        cls += " scroll"
        child_nodes = node.get("children", [])
        if len(child_nodes) == 1 and isinstance(child_nodes[0], dict):
            child_nodes = [{**child_nodes[0], "props": {**child_nodes[0].get("props", {}), "style": props.get("contentContainerStyle", {})}}]
        children = render(child_nodes)
    else:
        children = render(node.get("children"))
    return f'<{tag} class="{cls}" data-testid="{identity}" style="{css}">{children}</{tag}>'


def main():
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("before", "after"), required=True)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    ROOT = args.source_root.resolve()
    out = OUT / args.stage
    out.mkdir(parents=True, exist_ok=True)
    fonts = "".join(f"@font-face{{font-family:{name};src:url({data(ROOT / 'app/assets/fonts' / (name + '.ttf'))})}}" for name in ("InterRegular", "InterMedium", "InterSemiBold"))
    observations = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        for name in ("library", "details-harbor", "details-demo", "details-unavailable"):
            tree = json.loads((ROOT / f"app/build/design-preview/{args.stage}/{name}.json").read_text())
            content = f'''<!doctype html><html><head><meta charset="utf-8"><title>{name}: browser approximation, not Vega</title><style>
{fonts}
*{{box-sizing:border-box}}html,body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:#102F3A}}
body{{display:flex;font-family:InterRegular}}.view{{display:flex;flex-direction:column;flex-shrink:0;position:relative;min-width:0;border-style:solid;border-width:0}}
.text{{display:block;position:relative;flex-shrink:0;white-space:pre-wrap;border-style:solid;border-width:0}}img{{display:block;flex-shrink:0}}.scroll{{overflow:auto;scrollbar-width:none}}
</style></head><body>{render(tree)}</body></html>'''
            (ROOT / f"app/build/design-preview/{args.stage}/{name}.html").write_text(content)
            page.set_content(content)
            page.evaluate("document.fonts.ready")
            page.screenshot(path=str(out / f"{name}-browser.png"))
            observations[name] = page.locator("[data-testid]").evaluate_all("els => els.filter(e=>e.dataset.testid).map(e=>({id:e.dataset.testid,text:e.innerText?.slice(0,120),x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height}))")
            if args.stage == "after" and name in {"details-harbor", "details-demo"}:
                button = next(row for row in observations[name] if row["id"] == "title-details-show-info")
                assert abs(button["x"] + button["width"] / 2 - 960) < 1, button
                assert button["y"] >= 54 and button["y"] + button["height"] <= 1026, button
            if name in {"details-harbor", "details-demo"}:
                focused_tree = ROOT / f"app/build/design-preview/{args.stage}/{name}-info.json"
                if focused_tree.exists():
                    focused_content = content.replace(render(tree), render(json.loads(focused_tree.read_text())))
                    page.set_content(focused_content)
                    page.evaluate("document.fonts.ready")
                page.evaluate("""() => {
                  const scroll = document.querySelector('.scroll');
                  const target = document.querySelector('[data-testid="title-details-info"]') || document.querySelector('[data-testid="title-details-summary"]').parentElement.parentElement;
                  scroll.scrollTop += target.getBoundingClientRect().top - 54;
                }""")
                page.screenshot(path=str(out / f"{name}-plan-browser.png"))
                observations[name + "-scrolled"] = page.locator('[data-testid="title-details-show-info"]').evaluate_all("els => els.map(e=>({x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height}))")
                if args.stage == "after":
                    anchor = observations[name + "-scrolled"][0]
                    assert abs(anchor["y"] - 54) < 1, anchor
                    assert abs(anchor["x"] + anchor["width"] / 2 - 960) < 1, anchor
                page.evaluate("document.querySelector('.scroll').scrollTop = document.querySelector('.scroll').scrollHeight")
                page.screenshot(path=str(out / f"{name}-bottom-browser.png"))
        browser.close()
    (out / "bounds.json").write_text(json.dumps(observations, indent=2))


if __name__ == "__main__":
    main()
