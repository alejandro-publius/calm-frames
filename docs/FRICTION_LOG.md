# Friction log

Developer friction found while building Calm Frames, in the six fields Amazon asks for: task, steps, expected versus actual, severity, workaround, suggestion.

Everything here is real. Each entry is something that cost time on this build, with the exact commands and the exact output, and each one is traceable to a commit, a log, a results file or an entry in [`docs/DECISIONS.md`](DECISIONS.md). **Nothing was invented to reach a number, and nothing was softened.** Where we are stating a platform constraint we designed around rather than a failure we watched happen, the entry says so in its own words.

**This file is the log, and it is the only one.** There used to be a second file beside it, `docs/friction_pending.md`, which the lanes jotted into while working. Two mock judges said in a row that shipping a scratch pad next to the real log invites a reader to mistake one for the other, and they were right, so it is gone: its drafts had already become entries 1 to 11 here, and what it kept that was worth keeping, a table saying where the evidence for each later entry lives, is now at the end of this file. The shorter, per-tool version of this material is [`docs/FEEDBACK.md`](FEEDBACK.md), and that is what goes into the Devpost product feedback.

**Environment for every entry unless the entry says otherwise:** macOS 15.1.1 (24B91) on Apple M1, 16 GB. Vega CLI 1.3.4, Vega SDK 0.24.9914, Vega OS 1.2 (TV Ship/101520710) on the Vega Virtual Device, Node 22.23.2, Python 3.12.13, React Native 0.83, September 17 2026.

## Summary

| # | Area | What broke | Severity |
|---|---|---|---|
| 1 | Installer | Progress bars flood a non-TTY log | Low |
| 2 | Installer | Edits every shell startup file, with no opt-out | Low |
| 3 | Docs | Versioned docs root returns 404 | Low |
| 4 | Docs | System requirements split across pages, and inconsistent | Low |
| 5 | CLI | `vega virtual-device status` fails before the first start | Low |
| 6 | CLI | `vega device list` crashes with a TypeError | Medium |
| 7 | Virtual device | Stops with nothing written to the log | Medium |
| 8 | CLI | `status` reports running before the device is usable | Low |
| 9 | CLI | No supported way to press a remote button or capture the screen | Medium |
| 10 | Device | No way to put a file in an app's data directory on OS 1.2 | Medium |
| 11 | CLI | `copy-to` help text has source and destination backwards | Low |
| 12 | Device | The device drops the app's own log output under load | High |
| 13 | Build | Release builds strip `console.log` | Low |
| 14 | Device, React Native | No way to get a frame of what the app drew, from inside or outside | High |
| 15 | Platform | No crypto API, so signature checking had to be written by hand | High |
| 16 | Build | The build rewrites `manifest.toml` on every build | Medium |
| 17 | Player | A plain MP4 over HTTP never starts, and never errors | Medium |
| 18 | Player | A server that answers 200 instead of 206 makes the player fail in silence | Medium |
| 19 | Player | A video-only stream pauses a few seconds in | Medium |
| 20 | Player, sample | The media element does not exist at mount, and nothing says when it does | Medium |
| 21 | Virtual device | It backgrounds an app nobody is touching, and playback stops | Medium |
| 22 | Virtual device | Playback is not steady, and the error says `UNKNOWN` | High |
| 23 | Sample | `postinstall` builds Shaka Player from source and needs a JDK | Low |
| 24 | Sample | `jest --ci` exits 1 on a clean checkout with every test passing | Low |
| 25 | Sample | Its dependency tree buries a secret scan in 208 findings | Low |
| 26 | Player, docs | `timeupdate` cadence and `currentTime` resolution are undocumented | High |
| 27 | React Native | `setNativeProps` throws on 0.83, so every piece of UI has to be state-driven | Low |
| 28 | Captions, docs | The z-order contract is undocumented, and there is one captions view per process | Low |
| 29 | Toolchain | Ogg Theora duplicate-frame packets kill the decoder | Medium |
| 30 | Toolchain | Theora decodes wider than the size the file declares | Low |
| 31 | Toolchain | Re-encoding moves the picture rectangle, which moves every area fraction | Medium |
| 32 | Toolchain | A re-encode renumbers the first timestamp, so the rendition slides | Medium |
| 33 | Toolchain | The ffmpeg photosensitivity filter misfires on its own first second | Low |
| 34 | Local automation | Sandbox blocks Jest's Watchman socket and Python HTTP listeners | Low |
| 35 | GitHub automation | All Audit jobs fail before a runner or step starts | High |
| 36 | Player | A packaged `file:///pkg/...` URI is not opened by the native player | High |
| 37 | Captions | The native caption view cannot be stacked above an RN image by z-index | High |
| 38 | Virtual device | Capture can return an older GPU frame; a static screen records few frames | Medium |
| 39 | Build tooling | Custom fonts render as the fallback unless they sit in `assets/fonts` | Low |
| 40 | React Native | Disabling a focused control drops native focus | Medium |
| 41 | Device, React Native | `Image` refuses a data URI, so a signed still showed black on the device | High |
| 42 | Player | `getVideoPlaybackQuality` fails below JavaScript on the virtual device, so no frame is ever counted | High |
| 43 | CLI, docs | The documented `vega exec inputd-cli` looks for a host executable that is not there | Medium |
| 44 | Device | The image loader logs an error for every packaged image, and then loads it | Low |

**Forty-four entries. Ten High, sixteen Medium, eighteen Low.**

**Entries 1 to 28 and 36 to 44 are on Amazon's surface**: the installer, the documentation, the CLI, the virtual device, the device itself, the build tooling, the player, the captions view and `vega-video-sample`. **Entries 29 to 33 are the wider toolchain**, mostly ffmpeg and PyAV, and they are here because they cost this build real time and two of them changed what the analyzer computes. **Entries 34 and 35 are restricted local automation and GitHub Actions startup, not Amazon issues.** They are marked separately so nobody has to guess which are Amazon's.

Nothing in entries 1 to 33 blocked the build outright, because every one of them had a way around it; 36 and 37 did stop playback and captions on the device until their workarounds were found, and on Oct 14, 41 and 42 did the same: the hold still showed black and every playback ended on a recovery screen until theirs. The first five High entries are the ones where there was no supported path, or no documented answer, and what we needed had to be built or measured from scratch: the device throwing away our measurement evidence (12), no way to see our own screens (14), no crypto API for checking a signature (15), playback on the virtual device being unsteady enough that a measurement needs twenty-two launches (22), and the player's position reporting being undocumented when the whole design has to act at a precise media time (26). Entry 35 records a historical startup block; runners resumed by October 5. The Audit failures between then and Oct 11 were dependencies and bills of materials, not runner startup, and the Oct 11 push is green.

Three entries say plainly that they are a platform rule we adopted and designed around rather than a failure we watched: 13, 27 and 28. They are in the log because each one shaped the build and each cost time to establish, and they are labelled so that nobody reads them as a crash we saw.

---

## 1. The installer floods logs when it is not attached to a terminal

**Task.** Install the Vega CLI and SDK 0.24 unattended, the way CI would.

**Steps.** Downloaded `get_vvm.sh`, then ran:

```sh
NONINTERACTIVE=true bash get_vvm.sh > vega_install.log 2>&1
```

**Expected.** A short log with one line per step.

**Actual.** Progress bars were written frame by frame. The log held 39,131 `Extracted Files: n/39131` lines plus carriage-return progress frames, 2.5 MB in total, and the version lines were buried in it. The install itself succeeded: CLI 1.3.4, SDK 0.24.9914, in 4 minutes 18 seconds.

**Severity.** Low.

**Workaround.** Recover the useful lines afterwards:

```sh
tr '\r' '\n' < vega_install.log | grep -v -E '\[[=-]+\]'
```

**Suggestion.** When stdout is not a TTY, print progress only at 10 percent steps or at the end, the way `curl` and `npm` do.

---

## 2. The installer edits every shell startup file with no opt-out

**Task.** Install the Vega CLI without surprising edits to shell configuration.

**Steps.** Same run as entry 1, with backups of `~/.zshrc` and `~/.zprofile` taken first, then diffed after.

**Expected.** A flag to skip rc edits, the way rustup has `--no-modify-path`, or an edit to only the current shell's file.

**Actual.** `source "/Users/<user>/vega/env"` was appended to both `~/.zshrc` and `~/.zprofile`. The script's list also includes `.bashrc`, `.bash_profile` and `.profile`. A zsh login shell now sources the env file twice. No environment variable in the script turns this off.

**Severity.** Low.

**Workaround.** Kept the edits and recorded them in `docs/ENVIRONMENT.md` so the next person knows where they came from.

**Suggestion.** Add `NO_MODIFY_RC=true`, and write to one file per shell: `.zshrc` for zsh, `.bashrc` for bash.

---

## 3. Versioned docs root returns 404

**Task.** Open the Vega 0.24 docs home page to find system requirements.

**Steps.** Opened `https://developer.amazon.com/docs/vega/0.24/`, the link most guides give. Checked with `curl` on September 17 2026.

**Expected.** The 0.24 docs landing page.

**Actual.** HTTP 404. `https://developer.amazon.com/docs/vega/latest/` is also 404, and `.../0.24/index.html` redirects to `.../0.24/index`, which is 404 too. `.../0.24/vega-get-started.html` redirects to `.../0.24/vega-get-started` and works.

**Severity.** Low.

**Workaround.** Search the web for the page name instead of navigating from the root.

**Suggestion.** Redirect `/docs/vega/<version>/` and `/docs/vega/latest/` to the get-started page.

---

## 4. System requirements are split across pages, and the versions disagree

**Task.** Confirm this Mac could run SDK 0.24 and the Vega Virtual Device before installing anything.

**Steps.** Read `install-vega-sdk.html` for 0.24, then the 0.24 release notes, then the sample's `package.json`.

**Expected.** One table with host OS versions, CPU architectures, RAM, free disk and end-of-support dates.

**Actual.** Three problems at once. The install page lists macOS and Ubuntu, Homebrew, Node.js 18 or later, and KVM for Ubuntu, but no RAM, disk or CPU figures. The fact that 0.24 is the last release for Intel Macs, with support ending December 15 2026, is in the release notes and not on the install page. And the sample repository declares Node 22 or later, which is stricter than the install page's Node 18, so following the install page gives you a Node that the samples reject.

**Severity.** Low. It is a research cost rather than a blocker, but it is the first thing a new developer hits.

**Workaround.** Read the release notes and the sample's `package.json` as well as the install page.

**Suggestion.** Put a requirements table on the install page, including the virtual device's memory needs and the Intel end-of-support date, and state the Node version the samples actually need.

---

## 5. `vega virtual-device status` fails before the first start

**Task.** Check the virtual device's state right after installing the SDK.

**Steps.**

```sh
vega virtual-device status      # on a fresh install, before any start
```

**Expected.** A normal status line such as "No virtual device instance yet. Run vega virtual-device start.", with exit code 0.

**Actual.** Non-zero exit, with `cannot find virtual device instance: default_instance` printed twice on one line, followed by the full internal `virtualdevice status --log-path ... --instances-path ...` command.

**Severity.** Low.

**Workaround.** Ignore it and run `vega virtual-device start`.

**Suggestion.** Treat "no instance" as a normal state with one clear line, and keep the internal command behind `--verbose`.

---

## 6. `vega device list` crashes while a virtual device is running

**Task.** List connected devices so a script can pick one.

**Steps.** Started the Vega Virtual Device, waited for it to boot, then:

```sh
vega device list
```

**Expected.** A table with the running virtual device in it.

**Actual.**

```
Vega operation FAILED due to an irrecoverable error: Cannot read properties of undefined (reading 'trim')
```

The SDK error log shows `[DeviceManagerHandler]: [getDeviceList]: Error - TypeError: Cannot read properties of undefined (reading 'trim')`. Every other device command works against the same device at the same moment, including `vega device is-connected`, `vega device info`, `vega run-app` and `vega device start-log-stream`.

**Severity.** Medium. It breaks the obvious way to script against a device, and the message gives no clue what to fix.

**Workaround.** Use `vega device is-connected` and `vega device info` instead. Every script in this repository does.

**Suggestion.** Guard the field the parser trims, and report which device entry failed to parse.

---

## 7. The virtual device stops with no message in the log

**Task.** Keep the virtual device up across a few install, launch and log-stream cycles.

**Steps.** Started it detached, installed and launched the app twice, streamed logs, drove the remote over QMP, then ran another install about 8 minutes later.

**Expected.** The device keeps running until it is stopped.

**Actual.** The QEMU process was gone. `vega virtual-device status` returned `{"running":false,"process_ids":{"qemu":-1}}` and later commands failed with "Device not found". Nothing was written to the virtual device's own output after "Virtual device ready", and the host had 61 percent of its memory free at the time.

**Severity.** Medium. A scripted run has to check the device before every step and be ready to start it again.

**Workaround.** `eval/vvd_smoke.py` starts the device when it is missing, and waits for `vega device is-connected` rather than trusting the status command.

**Suggestion.** Log why the device exited, and add an exit reason to `vega virtual-device status`.

---

## 8. `vega virtual-device status` reports running before the device can be used

**Task.** Wait for the virtual device to be ready, in a script.

**Steps.** Started the device, polled `vega virtual-device status` until it reported `"running":true`, then ran `vega run-app`.

**Expected.** "running" means the device is ready for device commands.

**Actual.** The status flips to true as soon as QEMU starts, while the guest is still booting, so `vega run-app` fails with "No connected Vega devices found". The boot takes roughly 20 more seconds.

**Severity.** Low.

**Workaround.** Poll `vega device is-connected` instead, which only succeeds once the device is usable.

**Suggestion.** Either hold "running" until the device is connectable, or add a separate readiness field so scripts do not have to guess.

---

## 9. No supported way to press a remote button or capture the screen

**Task.** Drive the app on the virtual device from a script, and capture what it shows. Capture matters for this project in particular, because Calm Frames has to check its own screens and transitions for flashing.

**Steps.**

1. Read every verb the CLI has for a device:

   ```sh
   vega device --help
   ```

2. Read the bundled device adapter's own help, since it is adb-derived and adb has both an input and a capture command:

   ```sh
   vega exec vda --help
   ```

3. Looked for those two adb tools on the device itself, through the developer shell (`vega device run-cmd`).

**Expected.** Something like `vega device key dpad-down` and `vega device screenshot out.png`.

**Actual.** Neither exists. `vega device` covers install, launch, logs, shell and port forwarding, but no input and no capture. The bundled device adapter is adb-derived, but the device has no `input` or `screencap` tool.

**Severity.** Medium. Automated UI checks and screen recordings both need this, and for an accessibility project the screen capture is not optional.

**Workaround.** The virtual device is QEMU with a QMP socket at `/tmp/qmp-socket-*.sock`, so `eval/vvd_control.py` sends key events with `input-send-event` and captures with `screendump`. Key injection works. Screenshots do not; see entry 14. This is an undocumented interface and it could change between SDK versions. Since Oct 9 the device's own `inputd-cli`, reached through `vega device run-cmd`, is the better route for keys; entry 43 has it and the documented spelling that fails.

**Suggestion.** Add `vega device key` and `vega device screenshot`, and make the screenshot capture the composited output rather than the framebuffer the app does not draw into.

---

## 10. No way to put a file in an app's data directory on OS 1.2

**Task.** Push a config file into our own app's data directory, so a measurement run can start without navigating menus in front of a camera.

**Steps.** Followed the `vega-video-sample` README, which says to push search data with `vega exec vda push KVATestData.json /home/app_user/packages/<package id>/data`. Tried the current equivalent on a virtual device running OS 1.2, with the app installed and running:

```sh
vega device copy-to --source ./calm-frames-harness.json \
  --destination /home/app_user/packages/io.github.alejandropublius.calmframes/data
```

**Expected.** The file lands in the app's data directory, where the app's own `KeplerFileSystem.readFileAsString('/data/<name>')` can read it.

**Actual.** `Permission denied`. The path does not exist either: `/home` is not on the device at all. `vega device run-cmd` runs inside the developer shell's own sandbox at `/pkgs/com.amazon.dev.shell`, which cannot see other packages' directories, so there is no path from the host into an app's data directory.

**Severity.** Medium. The sample documents a workflow that cannot be carried out, and any app that reads a config or a test fixture from its data directory has no way to be given one.

**Workaround.** Start the run from a button inside the app instead. The app now fetches its run config over HTTP at startup, which also works on the stick.

**Suggestion.** Either add `vega device copy-to --package <id>` that writes into that package's data directory in developer mode, or correct the sample README to say how it is done on OS 1.2.

---

## 11. `vega device copy-to` help text has source and destination backwards

**Task.** Copy a file to a device.

**Steps.**

```sh
vega device copy-to --help
```

**Expected.** Source is on the host, destination is on the device.

**Actual.** The help says `--source  Source file or directory on the device` and `--destination  Destination file or directory on the host`, which is the opposite of what the command does, and the opposite of its own examples printed just below.

**Severity.** Low.

**Workaround.** Follow the examples, not the option descriptions.

**Suggestion.** Swap the two descriptions.

---

## 12. The device throws away the app's own log output under load

**Task.** Collect the evidence for a cover timing run. The app prints one line per event, pairing media time with wall-clock time, and the plan was to read them out of the device log:

```sh
vega device start-log-stream | grep CALM_TIMING
```

**Steps.** Built and installed the debug package, started the timing harness on the virtual device, and streamed the device log for the length of the run while a two-minute clip played.

**Expected.** One line per event in the stream: media events, cover on, cover off, position reports.

**Actual.** Nothing the app printed survived. The device log instead carried:

```
Log suppression ended at level [info]. [140] logs were suppressed
```

A run that produced covers, position reports and errors produced no readable record of any of it. The suppression is reported after the fact and there is no way to ask for it back.

**Severity.** High. A measurement whose evidence can be deleted by a log rate limiter is not a measurement. This is the one that cost the most rework in the measurement chain.

**Workaround.** Two changes. Timing lines now print with `console.warn`, which survives more than `console.log` does. More to the point, the evidence no longer goes through the device log at all: `eval/vvd_timing_run.py` serves the clip and the run config over HTTP and collects the events the app posts back to it, and `results/*_events.json` is what the analysis reads. The device log is a convenience now, never the evidence.

**Suggestion.** Document the rate limiter and its thresholds. Give developer mode one level that is never suppressed, or a switch that turns suppression off for a named package. If lines must be dropped, say so at the moment of dropping, with the count, rather than afterwards.

---

## 13. Release builds strip `console.log`

**Task.** Watch what the app is doing during a run on the device.

**Steps.** Built both packages, `react-native build-kepler --build-type Release` and `--build-type Debug`, and installed the debug one for every run where the app's own output mattered.

**Expected.** The app's own log lines, whichever package is installed.

**Actual.** `console.log` does not survive a release build. This is a platform behaviour we designed around from the first device run rather than a failure we sat and watched: every observed run in this project installs the debug package for that reason, `eval/vvd_smoke.py` says so in its own docstring, and the timing log uses `console.warn` rather than `console.log` partly because of it. We did not do a controlled side by side, so this entry is a constraint with a cost rather than a bug report.

**Severity.** Low. It is reasonable behaviour. The cost is that it is not stated where a developer plans their evidence, and it stacks with entry 12: one mechanism strips your lines at build time and another drops them at run time, and neither says so at the moment it matters.

**Workaround.** Install the debug package for anything that has to be observed, and use `console.warn` for lines that have to survive.

**Suggestion.** State on the build page which console levels survive a release build, and mention it next to the logging documentation rather than only in the build documentation.

---

## 14. There is no way to get a frame of what the app drew, from inside it or outside it

**Task.** Check Calm Frames' own screens and transitions for flashing. This is not optional for us: WCAG 2.3.1 applies to an app's own interface, and an app that hides flashing in other people's video while flashing its own cards would be absurd.

**Steps.** Four routes, in order.

1. `vega device screenshot`. Does not exist (entry 9).
2. QEMU's `screendump` through the QMP socket, which `eval/vvd_control.py` drives.
3. A screen capture of the virtual device's window from macOS, with ffmpeg and with the system screen grab.
4. A pixel read from inside the app: `takeSnapshot` in React Native, or any `@amazon-devices` package that offers a view capture or frame grab.

**Expected.** At least one of the four gives a picture of the running app.

**Actual.** None of them does.

- `screendump` writes a file and the file is black. The app renders through a GPU layer that the framebuffer capture does not see.
- macOS exposes no screen capture device to ffmpeg without the Screen Recording permission, and the window is not captured anyway: a full screen grab taken while the virtual device was frontmost returned the desktop behind it.
- React Native 0.83 has no `takeSnapshot`. It was removed from core and nothing in `node_modules/react-native` exposes a pixel read.
- No `@amazon-devices` package offers a screenshot, a view capture or a frame grab. The only match anywhere across them is `readPixels` inside a Flow type stub for the DOM, which is a type declaration and not a runtime.

**Severity.** High. It changed the design of a whole deliverable, and it means no visual evidence of this app exists that was taken from a screen rather than reconstructed.

**Workaround.** The app records what it paints instead of what it displays. Every Calm Frames screen reports its own frame, the colour behind the whole screen and the distinct colours painted on top, read off the rendered tree rather than written down by hand, so a style change shows up in the record. `tools/ui_flashmap.mjs` turns that timeline into a lossless video, giving every painted colour a block one WCAG area window wide so the analyzer overstates area rather than understating it, and the same analyzer we point at content is pointed at that. Nine screens, zero flagged segments, checked in CI. A test fails if a declared frame drifts from what renders. It is a real record of the app's own drawing, including every transition, and it is not a photograph, and we say so everywhere it is quoted.

**Suggestion.** Make `vega device screenshot` capture the composited output. Separately, expose a view capture from inside the app, even a slow one, because self-testing an interface should not need a camera.

---

## 15. Vega has no crypto API, so a signature check had to be written by hand

**Task.** Verify an Ed25519 signature on a flash map before letting a title play. A map that is unsigned, stale or bound to a different file has to leave the picture hidden, and that decision has to be made on the device.

**Steps.** Looked for a way to verify a signature or hash bytes: WebCrypto in React Native 0.83, Node's `crypto`, and every `@amazon-devices` package in the sample's dependency tree, including `security-manager-lib`.

**Expected.** Something like `crypto.subtle.verify`, or a platform key store with a verify call.

**Actual.** Nothing. React Native has no WebCrypto and no `crypto` module. `@amazon-devices/security-manager-lib` deals in privileges rather than primitives. So an app that ships signed data has no supported way to check the signature.

**Severity.** High. Hand-written cryptography in an application is the last thing anyone should want, and the platform left no other option.

**Workaround.** SHA-512 and Ed25519 verification, written in TypeScript on BigInt, following FIPS 180-4 and RFC 8032 section 5.1.7 with the strict checks: a non-canonical point encoding is refused, a scalar at or above the group order is refused, and the cofactorless equation is the one that has to hold. Checked against the RFC 8032 test vectors and against a real map signed by our own pipeline. Being stricter than the signer can only ever refuse a map, and refusing a map keeps the picture hidden, which is the safe direction. It runs once per title before play starts, never on the path of a frame. A third piece was needed as well: `JSON.parse` followed by `JSON.stringify` cannot rebuild the bytes Python signed, because parsing throws away how a number was written and Python's `1450.0` comes back as `1450`, so the parser keeps each scalar's source text.

**Suggestion.** Expose a verify-only primitive: SHA-256, SHA-512 and Ed25519 or ECDSA verification, in a Vega module. Signed content is normal on a television platform, and every app that handles it is otherwise writing this same code.

---

## 16. The build rewrites `manifest.toml` on every build

**Task.** Keep the app's manifest saying what the app actually needs, and keep two load-bearing blocks in it.

**Steps.** Removed the sample's service and task components, removed the five npm dependencies those features needed, then built with `react-native build-kepler` and read the manifest afterwards.

**Expected.** The manifest is our file. The build reads it.

**Actual.** The build rewrites it, adding one `[[needs.module]]` entry per installed `@amazon-devices` package. Our manifest carries 30 of them today. Two consequences. First, removing a feature means removing its dependency too, or the app goes on declaring it needs a module for a feature it no longer has: we kept `kepler-content-personalization` and `kepler-epg-provider` because the personalization mocks still need them, and the manifest still declares both. Second, anything hand-written in that file lives under a tool that rewrites it, and two of the hand-written blocks are ones the app breaks quietly without: the `IMediaPlaybackServer` extras block, which is how Alexa and remote transport commands reach the app at all, and the `com.amazon.devconf.privilege.accessibility` privilege, without which no VoiceView announcement is made.

**Severity.** Medium.

**Workaround.** `app/test/calmframes/manifest.test.ts` fails if either block goes missing, and the pristine manifest is at commit `cf8b752` if it has to be restored by hand.

**Suggestion.** Say in the build documentation that the manifest is rewritten and which sections the tool owns. Better, keep the generated `[[needs.module]]` list in a separate generated file that the build merges, so the hand-written manifest is never touched.

---

## 17. A plain MP4 over HTTP never starts, and never says why

**Task.** Play our own two-minute marker clip on the device, served from the machine running the measurement.

**Steps.** Served `media/markers.mp4` over plain HTTP from a local server, pointed the app at the URL, and watched both the device log and the app's own event stream.

**Expected.** It plays, or it fails with an error the app can show.

**Actual.** Neither. Playback never started and no error arrived: no `error` event, no error view, and the buffering spinner stayed up. The same content over HLS plays. Two separate things are going on. The player will not take a raw MP4 handed to the adaptive path, and the sample sends anything whose `format` is not the exact literal `"MP4"` down that path. And the failure is swallowed rather than reported, which is a defect in the sample itself: `ShakaPlayer.load()` is declared `void` and fires its async work unawaited, so the rejection becomes an unhandled rejection and the caller's `try`/`catch` can never see it.

**Severity.** Medium. It cost a day, because a spinner that never stops looks like a network problem rather than a load failure.

**Workaround.** Package the clip as HLS, copying the stream rather than re-encoding it, so the marker times still hold. For the silent failure, we wrote the fix: two commits and three tests against `AmazonAppDev/vega-video-sample`, ready to open from a fork, in [`docs/OPEN_SOURCE_PR.md`](OPEN_SOURCE_PR.md) and [`docs/upstream-pr/`](upstream-pr/).

**Suggestion.** Report a load failure to the app. That is the upstream fix. Separately, document which containers and protocols the player accepts on which path, because "MP4 over HTTP" is what every developer will try first.

---

## 18. A server that answers 200 instead of 206 makes the player fail in silence

**Task.** Serve the marker clip to the device from a Python test server during a measurement run.

**Steps.** Served the directory with `http.server.SimpleHTTPRequestHandler` behind a `ThreadingHTTPServer`, and pointed the app at it.

**Expected.** The player fetches the file, by ranges or not, and plays it.

**Actual.** The clip never loaded and the run produced nothing, with no error. Python's handler ignores the `Range` header and returns the whole file with a 200, and the player treats that as a broken source. Nothing in the log says "this server does not answer ranges", so from the outside it looks the same as entry 17.

**Severity.** Medium. Two silent failures that look identical is what makes this expensive: we could not tell which one we were looking at until the server was fixed.

**Workaround.** `eval/vvd_timing_run.py` implements `Range` properly: it parses `bytes=start-end` and suffix ranges, replies 206 with `Content-Range`, and replies 416 with `bytes */size` when the range cannot be satisfied.

**Suggestion.** Two things, both small. Say in the player documentation that an HTTP source must answer byte ranges. And make the "source is unusable" case produce an error the app can see, which is the same ask as entry 17.

---

## 19. A video-only stream pauses a few seconds in

**Task.** Play a generated test clip long enough to measure twenty covers.

**Steps.** Generated a clip with video and no audio track, played it on the virtual device, and watched position reports.

**Expected.** It plays to the end, or it fails.

**Actual.** It played and then stopped a few seconds in, so a run that needed two minutes measured nothing. Adding a silent stereo AAC track at 48 kHz fixed it, with no other change.

We looked for the cause in the sample and it is not there: a search of the whole pristine `src/` for `audioTrack`, `audioTracks`, `readyState`, `stalled`, `canplay`, `canPlayType` and `preload` finds only two unrelated Redux `preloadedState` hits. There is no buffering watchdog and nothing that waits on audio. The sample's handlers are `onWaiting`, which shows the spinner, and `onPlaying` and `onSeeked`, which hide it. None of them pause. So this comes from below the sample, in Shaka or in the W3C media pipeline, which is why it is not part of our upstream pull request.

**Severity.** Medium.

**Workaround.** Every test clip this project generates carries a silent audio track. `eval/marker_clip.py` adds it with `anullsrc`, and the comment there says why so nobody removes it. It has a second benefit: the layering test asks whether sound keeps going while the picture is hidden, and a clip with no audio cannot answer that.

**Suggestion.** Either play video-only streams, or fail them with an error. Pausing a few seconds in is the worst of the three, because it looks like a stall and sends you hunting for a network problem.

---

## 20. The media element does not exist when the screen mounts, and nothing says when it does

**Task.** Attach media event listeners, so a measurement run can record `timeupdate`, `playing`, `waiting`, `seeked` and the rest.

**Steps.** Attached listeners in an effect at mount, the way a React developer would, then ran a two-minute measurement on the device.

**Expected.** Listeners attach to the media element and events arrive.

**Actual.** The run recorded no events at all. The player is created after the screen mounts, so at mount the ref is still null, the listeners attached to nothing, and the effect never ran again because nothing in its dependencies changed. There is no event, callback or promise that tells an app when the media element becomes available, so there is nothing to wait on.

**Severity.** Medium. It cost a whole run and it is silent: no warning, no error, just an empty results file at the end.

**Workaround.** The harness takes a `ready` flag from the screen that owns the player and re-runs its attach effect when the element appears. There is a test for it, and a beacon event records whether the element and its `addEventListener` were there at attach time, so a future empty run says which of the two was missing. `useCoverHarness.ts` carries the explanation in its own comment.

**Suggestion.** Give the player a readiness signal, or make the ref's assignment observable. Failing that, say in the sample's documentation that the media element arrives later than the screen and show the pattern.

---

## 21. The virtual device backgrounds an app nobody is touching, and playback stops

**Task.** Run a two-minute unattended measurement.

**Steps.** Installed and launched the app, started the run, and left the device alone with nobody pressing anything, as a camera rig would.

**Expected.** The app keeps playing while it is the foreground app.

**Actual.** The device backgrounds an app that nobody is touching, and a backgrounded app stops playing. A launch with nobody at the device can also leave the app in the background from the start, where it never plays at all. On top of that, the sample's player navigates away on an app state change, tearing itself down mid-run.

**Severity.** Medium. A person holding a remote never hits this. Every unattended measurement hits it.

**Workaround.** `eval/vvd_timing_run.py` presses one key after launch to bring the app forward, then presses a key the app does not bind every few seconds for the length of the run, which keeps the device awake without touching playback. A measurement run stays on the player screen and keeps the cover on rather than navigating away.

**Suggestion.** Give developer mode a way to hold an app in the foreground, or document the idle timer and how to extend it. Anything filmed or measured has this problem.

---

## 22. Playback on the virtual device is not steady, and the error says `UNKNOWN`

**Task.** Get one clean playback run, and then get enough of them to measure cover timing.

**Steps.** Ran the same HLS stream repeatedly through `eval/vvd_smoke.py`, then ran the timing harness repeatedly through `eval/vvd_timing_run.py`.

**Expected.** The same clip plays the same way each time.

**Actual.** Of four runs in one afternoon, two played cleanly, one reached the player screen and then failed with `Category: UNKNOWN, Position: 0.084` on the same HLS stream, and one never started because a key press did not land. Later, one layering run advanced media time by 0.14 seconds across 70 seconds while the same clip had played all the way through minutes earlier, so that run was recorded as inconclusive. The cover timing measurement needed 22 app launches to collect 49 usable trials, and a `make stick-day` rehearsal against the virtual device reached only 2 of 50 markers before the device stopped playing. The failures do not say why: the category is `UNKNOWN` and the payload is a position.

**Severity.** High. It is the reason every measurement here is a pooled run across many launches rather than one clean take, and the reason an early number was published and withdrawn: a run that never played still produced a scheduler log that looked perfect until a stricter script refused to count it.

**Workaround.** Every analysis script now requires a position report from the player on both sides of a marker before it counts one, records the reason for each marker it did not count, and drops trials where playback stalled mid-trial. Runs are pooled across launches, and the per-pass event counts, rather than the start events, are what split them. `eval/verify_gate1_archive.py` rebuilds the summary from its own events in CI and fails on any disagreement.

**Suggestion.** Put a reason in the playback error: which fetch, which segment, which decoder, and the HTTP status if there was one. `UNKNOWN` plus a position is not enough for an app to do anything with, and on a safety feature the only safe response to an unexplained error is to hide the picture, which is not a good experience for the viewer.

---

## 23. The sample's `postinstall` builds Shaka Player from source and needs a JDK

**Task.** `npm install` in a fresh clone of `vega-video-sample`.

**Steps.**

```sh
npm install     # runs postinstall: cd shaka-setup && ./build.sh && ./copyOutputs.sh
```

**Expected.** Dependencies install.

**Actual.** `postinstall` unpacks and builds Shaka Player, which needs a JDK on the path. The JDK on this machine was Java 1.8 and x86_64 only. Nothing says a JDK is involved until the build is already running, and the sample's README does not mention it where you first need it.

**Severity.** Low, and unavoidable once you know. It is on the list because it is a first-hour experience and it is one line of documentation.

**Workaround.** `npm install` in this repository runs with `JAVA_HOME=/opt/homebrew/opt/openjdk@21`, recorded in `CLAUDE.md` so nobody has to rediscover it. CI installs with `npm ci --ignore-scripts`, which skips the build entirely, because the tests mock the player and never need the built bundle.

**Suggestion.** Say in the README, next to the install step, that `postinstall` builds Shaka Player and needs a JDK, with the version. Mention `--ignore-scripts` for test-only environments.

---

## 24. `jest --ci` exits 1 on a clean checkout of the sample with every test passing

**Task.** Run the sample's own test suite as CI would, on an unmodified checkout, so that our fork's CI has a baseline.

**Steps.** Clean checkout of `v0.24-RN83`, full install, then:

```sh
npx jest --ci
```

**Expected.** Green, or a failure that names a test.

**Actual.** Exit code 1 with every test that ran passing, and nothing in the output naming a failing test. It ends with:

```
 › 2 snapshots obsolete.
   • <MediaItemShoveler /> renders default featured MediaItemShoveler with no playlistName 1
   • <MediaItemShoveler /> renders default nonFeatured MediaItemShoveler with playlistName 1
Test Suites: 1 skipped, 61 passed, 61 of 62 total
Tests:       4 skipped, 342 passed, 346 total
Snapshots:   2 obsolete, 54 passed, 54 total
```

`test/blocks/components/MediaItemShoveler/__snapshots__/MediaItemShoveler.test.tsx.snap` holds two entries that no current test produces, and `--ci` counts an obsolete snapshot as a failure. We first met it as a red CI run on our own app on a day when nothing was wrong.

One honest note about that paste. Our verification checkout lives at a very deep scratch path, and two other suites, `DrawerContent.test.tsx` and `Preview.test.tsx`, fail there for an unrelated reason: their snapshots hold an asset `testUri` written relative to the project root, which comes out absolute from a deep path. Those two pass in `app/` in this repository, which is the same code at a normal path, so they are excluded from the run above. The obsolete-snapshot exit is independent of them: it happens with every remaining test passing.

**Severity.** Low, and loud. A first-time contributor sees a red build they did not cause.

**Workaround.** Delete the two obsolete entries, which is what commit `e09c36f` in this repository does for our copy. Keeping `--ci` strict is the point of it, so the right fix is to delete rather than to loosen the flag.

**Suggestion.** Delete the two entries upstream. We have offered to send it as a one-line pull request alongside our fix.

---

## 25. The sample's dependency tree buries a secret scan in 208 findings

**Task.** Add secret scanning to the repository, in CI and as a pre-commit hook, and have it be worth reading.

**Steps.** Ran `gitleaks` over the working tree once `node_modules` and the Shaka build existed.

**Expected.** A handful of findings to triage, or none.

**Actual.** 208 findings. Every one of them is a minified third-party demo bundle that ships inside the dependency tree or the Shaka build, none of them committed, and that volume would bury a real finding on the day there is one.

**Severity.** Low. It is the ordinary cost of a large JavaScript dependency tree rather than anything specific to Vega, and it is here because it is a real hour that went on making the tool useful.

**Workaround.** A config that keeps every default rule and allowlists only generated directories. Checked both ways rather than assumed: a synthetic GitHub-style token dropped into `docs/` is found, the same file under `app/build/` is ignored, and the repository is otherwise clean. The hook has since earned its place twice, including blocking a commit over inline Ed25519 public keys in tests, which were checked against the committed `.pub.pem` before one exact string was allowlisted.

**Suggestion.** Ship a `.gitleaksignore` or an equivalent in the sample, covering `node_modules` and the Shaka build output. It is a file most projects need and few write.

---

## 26. The player's position reporting is undocumented, and it is not regular

**Task.** Put the cover on screen before a flagged segment starts. That needs two facts about the player: how often it says where the playhead is, and how precise that number is.

**Steps.**

1. Looked for a stated cadence for `timeupdate` and a stated resolution for `currentTime`, in the Vega documentation and in the type definitions that ship with `@amazon-devices/react-native-w3cmedia`.
2. Found neither, so measured them. Instrumented the app to record every media event with both media time and wall-clock time (`app/src/calmframes/timingLog.ts`), played a clip on the virtual device, and wrote the distribution to `results/vvd_timeupdate_stats.json`.

**Expected.** A documented cadence and a documented resolution, the way a platform states a frame budget. Anything that has to act at a precise media time depends on both.

**Actual.** Neither is documented, and the measured behaviour is not what a developer would assume. In one recorded run the gap between position reports had a median of <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.median -->426<!--/n--> ms, a shortest of <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.min -->75<!--/n--> ms and a longest of <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.max -->5219<!--/n--> ms, while the clip played on throughout. The smallest step `currentTime` reported was <!--n results/vvd_timeupdate_stats.json:current_time_precision_ms -->3<!--/n--> ms. A cover that waited for a position report would have been more than five seconds late in that run, and nothing would have said why.

**Severity.** High. It is the fact this whole project's timing design rests on, the failure mode is silent, and every developer has to measure it for themselves and will get a different answer on a different device.

**Workaround.** Schedule ahead instead of reacting. The cover runs on a wall clock that is re-anchored to media time at every position report, so it goes on before a marker rather than after it, and `app/src/calmframes/mediaClock.ts` holds that arithmetic including playback rate. The price is drift: through the five second silence above, the app's estimate had run <!--n results/vvd_timeupdate_stats.json:worst_wall_clock_drift_ms -->2756<!--/n--> ms away from the player by the time a report arrived. So anything that makes the playhead uncertain, a seek, a stall, buffering or backgrounding, hides the picture at once rather than trusting the estimate. Every timing line records both clocks, so a 240 fps recording can be lined up against what the app believed.

**Suggestion.** Document both, with a stated guarantee and a word about what happens under load. Captions, chapter skips, ad insertion and accessibility overlays all have to act at a precise media time, and right now each of them is guessing.

---

## 27. `setNativeProps` throws on React Native 0.83, so every piece of UI has to be state-driven

**Task.** Drive the cover on and off, along with the rest of the UI, in a way the platform supports.

**Steps.**

1. Took the rule from this project's own day-one list, `docs/BUILD_PROMPT.md` line 114: ban `setNativeProps`, because it throws a TypeError on React Native 0.83.
2. Enforced it rather than trusting it. `app/package.json` carries three ESLint rules against it, one `no-restricted-properties` and two `no-restricted-syntax` selectors, each with the reason in its message, and `app/test/calmframes/dayOneGuards.test.ts` asserts they are there. Every one of those assertions was broken on purpose and seen to go red.

**Expected.** A supported way to change a native view's property directly, as React Native has had for years.

**Actual.** It throws on 0.83. **We never called it, so we never saw the error.** This is a platform rule we adopted and enforced, not a crash we watched, and the log says so rather than dressing it up. The cost was a design constraint rather than a debugging session, and the constraint is real: the cover is driven by state, which puts it behind a React commit and a render, and that delay is one of the things the guard band has to absorb.

**Severity.** Low for us, because we were told. Higher for anyone who finds out by calling it, because the error does not say why and the fix is a design change rather than a patch.

**Workaround.** `app/src/calmframes/CoverLayer.tsx` is state-driven and says why in its own comment. The lint rules make a call fail the build rather than the device.

**Suggestion.** Make the failure explain itself, or ship the restriction as a lint rule in the app template, so it is enforced where a developer writes the code rather than discovered where it runs.

---

## 28. The z-order contract is undocumented, and there is one captions view per process

**Task.** Put the cover between the video picture and the captions, so a caption stays readable over a hidden picture. This is the design the whole product rests on: sound and captions carry on while the flashing part is hidden.

**Steps.**

1. Took two rules from this project's own day-one list, `docs/BUILD_PROMPT.md` line 184: playback only through `@amazon-devices/react-native-w3cmedia`, and only one `KeplerCaptionsView` per process.
2. Looked for a statement of the compositing order between `KeplerVideoSurfaceView`, `KeplerCaptionsView` and ordinary React Native views.
3. Found none, so built it the way the sample wires the two platform views and put the cover between them: surface at z-index 0, cover at 1, captions at 2, in `app/src/screens/PlayerScreen.tsx` and `app/src/calmframes/CoverLayer.tsx`, with a test asserting that order in the rendered tree.

**Expected.** A documented compositing order. An accessibility layer that draws between two platform views depends on it completely, and a change to it would break that layer silently.

**Actual.** Not documented anywhere we could find, in the API reference or the sample. It works: the order holds in the rendered tree and the app draws as intended. What we cannot say yet is whether it holds on a screen, because the virtual device cannot be photographed (entry 14) and the layering run's verdict in `results/vvd_layering_rehearsal.json` is <!--n results/vvd_layering_rehearsal.json:layering.verdict -->inconclusive<!--/n-->. The one-captions-view-per-process rule is the same shape: we designed around it from day one and never hit it, and an app that adds a second one finds out at runtime rather than at build time.

**Severity.** Low, and only because we were told. A team that discovers either of these by trying loses a day, and in the captions case loses it to a runtime failure.

**Workaround.** The cover sits at a named z-index constant between the two views, with the reason written next to it, and a test fails if the order changes. Confirming it on a real screen is part of the layering test on the stick.

**Suggestion.** State the z-order contract in the `KeplerCaptionsView` reference, along with the one-view-per-process rule, and say what an app may and may not put between the video surface and the captions.

---

## 29. Ogg Theora duplicate-frame packets kill the decoder

**Task.** Analyze the four Ogg Theora clips in the screening pool.

**Steps.** Ran the analyzer over `.ogv` files from the media pool, decoding with PyAV.

**Expected.** They decode like every other container.

**Actual.** The decode failed. Ogg Theora marks a frame identical to the one before it with a zero-length packet, and `avcodec_send_packet()` refuses one outright with EINVAL, which surfaces through PyAV as "returned 22". Four clips in the screened pool hit it, which means four titles could not be measured at all until it was fixed.

**Severity.** Medium.

**Workaround.** An empty packet is never handed to the decoder. It carries no picture, so it is kept in the timeline and filled with the picture in front of it, which is what a player shows for that packet's slice of time. That keeps the frame count and the frame intervals true to the file rather than growing a hole where the repeats were. There is a committed non-flashing Theora fixture as a regression test, and PyAV's own end-of-demux drain packet is handled by the same rule.

**Suggestion.** For anyone else hitting this: it is not a corrupt file. It is how Theora encodes a duplicate frame, and any decoder loop that forwards every demuxed packet will hit it.

---

## 30. Theora decodes wider than the size the file declares

**Task.** Record the picture rectangle a map was measured on, so that a re-encode can be measured against the same ground.

**Steps.** Probed the Theora clips and compared the stream's declared size with the size of the frames that came back.

**Expected.** They match.

**Actual.** Three Ogg Theora clips in this project's pool declare 840 by 560 and decode to 844 by 560, because the codec pads to its block size. Reporting the padded width as the file's size would be wrong, and it would stop a rendition ever being measured against the rectangle in that file's map, since the check is that the two files have the same coded frame.

**Severity.** Low, and worth writing down because it is silent and it corrupts a comparison rather than failing it.

**Workaround.** The declared size is what goes in the map. The whole decoded frame including the padding is what gets scaled and measured, which can only add a sliver of edge to the measurement rather than taking one away.

**Suggestion.** None for Amazon. This is a note for anyone who assumes a decoded frame is the size the container says.

---

## 31. Re-encoding moves the picture rectangle, which moves every area fraction

**Task.** Verify that a kid-safe rendition still hides everything the source map says to hide.

**Steps.** Analyzed a source title, rendered a rendition from it, then analyzed the rendition with the detector running normally on both.

**Expected.** The same picture in the same place, so the two sets of area fractions are comparable.

**Actual.** Re-encoding nudges the outermost rows and columns, so the letterbox detector run on the rendition finds a bar one row taller or shorter than the one it found in the original. Every area fraction is measured against the picture, so one row is enough to lift a span over the area limit and flag content that the original did not. This is what blocked a title in the pipeline, and it would have looked like a verify failure rather than a measurement artifact.

**Severity.** Medium.

**Workaround.** The rectangle travels with the map. A rendition is measured on the rectangle carried in from the source's map rather than on one detected in itself, verify refuses a rendition whose map was measured on a rectangle of its own, and the detector still runs so what it found is recorded alongside. A carried rectangle from a different coded frame size is an error rather than a rescale, because a rectangle from a different frame size does not describe this file.

**Suggestion.** None for Amazon. It is a warning for anyone comparing two encodes of the same video: detect once, then carry the geometry.

---

## 32. A re-encode renumbers the first timestamp, so the rendition slides under the map

**Task.** Play a rendition with a cover schedule built from the source's map.

**Steps.** Compared the first presentation timestamp of each rendition against its source, across the pool.

**Expected.** The pictures are where they were.

**Actual.** A re-encode routinely renumbers the first presentation timestamp to zero while leaving every picture where it was. The source files in this pool start anywhere from 3 to 67 ms in. The map's intervals are on the source timeline, so a rendition whose timeline has slid draws every live cover that much late.

**Severity.** Medium. It is small, and it comes out of the one budget that has nothing to spare: the guard band also has to absorb scheduler jitter, and a cover has already been measured going on 86 ms after its marker with the JavaScript thread away for about 335 ms of a 500 ms band.

**Workaround.** The start offset gets a tolerance of its own, 150 ms, which is the pool's worst real offset of 67 ms with room to spare, capped by the guard band so a narrower band narrows the tolerance too. Whatever the offset turns out to be, verify measures it and records it per preset as `rendition_start_offset_ms` in the catalog entry, so a player can subtract it and it costs the band nothing. It is an engineering tolerance, not a spec number, and it says so. Checked by breaking it: raising the limit to 600 ms turns two tests red, and dropping the cap turns the narrow-band test red.

**Suggestion.** None for Amazon. For anyone shipping a sidecar against a re-encoded rendition: measure the offset and publish it, rather than assuming the timelines agree.

---

## 33. The ffmpeg photosensitivity filter misfires on its own first second

**Task.** Run a published baseline alongside our analyzer, so the comparison table is not only us.

**Steps.** Ran ffmpeg's `photosensitivity` filter over the clip pool, including static controls, and inferred a flag from where its output differs from the unfiltered decode.

**Expected.** A static gray clip produces no difference.

**Actual.** It fires in its first second even on static gray. It is also a mitigator rather than a reporter: it rewrites the frames it thinks are unsafe, so there is no flag to read, only a difference to infer.

**Severity.** Low, and it matters for fairness rather than for our own product. A baseline that is measured wrong makes our numbers look better than they are.

**Workaround.** The first second of its output is dropped, and the baseline write-up says that in the results file itself rather than in a footnote. Neither baseline is presented as a safety tool.

**Suggestion.** None for Amazon. For anyone comparing detectors: check what your baseline does to a control clip before you report a difference.

## 34. Restricted automation blocks Watchman and local HTTP listeners

**October 9 follow-up.** In the restricted finishing session, `ps` was denied,
Vega status could not write its SDK log, and `vega virtual-device start -t 30`
failed while registering QEMU with the host. `claude auth status` returned
`loggedIn: false`; one read-only CLI task returned `Not logged in`. This is
not evidence that the user's normal terminal lacks subscription access.
No credentials, billing method or permission controls were changed. The
simulator and subscription check require the normal host session.

`fnm env` also tried to write outside the workspace; using the already installed
Node 22 binary directly worked. The Python collection step hit jsii's host
cache timestamp write; `JSII_RUNTIME_PACKAGE_CACHE_ROOT` selects a writable
build cache without changing tests. The pinned CycloneDX generators were
already cached and could run directly: all three regenerated SBOM files matched
the committed bytes. The app's aarch64 Debug build succeeded. These outcomes
separate a build from the still-blocked simulator validation.

**Task.** Run scene-hold and regression tests on Sep 29, 2026.

**Steps.** From `app/`, ran Node 22 Jest through `fnm exec --using 22 npm test`
with scene-hold, playback, guard, harness and map test paths. From the repo root,
ran `.venv/bin/python -m pytest flashmap pipeline eval -q -m 'not slow'`.

**Expected.** The tests to start.

**Actual.** Jest stopped before running any tests:

```text
unable to talk to your watchman on ~/.local/state/watchman/<user>-state/sock! (Operation not permitted)
```

The Python run executed its other checks, but the nine upload-server cases failed
in fixture setup at `socket.bind` for `127.0.0.1`, with
`PermissionError: [Errno 1] Operation not permitted`.

**Severity.** Low. These are local sandbox constraints, not Vega failures.

**Workaround.** Add `--watchman=false` to use Jest's file crawler. The broader app
run kept coverage enabled and completed with Watchman disabled. Re-run Python
without the two HTTP test classes to check the remaining suite, and record those
server tests as unverified here rather than treating them as passes. They still
need an unrestricted runner.

During the pre-push hardening pass, `make sbom-check` also could not fetch
`cyclonedx-bom` from PyPI because DNS access was restricted. The report-page
Chrome process exited with code -6 before producing a screenshot; its cause is
not established. A broad Jest rerun timed out in two existing registry tests
while host load was excessive, and the native build, broad reruns and incomplete
mutation run were stopped. Those interrupted or blocked checks are not passes.
Focused runtime regressions, strict TypeScript and targeted lint then passed;
complete final-source validation still needs a suitable runner.

The later final-source sequential app and selected Python sweeps passed, as did
native Debug packaging on all three configured architectures. The remaining
HTTP, report-page, SBOM and full remote CI checks are still unverified, not
silently counted as passes.

A bounded read-only Docker check found a client but could not access the Colima
daemon socket: `permission denied` on
`~/.colima/default/docker.sock`. No containers, images, builds,
network settings or shared services were changed. Docker is not an available
alternative HTTP-test runner in this session.

**Suggestion.** Document restricted-runner commands and retain the full suite in CI.

---

## 35. GitHub Actions fails before starting an Audit runner

**Task.** Obtain complete pre-publication CI evidence for the scene-hold changes.

**Steps.** On Sep 29, read the current main commit's workflow history through the
connected GitHub API. Inspect the Sep 28 scheduled
[Audit run](https://github.com/alejandro-publius/calm-frames/actions/runs/36431466841),
its jobs and timing, then retry its failed jobs once.

**Expected.** A runner to check out the repository and execute each audit.

**Actual.** Both attempts failed all four jobs within two to three
seconds, with `runner_id: 0` and `steps: []`. No runner logs exist. The first
attempt recorded zero runner milliseconds. The Sep 21 scheduled Audit on the
same main commit passed. No dependency audit command ran in either failed
attempt, so this is not evidence of a dependency finding.

After publishing the exact locally tested tree as
[draft PR #1](https://github.com/alejandro-publius/calm-frames/pull/1), both its
[CI run](https://github.com/alejandro-publius/calm-frames/actions/runs/36646189829)
and [Audit run](https://github.com/alejandro-publius/calm-frames/actions/runs/36646189802)
failed every job with no assigned runner and no executed steps. This reproduces
the restriction on the proposed tree without supplying any test result.

**Severity.** High for completing CI, not an Amazon or application failure.

**Workaround.** None in the repository. The exact startup annotation is not
available through this connector. Account quota or billing is possible, not
confirmed. Resolve the Actions startup restriction in GitHub, then rerun the
complete required checks. Local validation continues, and main stays unchanged.
Do not widen audit exceptions, disable jobs or change repository visibility.

**Suggestion.** Expose startup-failure annotations through the workflow-run API
so automation can distinguish account or runner restrictions from code failures.

---

<a id="packaged-file-uri"></a>

## 36. A packaged `file:///pkg/...` URI is not opened by the native player as written

**Task.** Play the bundled Harbor title from the package on the Vega Virtual Device.

**Steps.** Handed the player the packaged MP4 and WebVTT as `file:///pkg/...` URIs, the form the Kepler file system documentation gives for package assets.

**Expected.** The native player opens a package asset by its documented URI.

**Actual.** Native GStreamer treated `file:///pkg/...` as a literal file name and failed to open it. The same bytes opened as `/pkg/...`.

**Severity.** High. Nothing played from the package until this was found.

**Workaround.** Normalize the package prefix to `/pkg/...` at the native media boundary only, in `app/src/utils/VideoHandler.ts`, and keep the signed catalog identity unchanged. Both Harbor titles play.

**Suggestion.** Document the URI form the native player accepts for package assets, or accept the `file://` form the file system documentation gives.

## 37. The native caption view cannot be stacked above a React Native image by z-index

**Task.** Keep captions visible above a scheduled scene image during a hold.

**Steps.** Set a z-index directly on the native caption view, above the React Native image that draws the cover.

**Expected.** The caption view sits above the cover like any other sibling.

**Actual.** The native caption view stayed under the image; a z-index on it did nothing.

**Severity.** High. Captions under the cover defeat the point of a hold that keeps the story going.

**Workaround.** A retained, non-collapsible React Native host view carries the stacking style and the caption view lives inside it, in `app/src/screens/PlayerScreen.tsx`. Both observed holds keep captions on top.

**Suggestion.** Document native surface composition with examples: which views are native layers, and what z-index does and does not reach.

## 38. Simulator capture can return an older GPU frame, and a static screen records few frames

**Task.** Capture the simulator window for the demo and for navigation checks.

**Steps.** Captured with ScreenCaptureKit while Stage Manager had the simulator in the background, and recorded static screens.

**Expected.** A capture shows the frame on screen now, and a recording has a steady frame rate.

**Actual.** A capture could return an older GPU frame, which confused navigation validation. A static screen produced variable-rate video with few frames, so a presumed constant frame count was wrong.

**Severity.** Medium. Test friction rather than a product defect.

**Workaround.** Activate the simulator before every capture and review the recording's actual frames; read frame timestamps rather than assuming a frame count.

**Suggestion.** A CLI command that captures the simulator's screen, which entry 9 also asks for.

## 39. Custom fonts render as the fallback face unless they sit in `assets/fonts`

**Task.** Ship the licensed Inter faces the approved design uses.

**Steps.** Put the static TTFs under `assets/raw/fonts`, then under `assets/fonts`.

**Expected.** A bundled font resolves wherever the package carries it, or the documentation says where it has to be.

**Actual.** Under `assets/raw/fonts` every weight rendered as the fallback face. Under `assets/fonts` the intended weights appeared.

**Severity.** Low. Found by looking at the screen.

**Workaround.** The fonts live in `app/assets/fonts`.

**Suggestion.** Document the fonts directory, and what a fallback render looks like so it is recognised.

## 40. Disabling a focused control drops native focus

**Task.** Block repeated presses on a parent setting while its save is pending.

**Steps.** Disabled the focused preset, room and chime controls for the length of the save.

**Expected.** Focus stays where it was, or moves somewhere predictable.

**Actual.** Native focus vanished with the control, and the remote had nowhere to go.

**Severity.** Medium. A ten foot interface with no focus is stuck.

**Workaround.** Keep the control in the focus order, report the disabled accessibility state and block its handler instead, in `app/src/calmframes/ParentAreaScreen.tsx`. The deferred-write regression was seen failing before the fix.

**Suggestion.** Document focus behaviour when a focused view becomes disabled, and move focus to a neighbour by default.

## 41. The image loader refuses a data URI, so a signed still showed black on the device

**Task.** Show the signed hold still during a practice hold. The flash map carries each still as an authenticated `data:image/jpeg;base64,...` URI, which the app rendered through `Image` with `{ uri }`, and which every unit test and browser preview had drawn.

**Steps.**

1. Installed the Debug candidate on the Vega Virtual Device and started the practice film from Details.
2. Streamed the device log: `vega device start-log-stream --device Simulator`.
3. At each hold, read the app's own `CALM_TRACE still` breadcrumb and the device lines beside it.

**Expected.** The still from just before the hold, on top of the covered picture, as in every test and preview.

**Actual.** The hold card appeared over black. At every hold the device logged, with the data URI after the colon:

```
ERROR com.amazon.keplerscript: [KeplerScript-Native] LocalAssetImageLoader: Cannot load image from non local source:
```

Thirty-five such lines in the Oct 14 session. Nothing in the React Native for Vega pages read so far says a data URI is unsupported, and `Image` accepts the source without a type error, so the first the build heard of it was the device.

**Severity.** High. The still is what a hold shows instead of black, so on the device the feature's picture was black until the workaround, and no test or preview could have shown it.

**Workaround.** The two practice stills ship as package assets, generated by `eval/benign_story_stills.py`, and `app/src/calmframes/bundledStills.ts` swaps one in only when the authenticated data URI matches exactly, so the signed map still decides what is shown. Commit `52138fe`. A map for any other title shows black until its stills are bundled the same way.

**Suggestion.** Load data URIs in `Image`, or document that only packaged and remote sources load, and report the refusal to JavaScript with its reason instead of only to the device log.

---

## 42. The player never reports a decoded frame on the virtual device

**Task.** Keep the opening still on screen until the first real frame has decoded, then swap to the video, so a family never sees a black frame. The shell waited for `getVideoPlaybackQuality().totalVideoFrames` to move, which is what the API is for.

**Steps.**

1. Started any title on the Vega Virtual Device with the Debug candidate installed.
2. Streamed the device log and read the `CALM_TIMING` events beside the player's own lines.

**Expected.** `totalVideoFrames` climbs once playback starts.

**Actual.** Every call failed below JavaScript and the counter stayed at zero while picture and sound played:

```
E W3CMEDIA:[MSE_EME] get_video_playback_quality: MPB Call failed with code: 50001.
```

263 such lines in one twenty-minute session. The shell waited out its 15 second allowance and then showed the recovery screen about fourteen seconds into every playback, over a film that was playing correctly.

**Severity.** High. Every playback on the device ended on a recovery screen until the workaround, and nothing documents what code 50001 means or that the call cannot succeed on the virtual device.

**Workaround.** `app/src/calmframes/useOpeningFrame.ts` readies the shell when the counter is silent but the element reports `readyState` of 2 or more, is not paused, and its clock has advanced a quarter of a second since the first poll; a counter that does report still wins. Commit `ac5a610`, with tests that failed first.

**Suggestion.** Make `getVideoPlaybackQuality` work on the virtual device, or fail it in JavaScript with a documented error instead of silently in native code, and document code 50001.

---

## 43. The documented remote-button command looks for a host executable that is not there

**Task.** Press remote buttons on the virtual device from a script. Amazon's 0.24 `inputd-cli` page (developer.amazon.com/docs/vega/0.24/inputdcli.html, read Oct 9, 2026) describes `inputd-cli`, built into Fire TV devices and the virtual device, and gives the host form `vega exec inputd-cli button_press KEY_BACK`.

**Steps.**

1. `vega exec inputd-cli --help`
2. `vega device run-cmd --device Simulator --command 'inputd-cli --help'`
3. `vega device run-cmd --device Simulator --command 'inputd-cli button_press KEY_DOWN'`, and the other keys, from the acceptance driver.

**Expected.** Step 1 presses buttons as the page says.

**Actual.** Step 1 prints `[Errno 2] No such file or directory: 'inputd-cli'` and exits 0, so a script cannot even tell that it failed. Rechecked Oct 14, 2026 on Vega CLI 1.3.4. Steps 2 and 3 work: the tool runs on the device and drove both Oct 14 acceptance sessions (`results/native-acceptance-2026-10-14/receipt.json`).

**Severity.** Medium. Entry 9 was written when no route was known and the QMP socket was the only way in. The documented route exists, its documented spelling fails, and a zero exit status hides that.

**Workaround.** `vega device run-cmd --device Simulator --command 'inputd-cli button_press KEY_X'`, with `KEY_UP`, `KEY_DOWN`, `KEY_LEFT`, `KEY_RIGHT`, `KEY_ENTER`, `KEY_BACK` and `KEY_PLAYPAUSE` all seen to work.

**Suggestion.** Make `vega exec inputd-cli` reach the device-side tool as the page says, or correct the page to the `run-cmd` form, and exit non-zero when the executable is missing.

---

## 44. The image loader logs an error for every packaged image, and then loads it

**Task.** Read the device log for the reason a signed still showed black (entry 41), and then for anything wrong with the Home scene, which logged the same error at every mount while reporting that it loaded.

**Steps.**

1. Installed the Debug candidate and streamed the device log: `vega device start-log-stream --device Simulator`.
2. Opened Home, Details, the opening shell and the practice film, and lined up every `LocalAssetImageLoader` line against the app's own `CALM_TRACE image` and `CALM_TRACE still` breadcrumbs.

**Expected.** An error from the image loader means an image did not load.

**Actual.** On Oct 14 every packaged image, loaded with `require(...)`, produced one line a few milliseconds before its own load event, and then loaded:

```
ERROR com.amazon.keplerscript: [KeplerScript-Native] LocalAssetImageLoader: Cannot load image from non local source:
```

Twenty distinct lines in one twenty-minute session: the coastal scene at every mount of Home and Details, the two pictures of the opening shell, and each bundled still at the holds, each followed within ten milliseconds by `image scene loaded` or `still loaded`. The loader seems to try a non-local source for a packaged asset first and log the miss as an error. Nothing distinguishes that line from the one in entry 41, where the image never loaded, except the load event the app has to print itself.

**Severity.** Low. No picture is affected. It cost an evening of chasing a gradient view that was never at fault, and it means a real image failure cannot be found in the log by its message alone.

**Workaround.** Judge an image by the app's own `onLoad` and `onError` breadcrumbs (`CALM_TRACE image` and `CALM_TRACE still`), never by the loader's line.

**Suggestion.** Log the miss at debug level, or not at all when a later source succeeds, and keep the error level for an image that did not load.

---

## How to add one

Write the six fields Amazon asks for: task, steps, expected versus actual, severity, workaround, suggestion. Real entries only, the way `CLAUDE.md` says. If it did not happen on this build, it does not go in, and if it is a platform rule we adopted rather than a failure we watched, say so in the entry itself. The log has three of those and each one is labelled.

Give it the next number here, add its row to the summary table at the top, and update the counts line under that table.

## Where the log's later entries came from

The first eleven and the Sep 29 entries, 34 and 35, were written here as they happened. Entries 12 to 33 were not: the lanes hit them while working rather than while keeping notes, so each one was found again in a commit, a code comment, a results file or a decision entry. Here is where each came from, so nobody has to take the log on trust.

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
| 26 position reporting is undocumented | `results/vvd_timeupdate_stats.json`, `app/src/calmframes/timingLog.ts` and `mediaClock.ts`, GATES.md |
| 27 `setNativeProps` throws on 0.83 | docs/BUILD_PROMPT.md line 114, the three ESLint rules in `app/package.json`, `app/test/calmframes/dayOneGuards.test.ts`, commit `3230b7e`. A rule adopted, not a crash seen |
| 28 z-order and one captions view | docs/BUILD_PROMPT.md line 184, `app/src/calmframes/CoverLayer.tsx`, `app/src/screens/PlayerScreen.tsx`, `results/vvd_layering_rehearsal.json`. Also adopted rather than hit |
| 29 Theora empty packets | `flashmap/src/flashmap/decode.py` header, `flashmap/tests/test_theora.py`, commit `e654b74` |
| 30 Theora decodes wider than declared | `flashmap/src/flashmap/decode.py` around the declared size |
| 31 re-encode moves the rectangle | `flashmap/src/flashmap/analyze.py` `carried_picture`, `picture.py`, commit `d89b063` |
| 32 re-encode renumbers the first timestamp | `pipeline/verify.py` `compare_rendition_to_source`, docs/SIDECAR_SPEC.md, commit `4436eda` |
| 33 ffmpeg photosensitivity filter | `eval/baselines/run_all.py`, commit `daec5b7` |
| 34 restricted sockets | Sep 29 scene-hold verification; commands and limitations recorded in docs/STATUS.md |
| 35 Actions startup | Audit run 36431466841, attempts 1 and 2, inspected Sep 29; no runners or steps |
| 36 packaged URIs | `app/src/utils/VideoHandler.ts`, the native media boundary; `results/native_validation_2026-10-10.json` |
| 37 caption stacking | `app/src/screens/PlayerScreen.tsx`, the retained caption host; the Oct 10 native captures |
| 38 simulator capture | docs/SHOT_MANIFEST.md and `results/redesign_demo_manifest_2026-10-10.json`, frame timestamps rather than counts |
| 39 fonts directory | `app/assets/fonts/`, docs/brand/README.md |
| 40 focus on a disabled control | `app/src/calmframes/ParentAreaScreen.tsx`, the deferred-write regression in the parent area tests |
| 41 data URI refused | `app/src/calmframes/bundledStills.ts` header, docs/STATUS.md (Oct 14, night), commit `52138fe` |
| 42 no decoded frame counted | `app/src/calmframes/useOpeningFrame.ts`, `app/test/calmframes/openingFrame.test.tsx`, commit `ac5a610` |
| 43 `vega exec inputd-cli` | CLAUDE.md, the section on working with the virtual device; `results/native-acceptance-2026-10-14/receipt.json` |
| 44 loader error before every load | `results/native-acceptance-4-2026-10-14/receipt.json` (`image_loader_errors_distinct`), FINAL_HANDOFF.md section 3 |

### 2026-10-14: visible native checks interrupted active desktop work

Repeated simulator foregrounding was distracting before a coherent UI change
was ready. Severity: workflow disruption. Stopped native interaction at the
user's request and moved to an isolated code integration plus headless host-tree
previews. Next native check should be one consolidated session after handoff.
Terminal control was separately denied by the computer-use tool for safety;
user-pasted prompts remain the available Claude coordination route.

### Oct 14: consolidated native preview blocked by locked Mac

After the reviewed source and focused corrections were ready, the requested
single native session could not begin. `cua.listApps()` reported that the Mac
was locked and automatic unlock failed. No simulator install, relaunch or
Terminal UI action followed. A manual Mac unlock is required. The independent
source, package and artifact work continued and the prior build was preserved.

### October 17: owner reports slow loading during design review

Task: open and watch the newly installed build. Expected: responsive transitions.
Actual: owner reported everything loads slowly and supplied an image of a scheduled
cover. Severity: blocks comfortable review. Source fixes remove measured repeated
verification and unnecessary startup/Back work; the image and retained logs do not
prove a stalled clock. Workaround: preserve the current app while source regressions
run, then use one coordinated native timing checkpoint. See the performance receipt.

### October 17: rapid cover and Skip status changes feel robotic

Owner task: watch the installed prepared video. Expected: readable steady feedback.
Actual: owner reported that Flashing hidden to Skip/status transitions were too quick.
Source showed changing countdown text, disappearing/reappearing Skip, completion
cards and two announcement paths. Severity: usability issue during playback.
Resolution in source: stable scene copy/action position and one speech path, without
changing cover intervals or media actions. Native acceptance awaits approval.

### October 17: concurrent package replacement interrupts native acceptance

Task: install the approved stabilization build once and test without capture.
Expected: the reviewed package remains installed during the check. Actual: a
second install completed about 70 seconds later and the transferred package hash
differed. App route breadcrumbs were absent. Severity: blocks attributable native
acceptance. Workaround: stop before remote keys and preserve the open app.
Suggestion: agree one simulator owner and compare the delivered hash before
navigation. The other installer was not identified. Evidence:
results/stabilization-native-2026-10-17/receipt.json.

### October 17: low-progress native playback despite playing state

Task: complete Pause, Skip and manual Back on the reviewed installed app. Expected:
media resumes normal progress and Skip completes promptly. Actual: 17.426 s media
progress in 122.089 s wall (including a 3.382 s deliberate pause); a fresh run
without Pause also slows. Native audio-sink reports zero position advance, video
queue reports buffering; JavaScript does not emit a new waiting event in run 1.
Skip reaches its guarded target after about 7.26 s. Severity: blocks smooth-playback
acceptance. Back remains usable. No source workaround applied without a proven
cause. Evidence: results/remaining-controls-2026-10-17/.

Follow-up, same day. Two isolation runs reproduced it: <!--n results/native-slowdown-isolation-2026-10-17/receipt.json:experiments.fresh-app.media_span_ms -->6010<!--/n--> ms of video took
<!--n results/native-slowdown-isolation-2026-10-17/receipt.json:experiments.fresh-app.wall_span_ms -->15560<!--/n--> ms on a fresh app, and <!--n results/native-slowdown-isolation-2026-10-17/receipt.json:experiments.fresh-simulator.media_span_ms -->5886<!--/n--> ms took
<!--n results/native-slowdown-isolation-2026-10-17/receipt.json:experiments.fresh-simulator.wall_span_ms -->26435<!--/n--> ms after a simulator restart
(results/native-slowdown-isolation-2026-10-17/). A minimal SDK playback app, run
outside this repository, showed the same pattern. Both later played at normal
speed with no code change; a later run advanced <!--n results/compact-scene-control-2026-10-17/native/summary.json:clock_segments.1.media_ms -->20894<!--/n--> ms of video in <!--n results/compact-scene-control-2026-10-17/native/summary.json:clock_segments.1.wall_ms -->20899<!--/n--> ms.
Cause unknown. Host activity is a candidate, not a finding. No fix is claimed.

### October 17: centered scene message dominates playback

Owner task: watch the prepared film. Actual: the large centered Flashing scenes
and Skip panel interrupts the composition. Resolution: a fixed compact group
in the lower-left safe corner, short truthful labels and one focus outline.
Source checks and native control logs pass after the authorized single install.
The app stays paused on the compact control for owner visual acceptance.
The screenshot's teal linked orbs remain unidentified and were not changed.

### October 17: playback state feedback and end return

Observed native clocks could crawl without a new waiting event. Source also
kept loading beside Pause and allowed any key to cancel the 2.3-second end
return. The finish pass adds read-only slow-progress feedback, gives Pause
sole status ownership, clears MP4 waiting only on progress, and routes end
directly through existing teardown. Separate waiting episodes now each get
one accessibility announcement. 217 focused tests pass. Native controls now
pass on the verified package, with natural end returning Home Watch in 361 ms.
Owner appearance/audio review remains separate. No slowdown cure is claimed.


### October 17: Intentional cover looked like a playback failure

Task: investigate owner-reported full-picture blackouts. Steps: inspect the supplied
image, replay prepared Acadia with text logs, compare the signed schedule and
numeric source/rendition black-frame analysis. Expected: an intentional, understandable
cover. Actual: the no-signed-still branch paints black, while Scene hidden and Skip
remain visible. Severity: confusing core playback presentation. Workaround/fix:
fully opaque slate explanation during the same scheduled interval. Separate finding:
the original and prepared clip both begin with about five near-black seconds.
Suggestion: include scheduled-cover presentation and content-opening review in the
owner's short demonstration check. No protection was removed.

## October 18: removed prepared-media generations linger in Vega staging

Task: build the approved three-island package after omitting two obsolete bundles.
Steps: replace the source prepared-library namespace with the reviewed 66,492,442-byte
copy, run npm run build:debug. Expected: package contains the same namespace. Actual:
native compilation completed successfully, but the unchanged postbuild gate rejected
the package budget. All three incremental staging directories still contained the
omitted generations, totaling 71,988,311 bytes. Severity: blocks installation.
Workaround: preserve stale staging for evidence, replace only the staged media
namespace with the exact source copy, repackage compiled output with installed vpt,
and rerun all strict package gates. No source, limit or trust change. Suggestion:
Vega should synchronize removals when staging raw assets, or document that asset
removals require cleaning the generated staging namespace.

## 2026-10-21: local test runner requested Watchman state access

Task: run the final UI source checks. Expected: workspace-only Jest run. Actual: Watchman tried to chmod its state outside the writable workspace and exited before tests. Severity: blocked that invocation only. Workaround: run Jest with --watchman=false using the existing Node 22; no permissions or software changed. Suggestion: use this flag for bounded local CI-style runs.

## 2026-10-21: Vega incremental packaging retained replaced media

Task: package the approved Acadia replacement. Expected: five bundles and 63,317,768 prepared bytes. Actual: native staging retained the removed Acadia bundle/report alongside the new bundle, and the mandatory package budget gate rejected the archive. No installation occurred. Severity: build blocked. Workaround: move only the generated prepared namespace from app/build/private/vega/aarch64/Debug/assets/raw to the external evidence backup, then rebuild from the checked source assets. Suggestion: refresh the native staged asset tree when a bundle is removed.

## 2026-10-25: native focus and pause defects found after source tests passed

These are app defects recorded on fbe53bf, not claims that Amazon caused them.
The [received handoff](../START_HERE_CODEX.md) contains the exact native package,
fictional-household screenshots and speech transcripts. The [local fix record](native-fixes-2026-10-25/README.md)
separates new source regressions from pending native confirmation.

| Issue / severity | Reproduction and expected behavior | Actual native behavior | Workaround and actionable correction |
|---|---|---|---|
| D1, high navigation disruption | Select each Home title, Down to Watch, Up. Expect the same selected card. | Spatial navigation moves to a nearer middle card and changes title; some card Down moves to Details. | Re-select the title before watching. Explicit native ref/handle routing now maps cards Down to Watch and action Up to the selected card; verify both sizes. |
| D2, high focus/visibility disruption | In a fictional profile's Parents, save Reading comfort. Expect switch focus and its full saved state to remain visible. | Focus returns to top Back; enlarged content pushes the switch below the viewport. | Scroll back and inspect the saved state. Consume initial Back preference once and reveal the switch using layout events; test save failure and moving away during save as well. |
| D3, high accessibility feedback defect | With VoiceView, open player, let playback start, pause, show/hide controls, resume and pause again. Expect one notice per actual pause, none on opening. | Opening gets a pause announcement; real pauses are silent with the recorded Dolby session. | Inspect visible pause state; do not treat it as speech acceptance. Keep a persistent polite live region and separate restored-pause guidance from a new pause event. Native listening still required. |

The near-white transition is tracked separately in the [first-frame investigation](native-fixes-2026-10-25/FIRST_FRAME.md).
The app's default route background was a concrete fixable gap. Recorder timing
alone cannot identify decoder or compositor fault, so those layers and approved
media remain unchanged. No permission bypass, Mac host fault attribution or
unverified platform defect is included here.

## 2026-10-25: one damaged local import blocked other caregiver reviews

This is a project intake-store defect, not an Amazon or Mac platform finding.
Reproduce with fictional local jobs: keep one intact review, truncate another
job's metadata, then restart and request the job list. Expected: the intact
review remains usable and the damaged record has a recoverable error. Actual:
the old store raised while starting or listing every job. Severity: high for
the affected local workflow. Workaround: preserve the damaged directory outside
the intake root before restarting; never repair a review hash by guessing.

The correction keeps a non-authorizing unreadable placeholder and permits only
explicit local removal after an owned worker is stopped. The same real HTTP
regression exposed a second issue: a saved review appeared ready just before
its worker exited, so an immediate approval was refused. Severity: moderate
transient workflow disruption. The corrected finishing state retains ownership
until actual exit. The [tests and browser evidence](cloud-followup-2026-10-25/IMPORT_RECOVERY.md)
cover both issues; no host fault or native acceptance is inferred.
