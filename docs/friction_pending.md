# Friction entries waiting for evkit

These are real entries from the build. They move into docs/FRICTION_LOG.md with `python -m evkit.friction add` once the head-start kits are installed, and this file is deleted after the import.

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
