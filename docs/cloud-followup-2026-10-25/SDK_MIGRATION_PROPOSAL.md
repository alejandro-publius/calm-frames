# Approved experiment: rejected before installation

The owner approved this bounded experiment. It was executed on isolated branch
`codex/codegen-compatibility-experiment-2026-10-25` and stopped at the first gate.
Commit `c1f57f4831d11f476b7e06d05cf7e239d2601374` introduces four new advisories,
including two critical Hermes findings, and retains the old ws fragmentation
finding. No install or native build followed. It is excluded from the candidate.
The [result](../../results/cloud-completion-2026-10-25/migration/migration-result.json)
records exact paths. No further approval is pending for this completed experiment.
The original approved scope follows for traceability.

This investigation continues checkpoint `dce5d40bc26bfc150265f971da85bbf5f605eaad`.
No canonical dependency, lockfile, SDK, exception or acceptance date changed in this pass.
The four advisories and two expired review groups still block Audit. This
proposal is a separate compatibility experiment, not a release authorization.

## What the official sources establish

The [fresh source register](../../results/cloud-completion-2026-10-25/source-access.json)
records the retrieved bytes and hashes. Amazon's public
[video sample](https://github.com/AmazonAppDev/vega-video-sample/tree/v0.24-RN83)
still has `v0.24-RN83` at `ef8e4da89b22ef7973d0d41beedfa2b42f7bb272`.
Its main and tagged package files match: React Native 0.83.0, security-manager
`~1.0.1767254405`, CLI `~0.22.7`. The resolved CLI here is already the registry's
latest 0.22.14. Updating that version would not remove the affected chain.

The official npm security-manager package's current release **and** RN83 alpha
retain `react-native-tscodegen-types: 0.66.0`. No published version in the
retrieved registry record removes that chain. The package's native module
compatibility map names the security-manager system interface; it does not
certify replacement codegen dependencies or a different device runtime.

The sample README recommends the Vega tools, JDK 21 or later, and Node 18 to 20.
That Node guidance differs from this repository's validated Node 22.23.2/npm
10.9.8 setup. It is not evidence to downgrade a checked toolchain. The dedicated
Amazon release-notes page returned proxy CONNECT 403, so newer vendor guidance
could not be established. No SDK upgrade is represented as supported here.

[Microsoft's codegen README](https://github.com/microsoft/react-native-tscodegen)
says development stopped and the work moved into React Native. The published
0.71.0 types package depends on RN 0.64.1, adds React Native type/assets packages,
and exports the same three runtime helper expressions as 0.66.0. Matching text
is not matching behavior: those expressions resolve a different React Native.
The 0.71.0 tarball was inspected after its registry SHA-512 integrity matched;
it was not installed into the candidate.

## Exact affected consumers and exposure

The [four-path analysis](REMAINING_DEPENDENCIES.md#exact-dependency-paths) and
[machine risk record](../../results/residual-dependencies-2026-10-25/residual-risk.json)
remain current:

| Advisory | Consumer that has to remain correct |
|---|---|
| GHSA-7f53-fmmv-mfjv | `security-manager-lib` -> codegen-types 0.66.0 -> nested RN 0.60.6 `Libraries/Blob/URL.js`. Codegen exports TurboModuleRegistry, codegenNativeComponent and codegenNativeCommands. |
| GHSA-rxrc-rgv4-jpvx | Nested RN's setupDevtools -> react-devtools-core 3.6.3 renderer/style bridge. No replacement bridge compatibility has been accepted. |
| GHSA-3h5v-q93c-6h6q | The old DevTools standalone server's ws 3.3.3. The ws 1.1.5 copies are outside this particular advisory range. |
| GHSA-96hv-2xvq-fx4p | ws 1.1.5 in Metro inspector, nested Metro and CLI, plus DevTools ws 3.3.3. The old handlers read removed `socket.upgradeReq.url`; a ws leaf override breaks those handlers. |

The direct application consumer is retained sample
`app/src/components/ConnectionComponent.tsx`, mounted by `SettingsScreen.tsx`.
It calls `SecurityManager.getPrivilegeState` and `requestPrivilege` before
reading network information. Removing that dependency or replacing permission
handling to clear Audit would be an application change, not a patch upgrade.

These are transitive paths of a declared app dependency, not all declared
`devDependencies`. The fbe53bf Debug and Release inventories did not contain
these vulnerable copies. Their observed installed role is the build/developer
graph. That finding does not inventory a new package or the device system
bundles, and no standalone DevTools exploit exposure was demonstrated. Findings
stay visible; none is suppressed as "development only."

## The bounded proposal

Authorize one isolated branch/worktree from the final current checkpoint to
evaluate **codegen-types 0.71.0 at the security-manager boundary**, including its
coherent RN 0.64.1 tooling subtree. This intentionally exceeds Amazon's exact
0.66.0 pin, which is why approval is required. Keep the application's RN 0.83.0,
security-manager public API, protection, media, signatures and household code.
Do not independently force ws or DevTools versions across incompatible consumers.

1. Resolve with the documented Node/npm versions. Inventory every changed
   transitive version and reject new unresolved findings. If the replacement
   does not remove the old consumers, or demands another application/framework
   migration, stop and report instead of expanding this authorization.
2. Exercise all three actual codegen exports and the security-manager TypeScript
   and Metro/system-module resolution paths. Test allowed, denied, rejected and
   retry permission responses without reading a real network name or PIN.
3. Exercise actual inspector discovery, attach/detach, peer lookup, text/binary
   forwarding, reconnect and shutdown with loopback clients. A successful npm
   install alone is not compatibility evidence.
4. Run normal typecheck, lint, app/tooling regressions, player generation and
   package checks; regenerate the three SBOMs with npm 10.9.8. Audit must retain
   its existing policy and expired-review handling. No exception renewal.
5. Review source/manifest/generated-module differences before adding the
   candidate to the consolidated native queue. Merge nothing automatically.

The risks are module-resolution changes, duplicate RN types, generated/native
interface differences and debugger protocol regressions. The native cost is
**two fresh package builds (Debug and Release)** with source-map-bound inventory,
then **one disposable-device session** checking launch/Watch/Back, permission
handling, debugger reconnect and the existing two-size regression queue. No
household reset, real PIN, repeated idle test or human comfort acceptance is
included. Cloud tests cannot replace this session.

Rollback is the unchanged current branch and its verified transfer. Discard
only the isolated experiment if its gates fail; do not reset another worktree.
For a native installation, retain and verify the existing rollback package and
install it package-scoped without clearing storage. Approval to investigate is
not acceptance of the resulting package or permission to publish it.

**Recorded decision:** the owner approved the bounded experiment. Its gate
failed, so it was not promoted. A supported vendor correction or a separately
scoped wider migration remains necessary. No risk acceptance or extension of an
expired review was requested or recorded.
