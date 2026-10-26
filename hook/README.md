# @calm-frames/flash-guard

A drop in flash guard for Vega video apps that play through
`@amazon-devices/react-native-w3cmedia`.

Give it the player and where the signed flash map is. It hides every flagged
part of a title before it starts while the sound and the captions keep playing,
says what it did, and makes every way of moving the playhead safe.

It reduces exposure to flashing above published limits in the videos it plays.
It is not a medical device.

## Install

**This package is not on npm yet.** Install a local tarball from a reviewed
checkout of the repository. Run the first two commands from the repository
root, then install the tarball into your Vega app:

```sh
CALM_HOOK_PACK_DIR="$(mktemp -d)"
npm pack ./hook --offline --ignore-scripts --pack-destination "$CALM_HOOK_PACK_DIR"
cd /absolute/path/to/your-vega-app
npm install "$CALM_HOOK_PACK_DIR/calm-frames-flash-guard-0.1.0.tgz" --ignore-scripts
```

Peers: `react`, `react-native`, `@amazon-devices/react-native-w3cmedia`,
`@amazon-devices/kepler-media-controls`, `@amazon-devices/react-linear-gradient`,
`@amazon-devices/react-native-kepler` and `@amazon-devices/react-native-svg`,
which draws the control surfaces. They must be installed in the consuming app. A GitHub-root npm install cannot select this monorepo's `hook/` subfolder.

The tarball contains the public TypeScript/TSX sources, their mirrored engine
dependencies, the README and Apache licence. Metro uses the `react-native`
source entry; TypeScript uses the matching `types` entry. The consumer must
transform TypeScript/TSX through its React Native tooling. This is not a package
that plain Node can execute with `require()`.

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
<CoverLayer visible={guard.covered} mode={guard.coverMode} imageUri={guard.coverImageUri} />
// Above both.
<CalmCard card={guard.card} onSkip={guard.skipTo} />
```

Maps produced with scene holds carry checked JPEGs inside their signed payload.
The guard selects one only when its bounds contain the entire scheduled cover.
Pass `coverImageUri` to the cover to keep the scene's preceding context visible
while sound and captions continue. The image is fully opaque and sits over a
black backing; absent images, rejected maps, uncertain playback and image-load
failures retain that backing. The countdown and seek rules are unchanged.

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
against a clean `vega-video-sample` checkout: <!--n results/integration_diff.json:lines_added -->32<!--/n--> lines added and <!--n results/integration_diff.json:lines_replaced -->2<!--/n--> replaced across <!--n results/integration_diff.json:files_touched -->4<!--/n--> files, plus the two catalog fields and the key constant the app supplies.

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

## Check the package from a checkout

With Node 22 and the app's existing dependencies installed, run from the
repository root:

```sh
npm --prefix hook run test:package
npm --prefix hook run check:package
```

The second command packs this checkout, installs that exact tarball in a clean
temporary consumer with scripts disabled and registry access disabled, then
links only the seven current app runtime peers and React types. It checks all
public exports through the installed package's TypeScript resolution, resolves
the source entry and relative imports with the installed Metro resolver and
React Native defaults, and transforms every packed TS/TSX file with the app's
React Native Babel preset.
The file allowlist rejects keys, media, fixtures, development tools and private
app files. Both the tarball and temporary consumer are removed afterward.

This checks source-package installation with the current Vega peer types, not
a fresh registry install, native-device behavior, future peer compatibility or
npm publication. The check and sync tools are checkout-only and are not packed.
