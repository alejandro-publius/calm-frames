# Integrated delivery evidence — October 18, 2026

Source/app commit `612545932ea46f4547f594f58b2cf2b83f9134b3`.
See [the final handoff](../../docs/DELIVERY_INTEGRATION_FINAL.md).

- `build-receipt.json`, `build.log`, `app-inputs.json`: single successful Debug build and all 730 input hashes.
- `install-receipt.json`, `install.log`: single successful install, device package SHA-256 and running-app confirmation.
- `strict-built-package.json`: report-required gate against the built package.
- `python-tests.log`, `node-tests.log`, `app-tests.log`: 55 + 32 + 59 passing focused tests.
- Empty `typecheck.log` and `eslint.log` are successful quiet checks; `ruff.log` records its pass.
- `acadia-fixture-check.json`: existing exact-approved Acadia fixture rechecked using integrated Python code; no Watch/install permission.
- `intake-server-receipt.json`: controlled refresh of the idle owned loopback service, preserving jobs and signer configuration.
- `native-results.json`, `native-smoke.log`, `native-device.log.gz`: first launch wait stopped before remote keys because app trace messages were absent.
- `native-resume-results.json`, `native-resume.log`, `native-resume-actions.jsonl`, `native-resume-device.log.gz`: completed smoke using the same installed app without relaunch/reinstall.
- `native-trace.txt`: consecutive duplicate trace messages removed for reading; raw text logs retained compressed above.
- `reserved-before.json`, `reserved-after-integration.json`, `final-integrity.json`: concurrent submission edits preserved, all app inputs unchanged.

Native end → Home Watch focus took about 284 ms in the recorded run. This is a single
text-log measurement, not a performance guarantee or visual/audio acceptance.
No screenshot, screen/video recording, original hazardous playback or computer-use capture was performed.
