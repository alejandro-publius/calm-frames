# Local video intake handoff

## What works now

A user can choose a local video, copy it into a private local workspace, analyze the entire file, and review its duration, frame count, raw flagged intervals and preset-specific covered time without playing it. Approval calls the existing prepare, verify and export pipeline only when an existing authorized signer pair is configured. Export still does not add a title to the TV app.

This pass builds on `7a18871e154dff14e40d303cbe5d333d9c1164f6` in `claude/tv-experience-2026-10-16`. The previous app source remains `3fab9998b0790c8345c2a3f82452e91a05ef4ba6`; no app inputs changed, so there was no new native build or installation. Existing approved Acadia remains the TV title. No new hardcoded title, runtime trust key, URL-based catalog or resume feature was added. Resume is deferred until newly selected titles can reach the app through reviewed delivery.

## Run on this Mac

The current local server is available at <http://127.0.0.1:8766/>. Open that address manually. It does not display or serve original or prepared video. It is an intake/review tool, not a new native TV screen.

If stopped, run from the working checkout:

```sh
cd /Users/alexvintera/calm-frames-claude-tv-2026-10-16
/Users/alexvintera/calm-frames/.venv/bin/python -m pipeline.local_intake serve   --root /Users/alexvintera/Documents/Codex/2026-10-15/task/intake-development/real-jobs   --port 8766
```

One server owns one workspace. Ctrl-C stops its active imports. The original selected file is unchanged. Cancel stops analysis/preparation but retains the copied file for retry; Remove deletes only that import's copied file and artifacts. Closing the browser does not cancel work. A crashed server cannot leave a worker publishing a completed review: the worker checks its parent and current run identity, and has a one-hour deadline independent of browser polling. Reopening the server marks unfinished runs interrupted. Each retry uses separate artifacts.

## Clean checkout

Prerequisites: Python 3.12, ffmpeg and ffprobe on PATH. This pass used Python 3.12.13 and ffmpeg/ffprobe 9.0.1. From an authorized checkout containing this change, use the repository's existing setup:

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e './flashmap[dev]'
.venv/bin/python -m pytest pipeline/tests/test_local_intake.py -q
.venv/bin/python -m pipeline.local_intake serve --root /tmp/calm-frames-local-intake --port 8766
```

These are reproducibility instructions, not commands run against a fresh environment in this pass. No key-generation command is needed for analysis/review. Do not use the broader pipeline test suite as a no-key-generation check: some pre-existing test fixtures create keys.

## Supported boundary

MP4 with an ISO/MP4 file-type header, 8-bit H.264 `yuv420p`, AAC audio, 1 to 60 fps, at most 1280 by 720, 60 seconds and 64 MiB. One active import and eight retained jobs are allowed. HDR, variable frame rate, embedded subtitles, renamed non-MP4 containers and unsupported codecs are refused. Encrypted/DRM content is outside the workflow; a file that cannot be fully decoded is a failure, never a clean pass. Use non-DRM material you own or have permission to process. These input limits are not a disk quota or a guarantee every supported-size file can produce a package within the exporter's separate 64 MiB bound.

Both WCAG and broadcast analyses cover the full decoded timeline at the analyzer's working resolution. Frame count and final timestamp are checked against the probe. The app-v1 room is 85 inches at 4 feet. Standard uses its WCAG plan; Broadcast and Extra cautious use the existing union rules. Extra cautious uses larger guard time. Review shows raw profile findings separately from padded cover intervals and total covered time. None of these numbers promises seizure prevention or medical safety.

Source, review and map identity are checked again at approval. Normal preparation re-analyzes all presets, verifies them, and must reproduce the approved interval plans before strict package export. Package verification requires original reports, signatures, exact byte hashes and source identity. The HTTP server exposes no media endpoint and accepts mutations only from its own loopback origin. This is a single-user local tool, not a hosted service or a multi-user security boundary.

## Precise signing and delivery blocker

The previous Acadia handoff records that its temporary Ed25519 private key was deleted with its directory. The public half and the already signed bundle remain. That is documentary confirmation of deletion, not a forensic search of all disks. No broader private-key search occurred, and no other signer was authorized or configured.

The smallest next decision is either to identify an existing project signer and authorize its use, or explicitly authorize creation and local storage of one project-specific Ed25519 pair outside the intake workspace and repository. Do not send the private key in chat. A local pair is enough for this bounded prototype; no cloud signing service, AWS change or credentials change is required. Creation alone would not authorize arbitrary content or automatic trust of future packages.

After such authorization, configure `serve --key /private/authorized/key.pem --pub /private/authorized/key.pub.pem`, retry preparation for the reviewed file, and inspect the actual resulting package/report. The owner then needs to approve that exact bundle's compiled app catalog membership and public verification key. The developer can implement the title-selection seam, run source checks, build/install once and validate the remote journey. The current app intentionally accepts exact reviewed bundles; possession of a public key is not sufficient. No trust registration, key generation or new-title native playback happened in this pass.

The owner also needs to choose one supported, permitted video. Existing Acadia was used only as a known test fixture; its repeated analysis is not evidence of a newly chosen title reaching TV.

## Evidence and limits

[Receipt and exact source hashes](../results/local-intake-2026-10-17/receipt.json), [HTTP checks](../results/local-intake-2026-10-17/http-results.json), [lifecycle checks](../results/local-intake-2026-10-17/lifecycle-results.json), [full-file fixture review](../results/local-intake-2026-10-17/real-job.json), and [independent review](../results/local-intake-2026-10-17/independent-review.md).

The focused Python suite passed 40 tests, including unsupported input, complete-analysis refusal, source/map/review mismatch, active import limits, cancellation/retry, stale-run publication, parent loss, deadline, existing signed package verification, wrong identity, altered media, unsigned map and missing reports. No keys are generated by this suite. Ruff passes and the HTML's JavaScript passes Node syntax checking. Independent review reran the 40 tests.

Real localhost requests verified origin rejection, no original-media route, full-file analysis of the existing Acadia source (1804 frames, 37.642 seconds), and explicit approval remaining signing-blocked. A separate owned test server verified malformed input failure, worker exit after deliberate server termination, interrupted state on restart, a fresh retry identity, cancellation and exact-job removal. No video was displayed, captured or recorded. Keyboard focus was source-reviewed; rendered keyboard usability still needs owner inspection. No signer-positive integration test or new-title TV test is claimed.

The previously installed app was left at Home with Watch focused by the preceding native pass. This pass made no native interaction, restart or installation. [Previous native receipt](../results/black-gap-2026-10-17/receipt.json) records Home/Details/More info/Back, Help/Back, both Parents cancellation returns, playback pause/resume, guarded Skip and end return. Those logs establish events, focus and selected state, not pixels, audible continuity or universal playback performance. They do not test this new intake screen or a newly imported title. Owner checks remain Home proportions, visible cover treatment, readable controls and audible continuity. The known encoded near-black opening and intermittent VVD slow-progress limitation remain separately documented.

## Three concrete Vega SDK feedback items

These are existing observed friction reports, not new repro runs. Environment: macOS Apple silicon; Vega SDK 0.24.9914, CLI 1.3.4, VVD 1.0.67506.0, aarch64 OS 1.2 (TV Ship/101520710), Node 22.23.2. Historical evidence must retain its recorded source/package version.

| Friction and evidence | Current workaround | Still unresolved and suggestion |
|---|---|---|
| Packaged `file:///pkg/...` media failed while `/pkg/...` opened. [Friction 36](FRICTION_LOG.md#36-a-packaged-filepkg-uri-is-not-opened-by-the-native-player-as-written); `app/src/utils/VideoHandler.ts`. | Normalize only at the native media boundary, preserving signed catalog identity. | SDK URI contract remains inconsistent. Accept the documented URI or document the native player form explicitly. |
| `getVideoPlaybackQuality` returned native code 50001 and frame count zero during playback. [Friction 42](FRICTION_LOG.md#42-the-player-never-reports-a-decoded-frame-on-the-virtual-device); [Oct 14 native receipt](../results/native-acceptance-2026-10-14/receipt.json), source `ac5a610`. | Opening-frame logic uses ready state, unpaused state and actual clock progress when the decoded counter is unavailable. | Counter remains unavailable on this VVD; clock progress is not proof of every rendered frame. Implement the API or expose a documented unsupported result in JavaScript. |
| Documented `vega exec inputd-cli` looked for a missing host executable yet returned exit 0. [Friction 43](FRICTION_LOG.md#43-the-documented-remote-button-command-looks-for-a-host-executable-that-is-not-there); same Oct 14 receipt. | Send `inputd-cli button_press KEY_*` through `vega device run-cmd` to the verified device. | Host command remains misleading. Correct the routing/docs and return a failure exit code when the command cannot execute. |

## Minimum owner steps

1. Open the local review page and select one supported video you have permission to process. Review its raw findings and padded interruption time without playing the original.
2. Decide whether to authorize an existing project signer or creation of a new local project-specific pair. There is no need to provide a private key in chat.
3. Once prepared, review the concrete exact-bundle/catalog proposal before app trust changes. Then the developer can finish title selection, build/install and check the native route.
4. Personally inspect the finished TV visuals and audio. Text logs cannot provide that approval.

No publication, push, release tag, cloud deployment, credentials change or edits to the three reserved submission documents occurred.
