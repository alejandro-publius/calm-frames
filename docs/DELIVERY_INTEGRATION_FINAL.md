# Delivery integration complete — October 18, 2026

The generic package review path is integrated into the active local project on
`claude/tv-experience-2026-10-16`. Source and installed app commit:
`612545932ea46f4547f594f58b2cf2b83f9134b3` (isolated implementation: `482ba4b`).
The consumer library still contains only the existing exact-approved Acadia fixture.

## Available now

- Open **http://127.0.0.1:8766** for the local intake page. After a verified export,
  Stage delivery review, Recheck delivery files and Cancel delivery review operate
  through the integrated backend. The idle owned server was refreshed once; all
  existing jobs, statuses and signer configuration were preserved.
- Staging validates package bytes, maps, original reports and exact approval identity.
  It produces a revocable operator receipt; it does not install media or enable Watch.
  The existing Acadia fixture recheck passes from this integrated checkout with
  `state: approved_for_build`, `can_watch: false`, `installed_by_staging: false`.
- The TV app is installed and left at Home with Watch focused. Native logs identify
  the same app process throughout the completed smoke. The log collector is stopped.

## Verification

**146 focused tests pass:** 55 Python intake/delivery, 32 Node approval/delivery-gate,
59 app tests. TypeScript, focused ESLint and Ruff pass. The strict built-package
check passes: four retained bundles, four original reports, 28,551,507 bytes;
only Acadia is consumer-approved. All **730 tracked app inputs** match the build.

Built once and installed once. Package:
`build/release/package-delivery-2026-10-18/calm-frames-delivery-aarch64-debug.vpkg`

SHA-256:
`f538fad6796a9f840a57ca9c86ae1794c435831f119322131570f027ba647160`

The transferred device package has the same digest. The non-capture native smoke
passed Home → Details → Watch, exact Acadia selection and `picture-shown`, playback
Back → Details Watch, Details Back → Home Details, Home Watch → playback, and natural
end → Home Watch. End-to-focus trace interval was approximately **284 ms in this run**.
The initial launch trace was absent, so that first wait stopped before any keys.
A fresh text collector then obtained trace messages from the already-running process;
there was **no second build, install or launch**.

These logs establish reported routes, focus identifiers, package selection and player
events. They do not establish visible pixels, audible output, clinical safety or a
fix for the previously observed intermittent simulator slowdown. No capture occurred.

[Receipts and logs](../results/delivery-integration-2026-10-18/README.md) include the
initial stopped wait and the completed resumed smoke. [Architecture facts](ARCHITECTURE_FACTS.md)
provide the report writer with code-backed flow, versions and cloud/local distinctions.
The earlier [package handoff](PACKAGE_DELIVERY_HANDOFF.md) documents the staging contract
and future exact-approval steps; its source-only/server status describes the earlier pass
and is superseded by this integration record.

## Owner steps

1. Directly inspect the installed app's Home/Details focus, prepared playback, covers,
   Back/end and audio. No visual/audio acceptance is recorded yet.
2. Before any new title can appear on TV, approve its exact bundle, catalog digest,
   signer fingerprint, content and consumer membership; then use the documented
   reviewed copy/generate/check/build/install workflow. Prairie remains frozen and
   outside the consumer list. No new signer or catalog was approved.
3. Finish the separately owned submission decisions: footage permission, an authorized
   demo recording and reviewer access/publication. This pass did not publish or push.

All three reserved Claude submission files match their pre-integration hashes and
were neither edited nor staged by this worker. No media, detector, threshold, signer,
trust, AWS, network, dependency or credential changes occurred during integration.
Feature work is stopped at this verified handoff.
