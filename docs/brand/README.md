# The Calm Frames mark

A peaceful monk inside a rounded frame, with one open halo. Teal ground,
cream face and text, saffron robe. The single open line stays readable at
small sizes. The identity is still, with no pulsing or animated halo.

The brand line is **A calmer way to watch**. It describes the experience;
it is not a clinical or detection guarantee.

## The inset border, Oct 14

Alex asked for a border on the launcher tile. The bust mark and the Fire TV
tile now carry a warm-sand (`#E5D9BA`) inset line, one percent of the height
in from every edge and concentric with the frame's corners, drawn last by
`make_logo.py`. It is static artwork: no glow, no shadow, no extra text. The
launcher's own focus treatment is the system's and is not imitated. The head
mark, used under 96 px, has no border because one percent of 48 px is under a
pixel. The 512 manifest icon is what a sideloaded package shows on the
launcher and in Settings; the 1280 by 720 tile is the Appstore listing asset.
The previous renders are in Git history before this change.

## Making the files

From the repository root:

    .venv/bin/python app/tools/brand/make_logo.py   # writes the three SVGs
    app/tools/brand/render.sh                      # writes every PNG

`make_logo.py` draws the three SVGs. `render.sh` renders them at the requested
sizes using the installed Qt SVG engine, with headless Chrome as a fallback.
`render_qt.cpp` is the small native renderer, compiled under `build/brand`.
The generators live in `app/tools/brand`; generated SVGs remain in
`app/assets/brand`. Only runtime assets belong in the packaged asset tree.
The Qt route needs the macOS command line tools and `pkg-config Qt6Svg`.
No new renderer was downloaded for the October 9 refresh.

Both are checked in, so the logo exports here can be rebuilt from the two scripts.

## The three drawings

| File | What it is | Used for |
|---|---|---|
| `calm-frames-mark-bust.svg` | Head and shoulders in the frame | Every icon at 96 px and above |
| `calm-frames-mark-head.svg` | The same person, drawn larger | Anything under 96 px, where the bust loses the face to the robe |
| `calm-frames-tile-1280x720.svg` | The mark beside the wordmark | The Fire TV tile |

## The sizes, and where each one is required

Rechecked against Amazon's own listing page on 2026-10-09. Quotes below so this can be
re-checked rather than trusted.

| File here | Size | Format | Required by |
|---|---|---|---|
| `../../app/assets/image/CalmFrames.png` | 512 x 512 | PNG, under 1 MB | The `icon` field in `app/manifest.toml` |
| `appstore-icon-512.png` | 512 x 512 | PNG, transparent | Appstore large icon |
| `appstore-icon-114.png` | 114 x 114 | PNG, transparent | Appstore small icon |
| `firetv-app-icon-1280x720.png` | 1280 x 720 | PNG, **no transparency** | Fire TV App Icon, the tile on the home screen |
| `preview-1024.png`, `preview-256.png`, `preview-48.png` | as named | PNG | Previews only. Not submitted anywhere |

From
[the 0.24 manifest page](https://developer.amazon.com/docs/vega/0.24/manifest-package.html):

> Image file to be used as the icon for the app within the **Settings** ->
> **Applications** -> **Managed Installed Applications** screen.

> Required resolution and format: 512x512, PNG

> Maximum file size: 1MB

From
[the Appstore listing page](https://developer.amazon.com/docs/app-submission/appstore-details.html#images-and-videos):

> Fire TV App Icon ... Size 1280 x 720px, Format PNG (no transparency)

Small icon "114 x 114px", "PNG (transparent)"; large icon "512 x 512px", "PNG
(transparent)". `app-submission/asset-guidelines.html` now redirects to that
page, so it is the one source for listing assets.

Three things worth knowing:

- **The manifest icon is not the launcher tile.** Amazon scopes it to the
  Settings screen. The tile a viewer sees on the Fire TV home screen is the
  1280 x 720 Appstore asset, which is submitted with the listing rather than
  built into the package.
- **1024 x 1024 is not an Amazon size.** It is an Apple and Google convention.
  The 1024 px file here is a preview and goes nowhere near a submission.
- **The build will not catch a wrong icon.** The packaging tool checks the
  `@image/<name>` spelling and whether the file exists, and a missing file is
  only a warning: its own string is "icon validation is not enforced,
  continuing packaging". There is no size check in it. So
  `app/test/calmframes/manifest.test.ts` reads the PNG header and asserts
  512 x 512 and under 1 MB, and that test was seen to fail both ways: pointed
  at a missing file, and pointed at a 256 px one.

## The wordmark font

The approved October 10 redesign uses bundled InterSemiBold for the wordmark
and InterRegular for the brand line. The Qt renderer registers the same static
licensed faces as the app. The SIL license is in `app/assets/fonts/` and
`docs/design/assets/`. The preserved tile uses #102F3A. The current app UI uses the separately approved dusk-coast palette.
No Amazon font files are redistributed.

## Harbor presentation artwork

The earlier `app/assets/image/tv/harbor.png` was generated with OpenAI's image
generation on October 10, 2026 from our own prompt, with our own earlier vector
illustration (`app/assets/brand/tv/harbor.svg`) as the visual reference. The
supplied output is a 1942 x 809 PNG. Its provenance, the prompt summary and the
exact file hash are recorded in
[`design_polish_2026-10-10.json`](../../results/design_polish_2026-10-10.json),
and its ledger row is in `media/LICENSES.csv`. It is presentation art only,
never a film frame or a signed playback still. It is dedicated under CC0-1.0
with the rest of what we made; the copyright standing of a generated picture is
unsettled, so that dedication covers whatever is ours in it and claims nothing
more, and Alex confirms it at the Oct 21 review. The logo scripts do not
reproduce this generated artwork.

This illustration appears only in the library and title details. It is not a
frame from Harbor or a signed playback hold. The film, checked media and hold
images keep their existing provenance. See
[POLISH_REVIEW.md](../design/POLISH_REVIEW.md) for the design changes and their
cloud evidence. A rebuilt Vega package, native composition and playback checks,
and refreshed demo recordings are still required for this polish.

### Cinematic Harbor artwork

`app/assets/image/tv/harbor-cinematic.png` develops that illustration into the
cinematic storybook direction selected for the app. It was generated with
OpenAI image generation on October 11, 2026, using our existing `harbor.png`
as its visual reference. The prompt asked for a coastal diorama with paper
and clay textures, a saffron sailboat, a lighthouse at sunset, and quiet teal
space on the left for the interface. The image contains no interface text.

The supplied PNG is 1944 x 809 pixels. Its SHA-256 is
`62cbb3b83a5112a414846b64df440b71b0c47a13a923e5c8c024265eb92d0b8c`.
This new asset uses the repository's Apache-2.0 license; its source, credit,
and hash are recorded separately in `media/LICENSES.csv`. The logo scripts
do not reproduce it.

It is presentation artwork and now a source plate for the October 13 animated
Harbor film. Playback holds are extracted from the analyzed film; this PNG is
never handed directly to the cover layer.
`eval/brand_assets_check.py` checks this asset independently; that check does
not establish native screen composition or the behavior of transitions.

## October 13 water opening

`app/assets/image/tv/harbor-water.png` is the opening's background plate. It was
generated with OpenAI image generation from our `harbor-cinematic.png`, asking
for a close view of the same harbor's teal water and warm reflections. No text
or interface is painted into the image. The app adds the mark and wordmark.
It uses the repository's Apache-2.0 license. Its provenance and digest are in
`media/LICENSES.csv` and the in-app credits include it. It is presentation art,
not a frame from the old geometric movie or a signed playback still.

## October 9 review of the mark

The 512 px and 114 px listing icons and 48 px preview retain the closed eyes,
smile and open halo. The tile uses full-opacity cream for both the name and
brand line. Its teal ground is opaque; the rounded icons retain transparent
corners. The manifest icon is generated from the same source as the large
listing icon. Review the actual PNGs after changing renderers or fonts.

Run `.venv/bin/python eval/brand_assets_check.py` and the brand asset tests,
then the app's `ui:flashmap`, manifest and ten-foot checks. These checks do not
establish native screen composition. Current run evidence is recorded in
`docs/COMPLETION_CHECKLIST.md`.

## The palette

These are the preserved artwork palette and original token roles, not the current app UI tokens. The approved dusk-coast UI does not recolor these assets.

The palette has one home: the [palette on the design page](../design/README.md#palette),
which lists every `CALM_COLORS` entry in `app/src/calmframes/calmStyles.ts`
with its use, and the pairs that carry text with their contrast ratios. This
section keeps only what is particular to the mark.

The five original colours at the top of `app/tools/brand/make_logo.py` are
app tokens, and `eval/tests/test_design_page.py` fails if one of them stops
being a palette colour or if any colour beyond the sixth appears. The sixth,
`SAND`, is the inset border Alex asked for on Oct 14; it is artwork only and
maps to no token:

| make_logo.py | Token | Hex | In the mark |
|---|---|---|---|
| `TEAL` | `BACKGROUND` | `#102F3A` | The ground of the icons and of the Fire TV tile |
| `CREAM` | `TEXT` | `#F3E8D3` | The halo, the face, the wordmark and the brand line |
| `SAFF` | `FOCUS_RING` | `#E6A957` | The robe |
| `SAFFD` | `ACCENT_DARK` | `#B87A2C` | The single fold line across the robe |
| `INK` | `INK` | `#17323C` | The closed eyes and the smile |
| `SAND` | none | `#E5D9BA` | The inset border on the bust mark and the tile, added Oct 14 |

The tile draws the wordmark and the brand line in full-opacity cream on the
opaque teal ground. Contrast values measured against the older `#1F4D5C`
ground do not describe this palette.
