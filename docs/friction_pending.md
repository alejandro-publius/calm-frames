# Friction entries waiting for evkit

These are real entries from the build. They move into docs/FRICTION_LOG.md with `python -m evkit.friction add` once the head-start kits are installed, and this file is deleted after the import.

**Where the other nineteen came from, Sep 17.** docs/FRICTION_LOG.md now holds 30 entries. The eleven below are the first eleven. The other nineteen were not written here first: they were mined back out of the build itself, because the lanes hit them while working rather than while keeping notes. Each one is traceable, and here is where each came from, so nobody has to take the log on trust:

| # in the log | Where the evidence is |
|---|---|
| 12 device drops the app's logs | `app/src/calmframes/timingLog.ts` comment quoting the device's own suppression line, commit `b31a5d7` |
| 13 release builds strip `console.log` | `eval/vvd_smoke.py` docstring, CLAUDE.md, commit `f192962` |
| 14 no frame of what the app drew | `app/src/calmframes/uiCapture.ts` header, DECISIONS "stop trying to record the virtual device's screen", commit `c520e85` |
| 15 no crypto API | `app/src/calmframes/ed25519.ts` and `sha512.ts` headers, `canonicalJson.ts` for the third part, commit `c520e85` |
| 16 the build rewrites `manifest.toml` | `app/test/calmframes/manifest.test.ts` header, the 30 `[[needs.module]]` entries in `app/manifest.toml`, commits `3230b7e` and `9da186f` |
| 17 plain MP4 never starts | commit `b31a5d7`, and the root cause in docs/OPEN_SOURCE_PR.md |
| 18 a 200 instead of a 206 | `eval/vvd_timing_run.py` `send_head`, commit `b31a5d7` |
| 19 video-only stream pauses | `eval/marker_clip.py` comment on the silent track, commit `b31a5d7` |
| 20 listeners attached before the player existed | `app/src/calmframes/useCoverHarness.ts` `ready` flag and its comment, commit `b31a5d7` |
| 21 the device backgrounds an idle app | `eval/vvd_timing_run.py` keepalive, commit `b31a5d7` |
| 22 playback is not steady | GATES.md milestone notes, `results/vvd_layering_rehearsal.json`, `results/stick_day/gate1.json`, commits `0aaa9b6` and `46d8e2b` |
| 23 Shaka build needs a JDK | docs/ENVIRONMENT.md, CLAUDE.md, `.github/workflows/ci.yml` comment |
| 24 `jest --ci` exits 1 on a clean checkout | commit `e09c36f`, re-measured Sep 17 against a pristine upstream checkout |
| 25 208 gitleaks findings | commit `606d0c1` |
| 26 Theora empty packets | `flashmap/src/flashmap/decode.py` header, `flashmap/tests/test_theora.py`, commit `e654b74` |
| 27 Theora decodes wider than declared | `flashmap/src/flashmap/decode.py` around the declared size |
| 28 re-encode moves the rectangle | `flashmap/src/flashmap/analyze.py` `carried_picture`, `picture.py`, commit `d89b063` |
| 29 re-encode renumbers the first timestamp | `pipeline/verify.py` `compare_rendition_to_source`, docs/SIDECAR_SPEC.md, commit `4436eda` |
| 30 ffmpeg photosensitivity filter | `eval/baselines/run_all.py`, commit `daec5b7` |

Keep adding here as things happen. It is easier to write one down at the time than to find it again afterwards.

## 1. The installer floods logs when it isn't attached to a terminal
- **Task:** Install Vega CLI and SDK 0.24 unattended, the way CI would.
- **Steps:** Downloaded `get_vvm.sh`, ran `NONINTERACTIVE=true bash get_vvm.sh > vega_install.log 2>&1` on macOS 15.1.1 (M1), Sep 17, 2026.
- **Expected:** A short log with one line per step.
- **Actual:** Progress bars were written frame by frame. The log held 39,131 "Extracted Files: n/39131" lines plus carriage-return progress frames, 2.5 MB in total, and the version lines were buried in it. The install itself succeeded (CLI 1.3.4, SDK 0.24.9914, 4 min 18 s).
- **Severity:** Low
- **Workaround:** `tr '\r' '\n' < log | grep -v -E '\[[=-]+\]'` to recover the useful lines.
- **Suggestion:** When stdout is not a TTY, print progress only at 10% steps or at the end, as `curl` and `npm` do.

## 2. The installer edits every shell startup file with no opt-out
- **Task:** Install the Vega CLI without surprising edits to shell configuration.
- **Steps:** Same run as entry 1, with backups of `~/.zshrc` and `~/.zprofile` taken first, then diffed after.
- **Expected:** A flag to skip rc edits (like rustup's `--no-modify-path`), or an edit to only the current shell's file.
- **Actual:** `source "/Users/alexvintera/vega/env"` was appended to both `~/.zshrc` and `~/.zprofile`. The script's list also includes `.bashrc`, `.bash_profile` and `.profile`. A zsh login shell now sources the env file twice. No environment variable in the script turns this off.
- **Severity:** Low
- **Workaround:** Kept the edits; recorded them in docs/ENVIRONMENT.md.
- **Suggestion:** Add `NO_MODIFY_RC=true`, and write to one file per shell (`.zshrc` for zsh, `.bashrc` for bash).

## 3. Versioned docs root returns 404
- **Task:** Open the Vega 0.24 docs home page to find system requirements.
- **Steps:** Opened `https://developer.amazon.com/docs/vega/0.24/` (the link most guides give). Checked with `curl` on Sep 17, 2026.
- **Expected:** The 0.24 docs landing page.
- **Actual:** HTTP 404. `https://developer.amazon.com/docs/vega/latest/` is also 404, and `.../0.24/index.html` redirects to `.../0.24/index`, which is 404 too. `.../0.24/vega-get-started.html` redirects to `.../0.24/vega-get-started` and works.
- **Severity:** Low
- **Workaround:** Search the web for the page name.
- **Suggestion:** Redirect `/docs/vega/<version>/` and `/docs/vega/latest/` to the get-started page.

## 4. System requirements are split across pages
- **Task:** Confirm this Mac can run SDK 0.24 and the Vega Virtual Device before installing.
- **Steps:** Read `install-vega-sdk.html` for 0.24, then the 0.24 release notes.
- **Expected:** One table with host OS versions, CPU architectures, RAM, free disk and end-of-support dates.
- **Actual:** The install page lists macOS and Ubuntu, Homebrew, Node.js 18 or later, and KVM for Ubuntu, but no RAM, disk or CPU figures. The fact that 0.24 is the last release for Intel Macs (support ends Dec 15, 2026) is in the release notes, not on the install page. The sample repo declares Node 22 or later, stricter than the install page's Node 18.
- **Severity:** Low
- **Workaround:** Read the release notes and the sample's `package.json`.
- **Suggestion:** Put a requirements table on the install page, including the VVD's memory needs and the Intel end-of-support date, and state the Node version the samples need.

## 5. `vega virtual-device status` fails before the first start
- **Task:** Check VVD state right after installing the SDK.
- **Steps:** `vega virtual-device status` on a fresh install, before any `start`.
- **Expected:** A normal status line such as "No virtual device instance yet. Run vega virtual-device start.", exit code 0.
- **Actual:** Non-zero exit, "cannot find virtual device instance: default_instance" printed twice on one line, followed by the full internal `virtualdevice status --log-path ... --instances-path ...` command.
- **Severity:** Low
- **Workaround:** Ignore it and run `vega virtual-device start`.
- **Suggestion:** Treat "no instance" as a normal state with one clear line, and keep the internal command for `--verbose`.

## 6. `vega device list` crashes while a virtual device is running
- **Task:** List connected devices so a script can pick one.
- **Steps:** Started the Vega Virtual Device, waited for it to boot, ran `vega device list`. SDK 0.24.9914, Vega CLI 1.3.4, macOS 15.1.1 on Apple M1.
- **Expected:** A table with the running virtual device.
- **Actual:** `Vega operation FAILED due to an irrecoverable error: Cannot read properties of undefined (reading 'trim')`. The SDK error log shows `[DeviceManagerHandler]: [getDeviceList]: Error - TypeError: Cannot read properties of undefined (reading 'trim')`. Every other device command works against the same device at the same moment, including `vega device is-connected`, `vega device info`, `vega run-app` and `vega device start-log-stream`.
- **Severity:** Medium. It breaks the obvious way to script against a device, and the message gives no clue what to fix.
- **Workaround:** Use `vega device is-connected` and `vega device info` instead.
- **Suggestion:** Guard the field the parser trims, and report which device entry failed to parse.

## 7. The virtual device stops with no message in the log
- **Task:** Keep the virtual device up across a few install, launch and log-stream cycles.
- **Steps:** Started it detached, installed and launched the app twice, streamed logs, drove the remote over QMP, then ran another install about 8 minutes later.
- **Expected:** The device keeps running until it is stopped.
- **Actual:** The QEMU process was gone. `vega virtual-device status` returned `{"running":false,"process_ids":{"qemu":-1}}` and later commands failed with "Device not found". Nothing was written to the virtual device's own output after "Virtual device ready", and the host had 61% of memory free at the time.
- **Severity:** Medium. A scripted run has to check the device before every step and be ready to start it again.
- **Workaround:** `eval/vvd_smoke.py` starts the device when it is missing and waits for `vega device is-connected` rather than trusting the status command.
- **Suggestion:** Log why the device exited, and add an exit reason to `vega virtual-device status`.

## 8. `vega virtual-device status` reports running before the device can be used
- **Task:** Wait for the virtual device to be ready in a script.
- **Steps:** Started the device, then polled `vega virtual-device status` until it reported `"running":true`, then ran `vega run-app`.
- **Expected:** "running" means the device is ready for device commands.
- **Actual:** The status flips to true as soon as QEMU starts, while the guest is still booting, so `vega run-app` fails with "No connected Vega devices found". The boot takes roughly 20 more seconds.
- **Severity:** Low
- **Workaround:** Poll `vega device is-connected` instead, which only succeeds once the device is usable.
- **Suggestion:** Either hold "running" until the device is connectable, or add a separate readiness field so scripts do not have to guess.

## 9. No supported way to press a remote button or capture the screen
- **Task:** Drive the app on the virtual device from a script, and capture what it shows, to check our own screens for flashing (a requirement of this project).
- **Steps:** Looked through `vega device --help` and `vega exec vda`.
- **Expected:** Something like `vega device key dpad-down` and `vega device screenshot out.png`.
- **Actual:** Neither exists. `vega device` covers install, launch, logs, shell and port forwarding but no input or capture. The bundled device adapter is adb-derived, but the device has no `input` or `screencap` tool.
- **Severity:** Medium. Automated UI checks and screen recordings both need this.
- **Workaround:** The virtual device is QEMU with a QMP socket at `/tmp/qmp-socket-*.sock`, so `eval/vvd_control.py` sends key events with `input-send-event` and captures with `screendump`. Key injection works. Screenshots come back black, because the app renders through a GPU layer that `screendump` does not see, so playback has to be verified from device logs instead.
- **Suggestion:** Add `vega device key` and `vega device screenshot` commands, and make the screenshot capture the composited output.

## 10. No way to put a file in an app's data directory on OS 1.2
- **Task:** Push a config file into our own app's data directory, so a measurement run can start without navigating menus in front of a camera.
- **Steps:** Followed the vega-video-sample README, which says to push search data with `vega exec vda push KVATestData.json /home/app_user/packages/<package id>/data`. Tried the current equivalent, `vega device copy-to --source ... --destination /home/app_user/packages/io.github.alejandropublius.calmframes/data`, on a virtual device running OS 1.2, with the app installed and running.
- **Expected:** The file lands in the app's data directory, where the app's own `KeplerFileSystem.readFileAsString('/data/<name>')` can read it.
- **Actual:** `Permission denied`. The path does not exist either: `/home` is not on the device at all. `vega device run-cmd` runs inside the developer shell's own sandbox (`/pkgs/com.amazon.dev.shell`), which cannot see other packages' directories, so there is no path from the host to an app's data directory.
- **Severity:** Medium. The sample documents a workflow that cannot be carried out, and any app that reads a config or test fixture from its data directory has no way to be given one.
- **Workaround:** Start the run from a button inside the app instead.
- **Suggestion:** Either add `vega device copy-to --package <id>` that writes into that package's data directory in developer mode, or correct the sample README to say how it is done on OS 1.2.

## 11. `vega device copy-to` help text has source and destination backwards
- **Task:** Copy a file to a device.
- **Steps:** `vega device copy-to --help`.
- **Expected:** Source is on the host, destination is on the device.
- **Actual:** The help says `--source  Source file or directory on the device` and `--destination  Destination file or directory on the host`, which is the opposite of what the command does and of its own examples just below.
- **Severity:** Low
- **Workaround:** Follow the examples, not the option descriptions.
- **Suggestion:** Swap the two descriptions.
