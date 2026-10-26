# Dusk lantern: the finished Home and Details, 14 October 2026

Branch `claude/dusk-lantern-2026-10-14`, from `f95a366`, the immersive composition
study on top of the approved dusk coast integration. This pass changes the Home and
Details composition and nothing underneath it: no media, map, guard, timing,
storage, dependency or palette change.

## What a family sees

- **Home.** The harbor fills the screen and the lighthouse stays clear of every
  control. The title sits low left in Fraunces at one readable size, with its one
  line of story. Watch now is the only coral action; Details beside it is quiet.
  Under the actions, a checked story with nothing to hold says so: "Harbor plays
  without picture holds." On the right, the lantern: "Watch with fewer flashes",
  the supported-title limitation in one sentence, one plain sentence about the
  demo, and a Picture hold demo control. How it works and Parental controls are
  quiet actions in the header.
- **Details.** One factual line under the title, "20 sec · No picture holds" for
  Harbor and "Optional demo · 20 sec · 2 practice holds" for the demo, counted
  from the same merged schedule the page already builds. Watch now, the caveat,
  Viewing details, Before you watch, the picture timeline and the viewing plan
  are as they were.
- **Back.** The route remembers which control started a title, now including the
  demo control, so Back from the demo's page lands on Picture hold demo, Back
  from playback started with Watch lands on Watch now, and Back from Details
  lands on Details. The player route still paints the harbor opening while its
  module loads, so the first Watch never shows a black frame.

## Supported content, said plainly

Calm Frames plays the titles packaged with it. Harbor was made without flashing
and has no picture holds; the 20 second demo has two scheduled practice holds
that show a still picture while sound and captions continue. Those holds are
examples, not detected flashing. On supported titles, marked scenes use a still
picture while sound continues. Detection can miss flashing: Calm Frames reduces
exposure to flashing above published limits in the videos it plays; not a
medical device. It does not filter other streaming apps.

## Before and after

Matched 1920 by 1080 and 1280 by 720 renders of the actual component trees in
Chromium, through the same export and host renderer the earlier studies used.
These are static browser renders, not simulator screenshots, and nothing here has
been seen on the Vega Virtual Device.

- [Before and after sheet](../results/dusk-lantern-2026-10-14/before-after.png),
  left `f95a366`, right this branch
- [Home 1080p](../results/dusk-lantern-2026-10-14/1080/home.png),
  [Details 1080p](../results/dusk-lantern-2026-10-14/1080/details.png)
- [Home 720p](../results/dusk-lantern-2026-10-14/720/home.png),
  [Details 720p](../results/dusk-lantern-2026-10-14/720/details.png)
- [Control bounds](../results/dusk-lantern-2026-10-14/bounds.json) and
  [scene contrast under the added lines](../results/dusk-lantern-2026-10-14/contrast.json)

The renderer asserts that every control and added line sits inside the five per
cent safe area at both sizes, that nothing with a test id covers the lighthouse
lamp, and that the scene behind the two lines drawn over it keeps at least
4.5 to 1 against the dim text colour. The Home line measures 9.56 to 1 and the
Details synopsis 5.75 to 1.

To regenerate:

```sh
python3 eval/preview/export_composition.py
cd eval/preview && /tmp/calm-home-preview-venv/bin/python render_dusk_lantern.py
```

## Build and install

The package is built the way the earlier receipts describe, from a checkout with
Node 22, JDK 21, the Vega SDK and Python 3.12 on PATH:

```sh
source ~/vega/env
eval "$(fnm env)" && fnm use
export JAVA_HOME=/opt/homebrew/opt/openjdk@21
bash scripts/release.sh --arch aarch64 --build-type Debug --tag dusk-lantern-2026-10-14
vega device is-connected --device Simulator
vega device install-app --device Simulator --packagePath build/release/dusk-lantern-2026-10-14/calm-frames-0.1.0-aarch64-debug.vpkg
vega device launch-app --device Simulator --appName io.github.alejandropublius.calmframes.main
```

The generated Shaka output in `app/src/w3cmedia/shakaplayer/dist` and
`app/src/w3cmedia/polyfills` comes from the app's postinstall; a fresh worktree
installed with `--ignore-scripts` needs it copied from a built checkout first.
Household data is preserved on install; never reset it to reach setup.

## Credits

The harbor scene, the zen mark and the Harbor film are the project's own, listed
with their licences in `media/LICENSES.csv` and `docs/brand/README.md`. Fraunces
and Source Sans 3 are OFL faces whose provenance is in
`app/assets/fonts/FONT_PROVENANCE.json`. The composition took its cues from the
Refero research of the same day (Letterboxd's metadata rail, Chantlings' single
warm accent, INVERSA's low anchored headline, Netflix's centred profile row);
no reference artwork or copy was reproduced.
