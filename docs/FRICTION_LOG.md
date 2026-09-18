# Friction log

Developer friction found while building Calm Frames on Vega OS, in the six fields Amazon asks for: task, steps, expected versus actual, severity, workaround, suggestion.

Everything here is real. Each entry is something that cost time on this build, with the exact commands and the exact output. Nothing was invented to fill the log, and nothing was softened.

**Working notes stay in [`docs/friction_pending.md`](friction_pending.md).** That file was the running log while the build was going, and it is kept rather than folded away, because the lanes still add to it as they hit things. This file is the final format, and it is what goes into the Devpost product feedback.

**Environment for every entry unless the entry says otherwise:** macOS 15.1.1 (24B91) on Apple M1, 16 GB. Vega CLI 1.3.4, Vega SDK 0.24.9914, Vega OS 1.2 (TV Ship/101520710) on the Vega Virtual Device, Node 22, September 17 2026.

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

Four are Medium and seven are Low. Nothing was High, and nothing blocked the build outright, because every one of them had a way around it. Three of them (6, 9, 10) cost the most, because each broke the obvious way to automate something and the workaround had to be built from scratch.

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

**Actual.** `source "/Users/alexvintera/vega/env"` was appended to both `~/.zshrc` and `~/.zprofile`. The script's list also includes `.bashrc`, `.bash_profile` and `.profile`. A zsh login shell now sources the env file twice. No environment variable in the script turns this off.

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

**Steps.** Read through `vega device --help` and `vega exec vda`.

**Expected.** Something like `vega device key dpad-down` and `vega device screenshot out.png`.

**Actual.** Neither exists. `vega device` covers install, launch, logs, shell and port forwarding, but no input and no capture. The bundled device adapter is adb-derived, but the device has no `input` or `screencap` tool.

**Severity.** Medium. Automated UI checks and screen recordings both need this, and for an accessibility project the screen capture is not optional.

**Workaround.** The virtual device is QEMU with a QMP socket at `/tmp/qmp-socket-*.sock`, so `eval/vvd_control.py` sends key events with `input-send-event` and captures with `screendump`. Key injection works. Screenshots come back black, because the app renders through a GPU layer that `screendump` does not see, so playback evidence has to come from device logs instead. This is an undocumented interface and it could change between SDK versions.

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
