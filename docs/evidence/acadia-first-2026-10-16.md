# Acadia as the consumer default, October 16, 2026

Status: source change only, on `codex/dark-cinema-2026-10-16`. The running
app has not been rebuilt, installed, launched, restarted or navigated in this pass.

The owner asked for real footage like Acadia instead of the Harbor video.
The default catalog now selects the exact approved Acadia source from the
existing prepared library. Home features Acadia and its Watch and Details
controls. The rail contains Acadia only. The dark cinema composition, artwork,
fonts and controls are unchanged.

Both prepared Harbor and the simulated Harbor demo are absent from the
consumer catalog, so neither appears in Home, Details practice links or
How it works. The explanation about simulated pauses appears only when an
internal demo is actually offered. The existing gradient diagnostic remains
under How it works > Check playback while Acadia is available. If Acadia is
unavailable, the existing diagnostic fallback behavior remains; Harbor is never
substituted. No new footage was acquired or prepared.

The signed catalogs, media, maps, keys, reports and validation code are
unchanged. The retained regression catalog explicitly includes both Harbor
versions, Acadia and the diagnostic. Existing Harbor navigation, signature
and route substitution tests still use their exact artifacts. Consumer tests
use the real default catalog and real verification.

## Source evidence

See [the receipt](../../results/acadia-first-2026-10-16/receipt.json) for results
and commands. Before the production change, the new consumer tests failed
because the catalog included both Harbor entries and Home featured Harbor.
After the change, the consumer route exercises Acadia Watch and return,
Details > More info > Back > Back, Parents > cancel, and How it works without
a demo link or demo-only copy. Existing remote Back tests also run on the new
default; only the two explicit practice-demo regressions inject the retained
Harbor catalog. No safety threshold, detector or preset policy was changed.

The first broad run exposed the two historical practice-route assumptions.
They now use explicit regression fixtures, without removing their assertions.
The final suite excludes all four capture/export/measurement suites listed in
the receipt. Textual Jest snapshots are in-memory assertions, not screenshots.

## Owner steps

No action is needed while showing the current demo. Parent approval is needed
before replacing the running build, as requested in the delegation. After that,
build and install once, then check Acadia Home, Watch, Details and Back using the
remote. Visual focus, playback appearance and audio still need that native
check. Source tests do not establish native appearance or sound.

The detector-policy investigation is separate and remains inconclusive on
concurrent-area accumulation. This change contains no detector edits.
