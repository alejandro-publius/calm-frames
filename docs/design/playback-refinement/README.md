# Playback UI refinement

The player now keeps pause status visible after the controls hide, gives icon
controls explicit names and contrasting focus rings, and shows a recoverable
playback error above the retained safety cover. The error has one preferred
focus action, Go back, which uses the existing navigation and cleanup path.

The earlier Back control overlapped the Practice holds label. Back and the title
now share a row at the upper right. Captions choices fit in a wider menu above
the caption area; the seek row and captions button have separate space inside
the TV safe margins. The controls refresh after media initialization so they receive the current
text tracks and duration; Back remains available while the media loads.

Pausing a scheduled hold changes its visible and accessible text. Pausing before
a hold explains that the countdown is stopped and keeps Skip available. The
presentation listener only reads playback events. The guard card, cover state,
seek target, media, verification and saved settings are unchanged.

## Browser comparisons

These are browser approximations of the actual React Native component trees,
including the real VideoPlayerUI, timer, caption menu, card, cover and error
screen. The baseline is `4302bff04312d74cc970a4d4a4757e6ab84216b4`.

| State | Before 1080p | After 1080p | Before 720p | After 720p |
|---|---|---|---|---|
| Back focused | [Before](before/1080/controls-back.png) | [After](after/1080/controls-back.png) | [Before](before/720/controls-back.png) | [After](after/720/controls-back.png) |
| Captions focused | [Before](before/1080/controls-captions.png) | [After](after/1080/controls-captions.png) | [Before](before/720/controls-captions.png) | [After](after/720/controls-captions.png) |
| Captions menu | [Before](before/1080/caption-menu.png) | [After](after/1080/caption-menu.png) | [Before](before/720/caption-menu.png) | [After](after/720/caption-menu.png) |
| Playing hold | [Before](before/1080/playing-hold.png) | [After](after/1080/playing-hold.png) | [Before](before/720/playing-hold.png) | [After](after/720/playing-hold.png) |
| Paused hold, controls hidden | [Before](before/1080/paused-hold.png) | [After](after/1080/paused-hold.png) | [Before](before/720/paused-hold.png) | [After](after/720/paused-hold.png) |
| Paused countdown, controls hidden | [Before](before/1080/paused-countdown.png) | [After](after/1080/paused-countdown.png) | [Before](before/720/paused-countdown.png) | [After](after/720/paused-countdown.png) |
| Paused story, controls hidden | [Before](before/1080/paused-story.png) | [After](after/1080/paused-story.png) | [Before](before/720/paused-story.png) | [After](after/720/paused-story.png) |
| Playback error | [Before](before/1080/error.png) | [After](after/1080/error.png) | [Before](before/720/error.png) | [After](after/720/error.png) |

## What the evidence establishes

The [before checks](before/checks.json) and [after checks](after/checks.json)
record error visibility, pause wording, focus-ring pixels, safe margins and
separation of captions, menu and controls. Bounds and browser hit-test results
are saved beside them. The regression tests run the actual screen and controls;
they exercise pause/resume, listener cleanup, Skip, caption selection and focus
return to the seek bar, plus leaving the error screen once after repeated presses.
The new regression cases fail against the untouched baseline.

[The receipt](../../../results/playback_design_2026-10-14.json) records focused
checks, source hashes, preview hashes and the remaining native work.

## Limits and reproduction

The native video surface uses the existing Harbor artwork as a static stand-in.
The picture-hold preview uses the image already embedded in the signed demo map.
Native captions are represented by a cue from the current Harbor VTT, and the
SDK seek bar uses a simple browser bar. Guard inputs and media events are fixture
data. The icon glyphs and Inter fonts come from the installed app dependencies
and assets. None of these previews establishes video timing, audio, native
caption rendering, Yoga layout or actual D-pad/VoiceView behavior.

To reproduce, copy `eval/preview/playback.fixture.tsx` into
`app/test/calmframes/playbackPreview.test.tsx` beside `playbackUiHarness.tsx`.
Set its stage, height, window dimensions and pixel-scale numerator for the
chosen resolution, then run that fixture with Jest and `--no-cache`. Export
both resolutions before running `eval/preview/render_playback.py --stage after`.
For the baseline, copy the same harness and fixture into a detached checkout
at the baseline commit and pass that checkout through `--source-root` with
`--stage before`. Remove only the temporary exporter after the run.

Native acceptance is still pending: observe pause/hold messaging after controls
hide, the first visible controls, D-pad focus entry and return, VoiceView labels,
native caption placement and error recovery on the matching Mac/Vega build.
