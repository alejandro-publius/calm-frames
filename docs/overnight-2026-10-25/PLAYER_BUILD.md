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
The integration owner is handling those audit files separately; player setup did
not modify them.

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

Restore only into a separate checkout of the declared source after its own
locked install. Verify the recorded build-script and patch hashes first. Do not
overwrite any tracked file, especially the custom `ShakaPlayer.ts`, which is
absent from the ZIP. Run the normal native-input preflight after restore. The
repository's `npm run setup:player` remains the normal regeneration path.

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
