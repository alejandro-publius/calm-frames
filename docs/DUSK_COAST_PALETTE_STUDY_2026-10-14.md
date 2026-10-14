# Dusk coast — one alternate palette study

Review-only branch: `codex/dusk-coast-palette-study-2026-10-14`, based on integrated candidate `95f74118192d2e05636c3a7c9d6007abe83a5131`. Palette source commit: `e97e0daba5ab071e0d6db22fd636c66c61bcbb11`. The integrated branch and its package remain unchanged. No build, installation or publication was performed for this study.

[Overview](../results/dusk-coast-palette-study-2026-10-14/dusk-coast-overview.png) · [Home before/after](../results/dusk-coast-palette-study-2026-10-14/home-palette-comparison.png) · [Settings before/after](../results/dusk-coast-palette-study-2026-10-14/settings-palette-comparison.png) · [Control states](../results/dusk-coast-palette-study-2026-10-14/states-after.png).

All images are saved in Library; exact IDs are in [attachment references](../results/dusk-coast-palette-study-2026-10-14/library-attachments.json). They are matched 1920 × 1080 **static component renders**, not native screenshots. Original artwork bytes, typography, content, layout, targets and behavior are preserved. Home overlay colors now derive from the background token so the original scenery fades into ink. The image itself was not recolored. Gold metadata was removed from Home so gold identifies focus there; warm ivory checkmarks and selection edges remain distinct.

| Role | Exact colors |
|---|---|
| Ink ground / primary text | `#151C26` |
| Warm ivory text / secondary text | `#F4ECDD` / `#BDC2C9` |
| Coral primary | `#D88B72` → `#C97B63` |
| Pressed primary | `#BF705B` → `#D18A73` |
| Slate secondary | `#303B48` → `#293440` |
| Pressed secondary | `#222C37` → `#354251` |
| Selected slate | `#404B59` → `#34404D`; edge `#E7D9BF` |
| Disabled fill / text | `#282F39` / `#9DA4AE` |
| Lighthouse focus / slate border | `#E6B963` / `#697585` |

Shared tokens and control paints carry the actual study. The full [palette and measurements](../results/dusk-coast-palette-study-2026-10-14/palette.json) are exported from those components, not a separate mockup palette.

Contrast ratios: ivory/ink **14.59:1**; secondary text/ink **9.56:1**; dark text across coral states **≥4.64:1**; secondary text across slate states **≥5.72:1**; selected rows **≥4.95:1**; disabled text **5.37:1**. Gold/ink separator is **9.37:1** and gold/selected slate **≥4.85:1**. Gold is separated from coral by the existing dark contour; no claim is made that gold against coral alone reaches 3:1. Focus also underlines text, and selection retains its checkmark. Controls do not animate.

Validation: eight focused tests across four suites passed, including actual Home/Settings exports, state contrast floors and existing activation/geometry checks. Typecheck and targeted lint passed. A focused selected-row export regression passed after updating its palette expectation. The final overview and state strip were visually inspected. Native appearance, remote input and VoiceView remain unverified; this study deliberately does not reopen the blocked native session.

Reproduction:

```sh
python eval/preview/export_palette_study.py
npm --prefix app run typecheck
npm exec --prefix app -- eslint app/src/calmframes/calmStyles.ts app/src/calmframes/CalmControlSurface.tsx app/src/calmframes/CalmButton.tsx app/src/calmframes/HomeHarborScene.tsx app/src/calmframes/KidHomeScreen.tsx app/src/calmframes/ParentAreaScreen.tsx app/test/calmframes/controlSurface.test.tsx
/tmp/calm-home-preview-venv/bin/python eval/preview/render_palette_study.py
npm --prefix app test -- --runInBand --coverage=false --watchman=false controlStudy.test
```

Node 22 and the existing preview/toolchain environments were reused; no dependencies added. Test summaries and artifact hashes are alongside the images. No artwork, media, guard, storage or timing files changed. [Native task](codex://threads/01a138bb-a422-7746-9293-caf676f250f3).
