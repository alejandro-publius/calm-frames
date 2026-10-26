"""Draw the name editor's exported host trees in Chromium, at 1080p and 720p.

A browser approximation of React Native host trees, using the app's own
fonts and styles. It is not a Vega capture: browser layout differs from Yoga,
and 720p is the 1080p tree drawn at two thirds, where the device rounds each
unit on its own. Run the sibling fixture first; see its header.

    CALM_CHROMIUM=/path/to/chromium uv run --with playwright \\
      python docs/design-polish-2026-10-23/fable-profile-names/preview/render_preview.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "eval/preview"))
import render_harbor as host  # noqa: E402

host.ROOT = ROOT
TREES = ROOT / "app/build/profile-names-preview/1080"
FONTS = ("CalmSansRegular", "CalmSansSemibold", "CalmDisplaySemibold", "InterRegular", "InterMedium", "InterSemiBold")
SAFE = 0.05
WATCHED = (
    "parent-area-back-top", "parent-area-rename-profile", "parent-area-name-field", "parent-area-name-problem",
    "parent-area-name-key-a", "parent-area-name-key-j", "parent-area-name-key-u", "parent-area-name-key-delete",
    "parent-area-name-save", "parent-area-name-cancel", "parent-area-name-retry", "parent-area-name-failed",
)


def main() -> int:
    fonts = "".join(
        f"@font-face{{font-family:{name};src:url({host.data(ROOT / 'app/assets/fonts' / (name + '.ttf'))})}}"
        for name in FONTS
    )
    trees = sorted(TREES.glob("*.json"))
    if not trees:
        print(f"no trees in {TREES}; run the fixture first", file=sys.stderr)
        return 2
    report: dict = {"note": "Browser approximation of exported React Native host trees. Not a Vega capture.", "states": {}}
    launch = {"executable_path": os.environ["CALM_CHROMIUM"]} if os.environ.get("CALM_CHROMIUM") else {}
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch)
        for height in (1080, 720):
            width = height * 16 // 9
            zoom = height / 1080
            folder = HERE / str(height)
            folder.mkdir(parents=True, exist_ok=True)
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            page.route("http**/*", lambda route: route.abort())
            for tree_file in trees:
                tree = json.loads(tree_file.read_text())
                page.set_content(
                    f"<!doctype html><html><head><meta charset='utf-8'>"
                    f"<title>{tree_file.stem}: browser approximation, not Vega</title><style>{fonts}"
                    f"*{{box-sizing:border-box}}html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden;background:#F7EACF}}"
                    f"body{{display:flex;font-family:CalmSansRegular}}.zoom{{zoom:{zoom};display:flex;width:1920px;height:1080px}}"
                    f".view{{display:flex;flex-direction:column;flex-shrink:0;position:relative;min-width:0;border-style:solid;border-width:0}}"
                    f".text{{display:block;position:relative;flex-shrink:0;white-space:pre-wrap;border-style:solid;border-width:0}}"
                    f"img{{display:block;flex-shrink:0}}.scroll{{overflow:auto;scrollbar-width:none}}"
                    f"</style></head><body><div class='zoom'>{host.render(tree)}</div></body></html>"
                )
                page.evaluate("document.fonts.ready")

                def rows(page=page):
                    found = page.locator("[data-testid]").evaluate_all(
                        "els => els.filter(e => e.dataset.testid).map(e => { const r = e.getBoundingClientRect(); "
                        "return {id: e.dataset.testid, x: r.x, y: r.y, width: r.width, height: r.height}; })"
                    )
                    return {row["id"]: row for row in found if row["id"] in WATCHED}

                first = rows()
                page.screenshot(path=str(folder / f"{tree_file.stem}.png"))
                state = {"viewport": [width, height], "first_viewport": first, "checks": {}}
                inside_x = all(
                    row["x"] >= width * SAFE - 1 and row["x"] + row["width"] <= width * (1 - SAFE) + 1
                    for row in first.values()
                )
                state["checks"]["watched_controls_inside_horizontal_safe_area"] = inside_x
                actions = [first.get("parent-area-name-save") or first.get("parent-area-name-retry")]
                actions = [row for row in actions if row]
                # Null where the state has no Save or Try again to place.
                state["checks"]["save_or_retry_in_first_viewport"] = (
                    all(row["y"] >= 0 and row["y"] + row["height"] <= height * (1 - SAFE) + 1 for row in actions)
                    if actions
                    else None
                )
                if "editor" in tree_file.stem:
                    page.evaluate(
                        """inset => {
                          const scroll = document.querySelector('.scroll');
                          const target = document.querySelector('[data-testid="parent-area-name"]');
                          if (scroll && target) scroll.scrollTop += target.getBoundingClientRect().top / (inset.zoom) - inset.pad;
                        }""",
                        {"zoom": zoom, "pad": 1080 * SAFE},
                    )
                    page.screenshot(path=str(folder / f"{tree_file.stem}-scrolled.png"))
                    state["scrolled_to_editor"] = rows()
                report["states"][f"{height}/{tree_file.stem}"] = state
            page.close()
        browser.close()
    (HERE / "bounds.json").write_text(json.dumps(report, indent=2) + "\n")
    for name, state in report["states"].items():
        print(name, json.dumps(state["checks"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
