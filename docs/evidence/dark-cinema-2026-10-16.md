# Dark cinema viewing flow

Private working branch: `codex/dark-cinema-2026-10-16`, based on preserved
`1509c1bc1270b6156e18c6b5f18af3ff835ce416`. The prior branch remains available.
The approved reference is the top option of Library file
`libfile_a0d840881b648191a4b25dfdc5e9fa99`.

## What changed and why

The video title is the largest text. Calm Frames is a small header wordmark.
A full-screen coastal scene provides atmosphere; dark gradients protect the
reading area and navigation. The bright rounded Watch button is the clearest
action. Details is quieter. Fraunces headings and Source Sans 3 controls remain.
The Home rail contains the two actual prepared videos, Harbor and Acadia.
Focusing a card changes the hero title, image and both actions without playing.
Selecting a card opens its Details. No invented catalog items are shown.

Details repeats the same image, title, runtime and Watch treatment. More info
and Technical details remain optional. Critical errors, the labelled simulated
demo and Help disclosures remain. The opening/return screen and player controls
share the dark palette, avoiding the previous ivory-to-dark change at playback.
Focus changes border and underline without resizing the controls. Press feedback
keeps the primary label readable. Menu controls use stable six-unit boundaries.

## Remote route

Home opens with Watch focused. Right reaches Details. Down reaches the video
rail; Left/Right chooses Harbor or Acadia. Select opens the selected Details,
where Watch is preferred. Back from playback restores the opening control;
Back from Details restores the Home card or Details control that opened it.
More info > Watch demo > demo Details > playback returns one level at a time.
Technical details returns to its opening control in More info. Parents cancel
returns to Parents without entering a PIN or changing settings.

## Assets and motion

Harbor uses existing `harbor-cinematic.png`. Acadia uses a byte-identical copy
of an existing prepared-video still, with provenance beside the image. No new
frame was extracted and no screen was captured. Signed media, maps, reports,
trust keys, catalog routes and household settings are untouched.

The native player supports video surfaces, but the available Harbor animation
has camera movement and a cut. No verified fixed-composition water-only loop
is available. This version therefore uses the permitted still fallback.
Decorative ripple lines were removed. Water-only motion remains outstanding;
no web animation or whole-image pan is substituted. The saved motion setting
is preserved. The unused legacy opening-animation component is unchanged.

## Verification boundary

The source gate passes 132 suites, 1,318 tests and 57 textual component
snapshots, with four existing skipped tests. Typecheck and lint pass. The
selection tests verify actual-title selection, action identity and one preferred
return control. The contrast tests cover primary and secondary materials,
focus and pressed states. Capture/export suites were excluded.

Native build and remote-check evidence is recorded separately in the receipt.
Text logs can establish emitted route, requested focus, playback identity and
media events. They cannot establish visual polish, visible focus, compositor
paint order, audible quality, captions or VoiceView. Owner visual acceptance
and the water-loop seam remain open.
