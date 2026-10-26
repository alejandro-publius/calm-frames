# Native acceptance, October 23

Status: blocked, not release-ready. Installed source is `cfa6610ace207ae6a39fa58be769bfb3e51ad203`, package SHA256 `a367f4c785ff64c20e7f4d3a466bf7b216be8d800fc03844246cd6f8df45cfe6`. Installed SHA384 matches. See receipt.json for exact provenance, observations and local artifact hashes.

The local branch adds three fixes to eff3ca4: exact packaged-still validation, recovered remote transport state, and Retry focus/OK ownership. The regressions failed before their fixes. No signed media, trust, submitted fallback, public video or live submission changed. No push or merge occurred.

Native observation found slow progress during resumed and fresh playback. The original eff3ca4 session completed the full five-minute scene and final-frame hold; that observation does not certify later builds. On cfa6610, explicit Retry reaches its action but refuses replacement because native synchronous teardown times out after 1.5 seconds. App-filtered logs show asynchronous teardown completion later. Treating the timeout as success would bypass the decoder ownership safeguard and is not an acceptable fix.

Next bounded engineering step: investigate native progress and decoder lifecycle using this reproduction and app-specific diagnostics. Consider a cancellable asynchronous teardown that awaits actual native completion before any replacement, with refusal on timeout and Back/background cancellation. This is a proposal, not implemented or validated here. Do not increase an acceptance threshold to hide slowness. Do not regenerate approved media or install software to diagnose it.

Background cancellation was attempted with KEY_HOME but no native background event was observed. The last Back-to-Home check expected the wrong breadcrumb `screen kid-home`; actual logs and screenshot confirm `screen home` with McWay card focus. Do not repeat Back after reaching Home. Profile switching remains untested behind the existing parent PIN; McWay has no caption track. Subjective audio, palette and full replacement-demo review remain pending.

The task-owned capture and log collectors are stopped. Simulator owner session 12233 was retained; inspect its state before any restart. The app rests on static Home. Local raw captures and logs are deliberately outside committed evidence in .logs; receipt hashes identify them. Preserve the rollback package listed in .logs/native-recovery-eff3ca4-20261023T002359964755Z/ROLLBACK.txt.
