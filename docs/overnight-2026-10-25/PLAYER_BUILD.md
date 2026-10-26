# Generated player inputs

The normal player setup completed from source
`596418e64e83f724c5c9e4a5b34122746aec11e4` in a fresh isolated worktree.
The ordinary native-input preflight now reports `ready`.
This establishes generated build inputs, not a native package or accepted playback.
The [receipt](../../results/overnight-2026-10-25/player-build/receipt.json)
records the exact source, commands, tool versions, logs and transfer checksum.
The [checks record](../../results/overnight-2026-10-25/player-build/checks.json)
also preserves an unrelated number-sync failure in this source snapshot:
`docs/SECURITY.md` has a stale app component count relative to `results/sbom.json`.
That historical mismatch is corrected in the integrated presentation at
`6bbb362`; the [final checks](FINAL_VALIDATION.md) include number synchronization.
Player setup did not modify those audit files.

## Executed path

The lane used its own locked app installation, Node 22.23.2, npm 10.9.8 and
OpenJDK 21.0.12.1. These commands ran in `app/`:

```sh
npm ci --ignore-scripts --no-audit --no-fund
npm run setup:player
npm run check:native-inputs
```

The unchanged setup script cloned Shaka's pinned version, applied the tracked
Amazon patches, and used its existing direct Python/JDK fallback when `kepler`
was unavailable. The current allowed network path completed without a domain
denial. The older codeload failure in historical status notes is not the outcome
of this attempt. No network policy, dependency, lockfile or source fix was used
to make the build pass.

The custom tracked `app/src/w3cmedia/shakaplayer/ShakaPlayer.ts` stayed unchanged.
Generated files remain ignored or outside the source checkout. AppleDouble and
Finder metadata emitted by the vendor copy step were inventoried and moved into
the external evidence directory; they are excluded from the transfer archive.

## Optional reusable inputs

The external artifact is
`/workspace/shared/calm-frames-overnight-player-build-2026-10-25/calm-frames-generated-player-inputs-596418e.zip`.
It contains only the generated compiled player, required polyfills,
`PlayerInterface.ts`, a provenance/restore manifest and retained license texts.
It contains no native package, SDK, node_modules, source maps, upstream docs,
household data or signing keys.

Use the ZIP size and SHA-256 in the
[receipt](../../results/overnight-2026-10-25/player-build/receipt.json), then check
each restored file against
[GENERATED_PLAYER_INPUTS.json](../../results/overnight-2026-10-25/player-build/GENERATED_PLAYER_INPUTS.json).
That manifest lists every destination, upstream tag and patch identity,
toolchain, license text and its hash. It also references the existing
[sample-license notice review](../AMAZON_SAMPLE_LICENSE_REVIEW.md); this build
does not settle that recorded notice discrepancy or authorize publication.

The integration owner independently verified every archived byte and every
recorded build-input hash against the final product source `b603be9`. The
[reuse receipt](../../results/overnight-2026-10-25/final/generated-input-reuse.json)
records the restore and normal preflight, typecheck and lint pass. Later app
changes do not alter these player-generation inputs; this does not make the ZIP
a native package for that later source.

Restore only into a clean separate checkout of the full transfer SHA after its
own locked install. The [restore helper](restore_generated_player.py) requires
that exact HEAD, the exact ZIP checksum and matching build-input hashes. It
refuses tracked files, linked destinations and differing existing inputs before
writing anything. Its [boundary checks](../../results/overnight-2026-10-25/final/final-restore-helper.json)
include refusal and idempotent restore. Follow the [Mac handoff](MAC_HANDOFF.md),
then run the normal native-input preflight. The custom tracked `ShakaPlayer.ts`
is absent from the ZIP. `npm run setup:player` remains the normal regeneration
path if build inputs later change.

The [complete generated-file inventory](../../results/overnight-2026-10-25/player-build/generated-file-inventory.json)
also records artifacts omitted from this small archive. The generated binaries
themselves are not committed.

## Native boundary

The installed CLI module's own
[SDK discovery](../../results/overnight-2026-10-25/player-build/native-sdk-probe.json)
could not find `vega` or `kepler`; `KEPLER_SDK_PATH` is unset. Its build command
requires that external tool, so no native compilation was attempted. No
simulator, install, signing, package publication or human review occurred.

The Mac acceptance handoff still needs the matching Vega SDK, an exact-source
native package and the separate focus, footer, protection/recovery, audio and
comfort observations. A ready input preflight cannot substitute for them.
