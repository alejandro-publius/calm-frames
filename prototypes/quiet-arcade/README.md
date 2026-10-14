# Quiet arcade, a 3D visual prototype

A browser-only prototype to judge one direction for Calm Frames: a small, quiet
room with real depth, warm light and an original character. It is evidence of a
look, not a television implementation. Nothing here touches the Vega app, its
dependencies or its media.

## Run it

```sh
cd prototypes/quiet-arcade
npm install            # Three.js 0.186.1, MIT, the only dependency
npm run serve          # serves the repository root on 127.0.0.1:4173
```

Then open `http://127.0.0.1:4173/prototypes/quiet-arcade/`. The page is served
from the repository root so it can use the app's own Fraunces and Source Sans 3
faces. Module scripts do not load from a `file://` address, so a server is needed.

## What is in the room

Everything is procedural geometry built in `scene.js`: a rounded floor slab and
two walls in muted violet, two rounded cabinets (cream with a coral marquee for
Harbor, teal with a gold marquee for the demo), a stool, a plant, a framed
picture and a pendant lamp. The lamp, a warm key light and a cool violet fill
light the room; shadows come from the lamp and the key, with soft contact discs
under the things that stand on the floor.

The lantern keeper is original: a bell-shaped figure in the coral robe, a hooded
ivory head with closed eyes, and a small lantern on a pole that gives the room
its one warm point of light. Selected, it bows once and the lantern brightens,
then everything returns to rest. Nothing in the room moves on its own.

## Controls

| Key or pointer | Does |
|---|---|
| Left, Right | choose the keeper, the Harbor cabinet or the demo cabinet |
| Enter | greet the keeper, or select a cabinet (the camera eases a little toward it) |
| Escape | clear the selection, or close the open panel |
| Up, Down | move between the menu and the room |
| Pointer | hover to choose, click to select, click the floor to clear |
| Still | keeps the room from moving: the keeper's greeting becomes light only, and selection no longer moves the camera. On by default when the system asks for reduced motion |

The four controls live outside the canvas: Try demo, Atmosphere, Still and Help.
Atmosphere lists Arcade (this scene) and Forest and Coast, both labelled "Not
built yet". Try demo opens a notice that the real Harbor demo is not wired into
this prototype. If WebGL is unavailable, or `?fallback=1` is added to the
address, the page shows a still of the room and the same menu.

## Verify it

```sh
npm run verify
```

`verify.py` serves the repository, drives the page in headless Chromium with
software rendering, presses the keys above, clicks the demo cabinet where it is
drawn, asserts the scene's own state after every step, and writes
`captures/01-arcade.png` to `captures/08-fallback.png`, `captures/interaction.webm`
and `captures/verify.json`. The first screenshot also becomes the fallback still.
This proves the interactions in a browser; it says nothing about a Fire TV remote,
VoiceView or the Vega renderer.

## Credits

Three.js (MIT) is the renderer. Fraunces and Source Sans 3 are the repository's
own OFL faces. The room, the cabinets and the keeper are drawn in code for this
prototype and reproduce no reference artwork. Three Refero screenshots were
viewed for principles only: Luma AI's interactive scenes page, Luma AI's 3D
model viewer on iOS, and Tilt's avatar screen.
