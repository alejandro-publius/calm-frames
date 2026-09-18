# @calm-frames/flash-guard

A drop in flash guard for Vega video apps that play through
`@amazon-devices/react-native-w3cmedia`.

Give it the player and where the signed flash map is. It hides every flagged
part of a title before it starts while the sound and the captions keep playing,
says what it did, and makes every way of moving the playhead safe.

It reduces exposure to flashing above published limits in the videos it plays.
It is not a medical device.

## Install

```
npm install @calm-frames/flash-guard
```

Peers: `react`, `react-native`, `@amazon-devices/react-native-w3cmedia` and
`@amazon-devices/kepler-media-controls`.

## Use

```tsx
import {
  CalmCard,
  CoverLayer,
  SafeMediaControlHandler,
  useFlashGuard,
} from '@calm-frames/flash-guard';

const guard = useFlashGuard({
  mediaRef: videoRef,
  mapUrls: { wcag: title.flashMapUrl },
  expectedSha256: title.sha256,
  publicKeyBase64: OUR_PUBLIC_KEY,
  ready: isVideoInitialized,
});

// Between the video surface and the captions view.
<CoverLayer visible={guard.covered} mode={guard.coverMode} />
// Above both.
<CalmCard card={guard.card} onSkip={guard.skipTo} />
```

Then two rules for the rest of the app:

1. **Nothing writes `currentTime` or calls `fastSeek` any more.** Every seek
   goes through `guard.requestSeek(source, targetMs)`, where source is one of
   `seek-bar`, `dpad-fast-forward`, `dpad-rewind`, `trickplay` or
   `media-control`. If a target lands inside a flagged part or its guard band,
   the guard covers the picture, then seeks, and holds the cover until playback
   is confirmed outside.
2. **Hand `SafeMediaControlHandler` to `setMediaControlFocus`**, so Alexa and
   the remote's transport commands go through the same function:

```ts
new SafeMediaControlHandler({
  engine: guard.seekEngine,
  getCurrentMs: () => (videoRef.current?.currentTime ?? 0) * 1000,
});
```

`docs/INTEGRATION_DIFF.md` in the Calm Frames repository is that change made
against a clean `vega-video-sample` checkout: 32 lines added across four files.

## What it needs from the app

- **A public key.** Maps are signed with Ed25519. The app ships the public half
  and never the private one.
- **A SHA-256 per title**, of the file that will play. That hash is the
  binding: a map that verifies against a different file says nothing about this
  one, and the guard refuses it.

## Fail closed

A map that is missing, stale, unsigned, unreadable, in a version this build
does not know, signed by a key the app does not hold, or bound to a different
file is not a map. In every one of those cases the picture stays hidden and
`guard.card` says the title is not checked yet. `covered` starts true and only
a verified map turns it off.

`kidModeTitles` is the matching rule for a shelf: it takes checked titles and
returns the verified ones, so an unchecked title cannot be listed.

## The manifest

Two entries in `manifest.toml`:

```toml
[[wants.privilege]]
id = "com.amazon.devconf.privilege.accessibility"
```

for the VoiceView announcements, and the `IMediaPlaybackServer` extras block
with `command_options` including `StartOver`, `SkipForward` and `SkipBackward`
and `AdvancedSeek` in `features`, without which the transport commands never
reach the app at all.

## Accessibility

Every card is an `aria-live="polite"` region and is also pushed through
`AccessibilityInfo.announceForAccessibilityWithOptions` with `{ queue: true }`,
so an announcement already in progress finishes rather than being cut off. Type
is sized for a television across a room, focus is a thick visible ring, and
nothing moves.

## Where the maps come from

The `flashmap` analyzer in the same repository, which measures a file against
the WCAG 2.3.1 general and red flash thresholds and writes a signed sidecar.
`docs/SIDECAR_SPEC.md` is the format, and any producer that writes it works.

## Licence

Apache-2.0. The mirrored engine under `src/engine` is generated from
`app/src/calmframes` by `hook/tools/sync.mjs`; edit it there.
