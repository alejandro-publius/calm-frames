# Calm Frames: finishing the viewing experience

Reviewed October 11, 2026. The native source changes below still need a fresh
Vega Virtual Device build and observation before the final recording.

## Public design reference

This review studied OpenAI's public
[Apps SDK UI](https://github.com/openai/apps-sdk-ui/tree/0f00143c7a639906f1621fe58e1b6be7b5bea46d),
at commit `0f00143c7a639906f1621fe58e1b6be7b5bea46d`. It is a web component
library for ChatGPT apps. The TV adaptations here are our design decisions,
not advice or approval from OpenAI's internal design team.

| Public reference | Principle applied to Calm Frames |
| --- | --- |
| [Semantic type and spacing tokens](https://github.com/openai/apps-sdk-ui/blob/0f00143c7a639906f1621fe58e1b6be7b5bea46d/src/styles/variables-semantic.css) | Keep a clear title, synopsis and action hierarchy using the existing TV-sized Inter styles. |
| [Button variants and states](https://github.com/openai/apps-sdk-ui/blob/0f00143c7a639906f1621fe58e1b6be7b5bea46d/src/components/Button/Button.mdx) | Give secondary navigation quieter emphasis and keep state feedback from moving the controls. |
| [Menu focus restoration](https://github.com/openai/apps-sdk-ui/blob/0f00143c7a639906f1621fe58e1b6be7b5bea46d/src/components/Menu/Menu.tsx) | Returning to a choice should retain context and prefer the selected item for focus. |
| [Empty-state structure](https://github.com/openai/apps-sdk-ui/blob/0f00143c7a639906f1621fe58e1b6be7b5bea46d/src/components/EmptyMessage/EmptyMessage.tsx) | Review loading, empty and failure states with the same care as the library, using useful text and an available next action. |

The app retains its own monk and halo, teal surfaces, cream text and saffron
focus. This initial pass added no web component dependency, hover behavior,
decorative motion, pulsing indicator or smaller web type scale. The later
optional interface effects are described below.

## Changes in this pass

The library now uses a concise Harbor synopsis that explicitly identifies it
as an original demo film. Details retain the full preparation disclosure, and
the separate practice-hold version keeps its explanation and labels. This
restores the short reading block beside the artwork without hiding what the
demo represents.

Parental controls reserve a fixed space for saving feedback beside the title.
The message appears there while the existing write is pending, with the same
polite announcement and interaction guards. It no longer inserts a row above
the settings on every save.

Setup now offers Back from TV and seating to the viewing preset, and from the
review to TV and seating. Choices and the confirmed PIN remain in memory.
Nothing is saved until Open library; the existing storage flow still owns
completion and failure recovery. Returning to a choice prefers the selected
control and clears the old focus styling.

## Visual review

These images are browser layout approximations made from the actual rendered
React Native component trees, bundled Inter and existing artwork. They use
synthetic household, focus and saving inputs. They are not native Vega captures.

- [Library](seamless/library-family-browser.png): a short synopsis keeps the
  artwork and library titles in view.
- [Parental controls at rest](seamless/parent-idle-browser.png) and
  [while saving](seamless/parent-saving-browser.png): the shared controls retain
  their positions as feedback appears beside the title.
- [Setup review](seamless/setup-review-browser.png) and
  [its actions after scrolling](seamless/setup-review-bottom-browser.png):
  Back is secondary to Open library. Native scrolling when focus moves to
  these actions remains part of the Vega check.

Source hashes, screenshot hashes, measurements, check results and scope limits
are recorded in
[`seamless_design_2026-10-11.json`](../../results/seamless_design_2026-10-11.json).
Browser text metrics and flex layout may differ from the native renderer.

## Final interface effects

After this review, Alex requested motion and interactive sounds. Parental
controls now offer Gentle artwork motion and Selection sounds independently.
Both are Off for new and existing households until a parent enables them;
existing PIN, viewing settings and warning-chime preferences are preserved.

The library and title artwork can settle into place once when a page opens.
Text, focus rings, setup and playback covers stay stationary and fully opaque.
Motion requires the system preference to explicitly allow it. Unknown or failed
preference queries keep artwork still; leaving, backgrounding or disabling the
effect cancels the entrance without replaying it later on the same page.

The original selection tone confirms accepted menu actions and successful
settings saves. Focus movement and Watch actions stay silent. The sound is
separate from the warning before a cover; it is stopped before playback and
suppressed when screen-reader status is unknown or enabled. Late initialization,
rapid requests and audio failures must not delay an action or queue later cues.

The installed Vega SDK provides the native animation and audio APIs used here.
Unit tests establish the lifecycle rules, not perceived quality, real audio
focus or native rendering. These changes follow the browser proofs above;
their intermediate animation frames and sounds are not demonstrated by those
images or by the static UI colour check. The native acceptance and recorded-video
checks in [MAC_FINISH.md](../MAC_FINISH.md) remain required.

## What makes the product finished

The next design gate is the current native app on Vega. Review the whole
journey: setup, choosing a story, playback, returning to the library, opening
parental controls and recovering from an unavailable title or failed save.
Check wrapping, reading distance, selected state, remote focus and screen-reader
order at every step. Keep the earlier capture evidence until the replacement
package, captures and demo agree on their source identity.

Use [MAC_FINISH.md](../MAC_FINISH.md) for the native procedure and
[COMPLETION_CHECKLIST.md](../COMPLETION_CHECKLIST.md) for release blockers.
Automated checks and browser layout proofs cannot establish native usability.
