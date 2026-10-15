# Plain language review, October 15

This pass follows the implemented composition A. It changes visible sentences,
labels and their accessibility equivalents, with corresponding test expectations.
It does not change route IDs, focus handlers, PIN rules, playback timing, detection,
map verification, media, artwork or settings. The hook mirror is synchronized.

## Selected changes

| Before | After | Reason |
| --- | --- | --- |
| Checked frame by frame. No flashing found, so the picture never holds. | The video plays normally. | Say what happens in this verified zero-interval video. Its metadata already reports the finding; the limitations stay below. |
| Try picture holds | Try the demo | Name the action without requiring a new term. |
| Two practice holds show what a picture hold looks like… | The picture pauses twice while sound and captions continue. This demo contains no flashing. | Explain the visible behavior and identify the harmless demonstration. |
| Holding a calm scene | Picture paused | Describe the demo's current picture. The detail and announcement still identify it as a demo. |
| Holding the picture | Flashing hidden | Explain why an actual flagged scene changes. |
| Held the picture for 5 seconds | Scene hidden for 5 seconds | Report the covered duration, without implying every covered instant contained a flash. |
| A flash that is missed is not held. | Any flashing that is missed will still be visible. | Make the detection limitation explicit. |
| Picture holds | Hidden scenes | Explain the parent's playback record. |
| Getting your video ready. It will begin in a moment. | Preparing your video. Checking the video before playback. | Do not promise an immediate start. |
| This title comes from an unsupported source. | The source of this video could not be verified. | Keep the verification reason understandable. The picture remains hidden. |
| Go back and try opening the story again. | Go back and try playing the video again. | Match the available Go back action. |

The table abbreviates the longer demo sentence. Durations such as five seconds
are data-driven, not new fixed values.

## Complete surface audit

- Home: the existing short Play, Details, How it works and Parents labels stay.
  No new help text or status notices were added to the featured Home layout.
- Details and timeline: short summary, clear demo counts, plain hidden-scene
  counts, and explicit detection limits. Existing checks and unavailable states
  still gate playback.
- How it works and onboarding: explain still picture, continuing sound and
  captions, advance warning, Skip, and the harmless demo. The approved medical
  limitation sentence remains byte-for-byte unchanged.
- Parent gate and settings: keep four-digit PIN instructions, dynamic failed
  attempts, lockout timing, local-storage behavior, save errors and recovery.
  Viewing rules still say that closer seating, larger TVs and kid profiles can
  hide more, never less. The Warning chime label describes its function.
- Loading, empty and offline states: describe the actual state and implemented
  next action. Household storage failure still prevents playback until settings
  and PIN are available. Offline wording still distinguishes a local library
  from no locally available videos.
- Playback cards, history and errors: distinguish real hidden scenes from demo
  pauses; retain Skip and duration meaning in screen-reader announcements.
  Missing, stale, wrong-version, wrong-file and unverifiable-source failures
  remain distinct. Every blocked playback message preserves hidden-picture
  behavior. Captions and media control names retain their existing meaning.
- Credits and licence notices: unchanged. Internal identifiers and diagnostic
  log vocabulary retain their technical names.

## Verification limits

Tests deliberately check the replacement wording and the same route and safety
behavior. The three capture/export suites are excluded. Browser checks inspect
DOM focus and geometry without capture. Native log checks establish emitted
focus, routes, media events and still-image load callbacks; they cannot establish
readability, text wrapping, sound continuity, visible captions or VoiceView.
The owner still needs to inspect those on the TV. No PIN was entered or reset.
