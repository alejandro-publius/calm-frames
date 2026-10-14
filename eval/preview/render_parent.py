"""Inspect parent screens exported with in-memory fixtures; not a native capture."""
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
            folder = ROOT / f"docs/design/parent-refinement/{args.stage}/{height}"
            folder.mkdir(parents=True, exist_ok=True)
            trees = sorted((host.ROOT / f"app/build/parent-preview/{args.stage}/{height}").glob("*.json"))
            assert len(trees) == 9, trees
            for tree_file in trees:
                tree = json.loads(tree_file.read_text())
                page.set_content(f'''<!doctype html><html><head><meta charset="utf-8"><title>{tree_file.stem}: browser approximation, not Vega</title><style>
{fonts}
*{{box-sizing:border-box}}html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden;background:#102F3A}}
body{{display:flex;font-family:InterRegular}}.view{{display:flex;flex-direction:column;flex-shrink:0;position:relative;min-width:0;border-style:solid;border-width:0}}
.text{{display:block;position:relative;flex-shrink:0;white-space:pre-wrap;border-style:solid;border-width:0}}img{{display:block;flex-shrink:0}}.scroll{{overflow:auto;scrollbar-width:none}}
</style></head><body>{host.render(tree)}</body></html>''')
                page.evaluate("document.fonts.ready")
                def capture(suffix, *, page=page, folder=folder, height=height, name=tree_file.stem):
                    rows = page.locator('[data-testid]').evaluate_all("els => els.filter(e=>e.dataset.testid).map(e=>({id:e.dataset.testid,text:e.innerText?.slice(0,160),x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height}))")
                    rows = [r for r in rows if r["id"] not in ("parent-area", "parent-area-open") and r["y"] < height and r["y"] + r["height"] > 0]
                    bounds[f"{height}/{name}{suffix}"] = rows
                    page.screenshot(path=str(folder / f"{name}{suffix}.png"))
                capture("")
                if args.stage == "after" and tree_file.stem in ("household", "child", "saving", "no-profiles"):
                    selected = {row["id"]: row for row in bounds[f"{height}/{tree_file.stem}"]}
                    for identity in ("parent-area-back-top", "parent-area-preset-wcag", "parent-area-preset-broadcast"):
                        row = selected[identity]
                        assert row["y"] >= height * .05 - 1 and row["y"] + row["height"] <= height * .95 + 1, row
                    row = selected["parent-area-preset-wcag"]
                    assert abs(row["x"] + row["width"] / 2 - width / 2) <= 1, row
                if args.stage == "after" and tree_file.stem == "full-household":
                    row = next(r for r in bounds[f"{height}/{tree_file.stem}"] if r["id"] == "parent-area-profiles-full")
                    assert row["x"] + row["width"] <= width * .95 + 1, row
                    assert row["y"] + row["height"] <= height * .95 + 1, row
                if tree_file.stem == "remove-confirm":
                    page.evaluate("""inset => {
                        const scroll = document.querySelector('.scroll');
                        const target = document.querySelector('[data-testid="parent-area-remove-question"]');
                        scroll.scrollTop += target.getBoundingClientRect().top - inset;
                    }""", height * .05)
                    capture("-question")
                if tree_file.stem in ("household", "child", "no-profiles"):
                    targets = {"room": "parent-area-room", "interface": "parent-area-interface-motion", "history": "parent-area-total"}
                    for section, identity in targets.items():
                        if page.locator(f'[data-testid="{identity}"]').count():
                            page.evaluate("""({identity, inset}) => {
                              const scroll = document.querySelector('.scroll');
                              const target = document.querySelector(`[data-testid="${identity}"]`).parentElement;
                              scroll.scrollTop += target.getBoundingClientRect().top - inset;
                            }""", {"identity": identity, "inset": height * .05})
                            capture("-" + section)
                    page.evaluate("document.querySelector('.scroll').scrollTop = document.querySelector('.scroll').scrollHeight")
                    capture("-bottom")
            page.close()
        browser.close()
    (ROOT / f"docs/design/parent-refinement/{args.stage}/bounds.json").write_text(json.dumps(bounds, indent=2) + "\n")


if __name__ == "__main__":
    main()
