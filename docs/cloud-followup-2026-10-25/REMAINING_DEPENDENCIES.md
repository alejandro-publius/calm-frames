# Five findings traced; one more compatible fix

Baseline: `cb96e21ed8db8719ce066bd7f7cdff4f583d6ca0`. The worktree was clean
and matched that exact checkpoint. Product/toolchain commit
`365be0813a8416399ada1d469b0db326d45917d4` updates the notifier; app UI,
playback, household data, import fixes, media and exception policy are unchanged.
The new audit has **4 distinct advisories: 3 high, 1 moderate**, across 9 affected
package entries. It still exits 1, with both October 21 exception groups expired.

## Exact dependency paths

All five baseline findings enter through this declared dependency chain:

```text
app
  @amazon-devices/security-manager-lib 1.0.1767254405
    react-native-tscodegen-types 0.66.0
      react-native 0.60.6 (nested, separate from app React Native 0.83.0)
```

Below, `R` means the exact directory
`app/node_modules/react-native-tscodegen-types/node_modules`.
The [machine path record](../../results/residual-dependencies-2026-10-25/baseline-paths.json)
contains unabridged paths, versions, requested ranges, immediate consumers and
the shortest chain from the root, resolved from the baseline lockfile.

| Advisory | Exact baseline vulnerable node(s) | Actual consumer and status |
|---|---|---|
| [GHSA-5fw9-fq32-wv5p](https://github.com/advisories/GHSA-5fw9-fq32-wv5p), notifier command injection | `app/node_modules/node-notifier` 5.4.5; upstream range `<8.0.1` | `R/@react-native-community/cli` 2.10.0 requests `^5.2.1`. Its `build/commands/server/messageSocket.js` calls `notify({title, message})` when no app is connected. The actual top-level Jest 29.7 reporter also resolves this optional peer. **Fixed here with 8.0.2.** The earlier report's old-Jest attribution was inaccurate. |
| [GHSA-rxrc-rgv4-jpvx](https://github.com/advisories/GHSA-rxrc-rgv4-jpvx), DevTools authorization | `R/react-devtools-core` 3.6.3; range `<4.28.4` | `R/react-native/Libraries/Core/Devtools/setupDevtools.js` calls `connectToDevTools` with the old renderer/style bridge. Fixed 4.28.4 is outside RN's `^3.6.1` request. **Unresolved:** actual renderer/bridge compatibility has not been established; no specific API break is claimed from a version number alone. |
| [GHSA-7f53-fmmv-mfjv](https://github.com/advisories/GHSA-7f53-fmmv-mfjv), RN URL regex exhaustion | `R/react-native` 0.60.6; range `>=0.59.0 <0.62.3` | The vulnerable expression is in `Libraries/Blob/URL.js:validateBaseUrl`. The codegen package requests `^0.60.6`, which excludes fixed 0.62.3. Its runtime entry exports RN's `TurboModuleRegistry`, `codegenNativeComponent` and `codegenNativeCommands`, so it cannot be treated as disposable type declarations. **Unresolved:** changing that RN line requires codegen/SDK integration validation. |
| [GHSA-3h5v-q93c-6h6q](https://github.com/advisories/GHSA-3h5v-q93c-6h6q), WebSocket header exhaustion | **Only** `R/react-devtools-core/node_modules/ws` 3.3.3; applicable range `>=2.1.0 <5.2.4` | The old standalone DevTools server uses this copy. **Unresolved:** a fixed 5.x consumer migration needs the actual standalone bridge/session exercised. The prior ledger incorrectly listed the 1.1.5 copies against this advisory; they are outside this range. |
| [GHSA-96hv-2xvq-fx4p](https://github.com/advisories/GHSA-96hv-2xvq-fx4p), WebSocket fragment exhaustion | `app/node_modules/metro-inspector-proxy/node_modules/ws` 1.1.5; `R/ws` 1.1.5; `R/react-devtools-core/node_modules/ws` 3.3.3. Applicable range `>=1.1.0 <5.2.5`. | `metro-inspector-proxy` 0.54.1, nested Metro 0.54.1, CLI 2.10.0 and DevTools 3.6.3 consume these nodes. **Demonstrated API barrier:** inspector device/debugger handlers, Metro's `attachWebsocketServer` and CLI `getpeers` read `socket.upgradeReq.url`. Fixed ws 5 passes the request separately to the connection callback and removes that property. A leaf override leaves those dereferences invalid. |

The header and fragmentation issues are two advisories, not two independent
sets of packages to count twice. The [current risk ledger](../../results/residual-dependencies-2026-10-25/residual-risk.json)
retains all four findings and corrects the header advisory's node list. Primary
advisories, registry versions, ranges and upstream patch identities are bound
in the [source register](../../results/residual-dependencies-2026-10-25/primary-source-register.json).

## Why the notifier change is bounded

The installed graph has one notifier instance. It now resolves to upstream's
fixed 8.0.2 line. Its new UUID dependency is pinned to the already-used fixed
11.1.1, so this change does not introduce the vulnerable 8.x UUID copy. No other
retained package version changes; three old private notifier dependency copies
are deduplicated. Node 22.23.2/npm 10.9.8 and the existing `.npmrc` are retained.

The [new tests](../../app/tools/notifier_dependency.test.mjs) exercise the real
CLI no-client path and the actual Jest success/failure reporter, Linux literal
argument handling including arrays, the Mac backend's arguments/callbacks, and
the UUID consumer's distinct v4 pipe names. No desktop notification, OS pipe or
native device is opened. POSIX quoting is checked with harmless literal probes
in a bounded shell with a clean environment. These are consumer tests, not an
exploit claim against the observed CLI's string-only call.

The Mac terminal-notifier executable is byte-identical before and after:
SHA-256 `2588f4ae2118396419767c388cf2b0a9a5e0cb53ce5d05a07c00f68a97a50215`.
Version 8 adds a ten-second default for a Mac notice without an explicit timeout;
the test records that behavior. Jest's explicit `timeout: false` retains its
meaning. This developer notification is unrelated to Fire TV player timing or
media budgets. Native notification delivery itself was not tested here.

The first npm resolution retained a new UUID 8.3.2 child despite the requested
override. The consumer test rejected it. Resolving the lock without that stale
node and installing it cleanly now uses only UUID 11.1.1. No advisory was hidden
or relabelled to make the check pass.

## Where the remaining migration paths stop

**SDK / nested RN:** the currently published security-manager package still pins
codegen-types 0.66.0. The registry's newer codegen-types 0.71.0 pins RN 0.64.1 and
adds other type/assets packages. That is a wider SDK code-generation change,
not a compatible patch to the existing request. Stop before replacing that graph
or the app's unrelated RN 0.83.0 runtime. The preferred next input is an
SDK-supported package update or explicit authorization for a separate codegen
migration with native build/system-bundle acceptance.

**DevTools / WebSockets:** a coordinated migration must preserve device discovery,
debugger attachment, peer lookup, message/binary handling, reconnect and shutdown.
The three actual `upgradeReq` consumers need changes before using fixed ws 5;
the standalone DevTools session needs its own compatibility evidence. A blind
global ws override is rejected. This pass does not fork the inspector or claim
that untested bridge versions work. A separate supported tooling migration is
the next option, with focused local protocol checks followed by the required
SDK/device integration observations.

**Exposure classification:** these paths are pulled through a declared app
dependency, so calling them all `devDependencies` would be inaccurate. The
received fbe53bf Debug/Release inventories did not contain these vulnerable
copies; their immediate observed role is the installed development/build graph.
That inventory does not establish a newer package or device system bundles.
The DevTools advisory's primary fix targets browser-extension privilege paths;
exploit applicability to this standalone backend was not demonstrated. The
scanner finding stays present, with no suppression or renewed acceptance.

No owner decision is needed to retain the completed notifier fix. Any decision
to broaden into the above migrations should be separate from release approval.
Until those findings and expired reviews are resolved, Audit remains blocking.
The single [native checklist](NATIVE_VERIFICATION.md) retains all outstanding
product checks for the latest source. Media plans remain plans; no footage,
narration, manga, publication or submission change occurred.
