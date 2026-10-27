# Checklist 12 dependency candidate

Base: `b51c51000f74cbbe6998070cbd3879c8aca3f206`.
Branch: `codex/checklist12-host-dependencies-2026-10-27`.
Scope: dependency and CI closure only. Native UI, player, media, catalogs and
local acceptance work are unchanged. Item 12 is complete after the exact native checks recorded below; PR 21 is merged.

## What changed and why

The published security-manager package still pins codegen-types 0.66.0, whose
manifest requests React Native 0.60.6. Fresh registry checks found no vendor
release that corrects this. The previous 0.71.0 experiment remains rejected.

Inspection of the actual installed security-manager implementation,
declarations, autolink configuration, native metadata and both Hermes system
bundles found no codegen-types import. Its native binding calls Amazon's own
TurboModuleRegistry directly. The app's permission consumer is retained.
This corrects the earlier inference that the existence of codegen-types runtime
exports alone established a runtime consumer in this SDK package.

One narrowly scoped override makes codegen-types 0.66.0 resolve the already
pinned application React Native 0.83.0. The codegen package and Amazon SDK
packages are unchanged. The obsolete RN 0.60 Metro, DevTools and WebSocket
consumers disappear together. No WebSocket leaf was substituted. The original
codegen runtime exports still exist; a future SDK import would require a fresh
compatibility review and is guarded here. This is a project compatibility
candidate, not a vendor-supported release claim.

Jest's optional desktop notification dependency is now explicit at its already
fixed version, 8.0.2, so removal of the old CLI does not remove that functionality.
The actual Jest reporter and Linux, macOS argument and Windows pipe-name
consumer tests remain. They do not send a desktop notification.

The [lock delta](../results/checklist12-dependencies-2026-10-27/lock-delta.json)
removes 333 package entries, adds none and changes no retained package version.
A clean Node 22.23.2/npm 10.9.8 install succeeds. Modern SDK CLI, logkitty,
manifest parsing, decoder/Metro, body-parser and build-tool checks remain active.
Historical consumer probes run when their consumer exists; otherwise explicit
lock-and-install absence assertions replace them. The new CI guard additionally
rejects the entire retired graph. No test step or threshold was removed.

## Audit review

The four distinct findings were GHSA-7f53-fmmv-mfjv (nested RN),
GHSA-rxrc-rgv4-jpvx (old DevTools), GHSA-3h5v-q93c-6h6q (old ws headers), and
GHSA-96hv-2xvq-fx4p (old ws fragmentation). Their vulnerable installed instances
are removed, not omitted from scans. All retained versions continue to be
scanned by unmodified npm audit and scripts/dep_audit.py.

Fresh npm and both configured Python scans complete with zero findings.
The expired October 21 groups and the October 30 TOML group have no finding
left to cover. They are retired, without renewed dates or risk acceptance.
Their original text remains in Git at the base commit. The
[pre-retirement report](../results/checklist12-dependencies-2026-10-27/audit-before-exception-retirement.json)
shows zero findings while correctly failing the two expired dates. The
[current report](../results/audit.json) passes with zero exceptions. Unchanged
policy tests preserve scanner failure, new-advisory and expired-review refusal.

## Evidence and limits

- All published security-manager files match their baseline SHA-256 values,
  including system bundles, maps and native metadata. The
  [file manifest](../results/checklist12-dependencies-2026-10-27/security-manager-files.json)
  is enforced in CI.
- The actual security-manager JS and Amazon registry preserve allow, deny,
  unexpected-state refusal, propagated errors, credential-constructor
  registration and missing-native-module refusal. Only the native interface
  boundary is simulated; no real permission request is made.
- The actual Amazon CLI generates identical C++ fixture output before and after;
  [baseline hashes](../results/checklist12-dependencies-2026-10-27/codegen-files.json)
  are enforced in CI. This is code generation, not a native compilation.
- The complete React Native CLI configuration is identical after replacing
  each worktree's root path. Native dependency/autolinking maps are identical.
- The first hosted app run passed 1,955 tests and failed three image-size
  checks that still addressed the removed Metro 0.54 path. Those same asset
  assertions now exercise the current Metro 0.83 consumer; all 20 image-size
  tests pass. The adapter's malformed-input and cleanup tests remain intact.
- The connection component's nine tests and snapshot pass, as does normal
  TypeScript checking. Its Jest native mock is not native permission evidence.
- Both new guard negative controls fail as intended: restoring the old lock
  rejects the vulnerable graph; altering a recorded SDK hash rejects asset drift.
- The SBOM was regenerated with the pinned generators and npm 10.9.8. Its
  existing peer-dependency warnings remain visible; generation still uses the
  repository's unchanged lockfile policy. No new peer requirement was added.

Exact results and log hashes are in the
[validation receipt](../results/checklist12-dependencies-2026-10-27/validation.json).
The prior b51c510 native builds and nine functional CI jobs remain evidence for
the unchanged product source, not for this new dependency resolution.

## Native closure

[Exact native receipt](../results/checklist12-native-2026-10-27.json) records the
clean Mac installation, Debug/Release builds, ABI and package gates, source-bound
inventories and unchanged native/autolink/SDK assets. The actual SDK privilege
state API returned DENY in the fictional disposable Debug runtime, without a
permission request or change. Exact Release startup, approved McWay playback,
Back and explicit saved-position Resume passed. Independent read-only review
found no remaining dependency acceptance gap. PR 21 merged normally.

This validates the scoped project compatibility correction. It does not claim
vendor certification, observed native permission grant/refusal dialogs, reliable
pause speech or public redistribution permission. Debug stays private.

Primary sources checked: the npm registry records for
[@amazon-devices/security-manager-lib](https://registry.npmjs.org/@amazon-devices%2fsecurity-manager-lib)
and [react-native-tscodegen-types](https://registry.npmjs.org/react-native-tscodegen-types),
[Amazon's pinned sample](https://github.com/AmazonAppDev/vega-video-sample/blob/v0.24-RN83/package.json),
and [Microsoft's archived codegen repository](https://github.com/microsoft/react-native-tscodegen).
