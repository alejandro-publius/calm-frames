# Native timing and recovery: what the evidence establishes

This is the explicit limitations record for original item 9 and the remaining
native parts of items 3, 7, 10 and 11. The latest received source is
`15ef46c6e23c8ba627492da23b1b147000031aa4`; the installed Mac candidate described
by that handoff is `a672f57d333dc0e3fada51b3175ca1711d1f9397`.
Later local source changes need their own native build identity.

## Cover, seek and decoder ordering

| Boundary | Evidence available here | Exact limit |
|---|---|---|
| All app seeks use the guard | [seekSafety.ts](../../app/src/calmframes/seekSafety.ts), [useFlashGuard.ts](../../app/src/calmframes/useFlashGuard.ts), [seek guard tests](../../app/tools/seek_lint_guard.test.mjs) | Source and simulated-event checks establish request/state order. They do not timestamp physical display scanout. |
| Cover before a protected seek | The [native gaps receipt](../../results/native-acceptance-gaps-2026-10-23/receipt.json) records covered seek requests and sampled observations on its own earlier source. | A requested or sampled cover does not prove an opaque frame reached the compositor before every seek or decoded frame. No hardware timing or exhaustive compositor measurement is available. |
| Recovery confirmation | [playbackRecovery.ts](../../app/src/calmframes/playbackRecovery.ts), [RecoverablePlayback.tsx](../../app/src/calmframes/RecoverablePlayback.tsx), [native-adapter tests](../../app/test/calmframes/nativePlaybackRecovery.test.tsx) | Tests exercise seek confirmation, fresh playback progress, explicit retry and stale-session refusal. The native mock cannot prove decoder behavior between callbacks. |
| Native teardown and retained picture | [VideoHandler.ts](../../app/src/utils/VideoHandler.ts) and [scoped native async retest](../../results/native-async-retest-2026-10-23/receipt.json) | Earlier observations are source-bound. This cloud cannot observe current compositor, decoder release or Back/background timing. Missing log events are not evidence that an event did not occur. |
| Failure and retry | [Recorded native profile/retry receipt](../../results/native-profiles-retry-polish-2026-10-23/receipt.json) distinguishes its production and injected-failure harness packages. | Harness results do not turn the harness into production or establish every failure mode. Those branches remain excluded. |

The defensible claim is guarded request/state behavior with scoped native
observations and the above unmeasured timing boundaries. There is no medical
safety, seizure-prevention or universal comfort claim. Additional native timing
evidence can narrow these limits; it cannot be replaced by a passing unit test,
a frame-count estimate or a browser screenshot.

## Recovery preserves identity and protection

The [checkpoint format](../../app/src/calmframes/playbackCheckpoint.ts) binds
saved progress to the title/edition and profile. It does not carry permission to
weaken the current household floor. [Recovery tests](../../app/test/calmframes/playbackRecovery.test.ts)
and the [native adapter suite](../../app/test/calmframes/nativePlaybackRecovery.test.tsx)
exercise the source boundaries. Recorded separate positions, including through
a rename, support position isolation, not differential protection acceptance.

The [consumer caption inventory](../../results/native-acceptance-gaps-2026-10-23/catalog-caption-inventory.json)
contains no caption tracks. Restoration is implemented and tested for supported
tracks with changing native IDs; observed caption restoration cannot be claimed
for a catalog with no such tracks. Do not add unapproved media to obtain a pass.

## Retain the completed observations

- #5 remains closed within the [recorded name-editor acceptance scope](../design-polish-2026-10-23/claude-integration/README.md#item-5-names-made-up-household-1280-by-720-voiceview-on).
  The controlled failed-save check uses a named fixture, not damaged household
  storage. No repeat of that whole pass is required merely to move evidence.
- #6 production first-run navigation passed at both supported sizes. The idle
  shutdown was the device power timeout closing all applications; it is not
  reclassified as a Calm Frames crash. Disclaimer layout remains the owner's
  choice, and idle playback beyond that interval was not observed.
- #7 McWay has its recorded sustained edition and explicit final still. Other
  approved titles retain silent stills and separately selected short previews.
  No equivalent long moving Forest or Sea Otters edition is supplied. Looped or
  slowed short footage is not a substitute.
- #11 native notes retain the upstream seekbar announcement limit, intermittent
  resume-entry VoiceView behavior and unavailable reduced-motion observation.
  The cloud pause-announcement correction has its own source checks and still
  needs listening on a resulting native package.

The [handoff review](HANDOFF_REVIEW.md) states which records were received and
which detailed native ZIPs remain unavailable. Human listening, palette,
readability and comfort judgments belong to the owner.
