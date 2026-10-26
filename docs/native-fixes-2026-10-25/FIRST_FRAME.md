# Near-white transition investigation

The received [measurements](../../results/native-validation-fbe53bf-2026-10-25/evidence/pale-frame-measurements.json)
and [contact sheet](../../results/native-validation-fbe53bf-2026-10-25/evidence/t12-1080-otters-preview-start-frames.jpg)
describe **fbe53bf Debug**, not the new source. They record near-white frames
on McWay opening and its resume choice (at least 0.068 seconds each), Sea Otters
preview opening (0.417 seconds) and Forest preview opening (0.468 seconds).
These are recorder-derived lower bounds, not a frame-rate or latency benchmark:
the recorder writes only when the picture changes. Still scenes, Open library
and the recorded cold starts did not show this frame. Root cause was not
established by those observations.

## App-side evidence and bounded fix

The installed React Navigation DefaultTheme uses `rgb(242, 242, 242)` as its
background. Its stack card container paints that background before route
content. The previous app root supplied no background and the stack supplied
no card background override. Both now use the existing coastal
`CALM_WORLD.BACKGROUND` (`#F7EACF`) in [App.tsx](../../app/src/App.tsx) and
[AppStack.tsx](../../app/src/components/navigation/AppStack.tsx). Navigation animation
remains disabled. The regression failed before that change and now passes.

This is a credible app rendering path for an otherwise empty near-white frame,
not proof of the recorded frame's origin. In particular,
[RecoverablePlayback.tsx](../../app/src/calmframes/RecoverablePlayback.tsx)
does not mount its player child until the playing phase. The recorded pale
frame while opening the resume choice therefore cannot be assigned to a newly
mounted decoder without further evidence. A native/compositor layer or a
previous surface can still behave independently of the React background.

## Deliberately unresolved

The Sea Otters contact sheet also shows a coastal picture before the otters,
after the opening card; the Forest recording reports a brief dark ending.
Those are separate from the uniform route background. Their media/surface
origin is not established by a screenshot sheet. No approved media, signed
maps, source hashes, covers, timeouts or decoder sequencing were changed.
There is no invented native first-frame callback or claimed timing guarantee.

For the new exact package, observe McWay Watch, the saved-position choice and
the two optional previews using the same benign routes. Record whether the
uniform pale frame persists and separate it from any first media picture or
ending gap. Keep change-only recorder limits explicit. Only if this remains
ambiguous should a small sanitized excerpt from the named transition and its
capture receipt be requested; the whole archive is unnecessary now.
