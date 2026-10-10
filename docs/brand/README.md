# The Calm Frames mark

A peaceful monk inside a rounded frame, with one open halo. Teal ground,
cream face and text, saffron robe. The single open line stays readable at
small sizes. The identity is still, with no pulsing or animated halo.

The brand line is **A calmer way to watch**. It describes the experience;
it is not a clinical or detection guarantee.

## Making the files

    cd app/assets/brand
    ../../../.venv/bin/python make_logo.py   # writes the three SVGs
    ./render.sh                              # writes every PNG

`make_logo.py` draws the three SVGs. `render.sh` renders them at the requested
sizes using the installed Qt SVG engine, with headless Chrome as a fallback.
`render_qt.cpp` is the small native renderer, compiled under `build/brand`.
The Qt route needs the macOS command line tools and `pkg-config Qt6Svg`.
No new renderer was downloaded for the October 9 refresh.

Both are checked in, so every image here can be rebuilt from the two scripts.

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

The tile asks for `Amazon Ember` first, which is what Vega draws React Native
text in and what `src/components/rotator/AutoRotator.tsx` names outright. Ember
is Amazon's, it is not on this machine, and it is not ours to redistribute, so
the PNG checked in here is rendered in the first fallback that is installed.
Anything with Ember available, including the device, gets the real font from the
SVG. If the tile is ever rebuilt on a machine with Ember, the PNG will change
and that is the intended outcome.

## October 9 review

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

The five colours at the top of `make_logo.py` are the app's palette tokens, in
`app/src/calmframes/calmStyles.ts`. What each one may be used for is decided by
measured contrast, not by taste:

| Token | Hex | Contrast on teal | What it may carry |
|---|---|---|---|
| Teal | `#1F4D5C` | ground | Every screen sits on it |
| Cream | `#F3E8D3` | 7.60:1 | Text, at any size |
| Saffron | `#E6A957` | 4.47:1 | The focus ring and fills. **Not text** |
| Saffron dark | `#B87A2C` | 2.58:1 | Edges and fills only. Carries nothing |
| Ink | `#17323C` | n/a | Text on cream (11.10:1) and on saffron (6.53:1) |

Saffron misses the 4.5:1 floor for text by 0.03, so it is a ring and a fill and
never a label. The dark saffron carries no text at all: ink on it is 3.76:1 and
cream on it is 2.95:1, and both are under the floor.
`app/test/calmframes/tenFoot.test.tsx` measures every rendered line against
whatever is actually painted behind it, so a colour used in the wrong place
fails there rather than here.
