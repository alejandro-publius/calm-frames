"""Render unavailable host trees at their exported size; this is not a native capture."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

import render_harbor as host

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("before", "after"), required=True)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    host.ROOT = args.source_root.resolve()
    fonts = "".join(f"@font-face{{font-family:{name};src:url({host.data(host.ROOT / 'app/assets/fonts' / (name + '.ttf'))})}}" for name in ("InterRegular", "InterMedium", "InterSemiBold"))
    bounds = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        for height in (1080, 720):
            width = height * 16 // 9
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            folder = ROOT / f"docs/design/unavailable-refinement/{args.stage}/{height}"
            folder.mkdir(parents=True, exist_ok=True)
            trees = sorted((host.ROOT / f"app/build/unavailable-preview/{args.stage}/{height}").glob("*.json"))
            assert len(trees) == 11, trees
            for tree_file in trees:
                tree = json.loads(tree_file.read_text())
                content = f'''<!doctype html><html><head><meta charset="utf-8"><title>{tree_file.stem}: browser approximation, not Vega</title><style>
{fonts}
*{{box-sizing:border-box}}html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden;background:#102F3A}}
body{{display:flex;font-family:InterRegular}}.view{{display:flex;flex-direction:column;flex-shrink:0;position:relative;min-width:0;border-style:solid;border-width:0}}
.text{{display:block;position:relative;flex-shrink:0;white-space:pre-wrap;border-style:solid;border-width:0}}img{{display:block;flex-shrink:0}}.scroll{{overflow:auto;scrollbar-width:none}}
</style></head><body>{host.render(tree)}</body></html>'''
                page.set_content(content)
                page.evaluate("document.fonts.ready")
                rows = page.locator('[data-testid]').evaluate_all("els => els.filter(e=>e.dataset.testid).map(e=>({id:e.dataset.testid,text:e.innerText,x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height}))")
                bounds[f"{height}/{tree_file.stem}"] = rows
                if args.stage == "after":
                    selected = {row["id"]: row for row in rows}
                    title, notice, back = (selected[f"title-details-{suffix}"] for suffix in ("title", "notice", "back"))
                    for row in (title, notice, back):
                        assert row["x"] >= width * .05 - 1 and row["x"] + row["width"] <= width * .95 + 1, row
                        assert row["y"] >= height * .05 - 1 and row["y"] + row["height"] <= height * .95 + 1, row
                    assert title["y"] + title["height"] < notice["y"], selected
                    assert notice["y"] + notice["height"] < back["y"], selected
                    assert abs(back["x"] + back["width"] / 2 - width / 2) <= 1, back
                    assert "title-details-play" not in selected
                page.screenshot(path=str(folder / f"{tree_file.stem}.png"))
            page.close()
        browser.close()
    (ROOT / f"docs/design/unavailable-refinement/{args.stage}/bounds.json").write_text(json.dumps(bounds, indent=2) + "\n")


if __name__ == "__main__":
    main()
