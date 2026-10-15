# Mac implementation evidence, October 15

The machine-readable `receipt.json` identifies the exact source, package and
checks. `baseline-native.json` belongs to incoming source `b6b134c`, while
`selected-native.json` belongs to the selected layout at `69df28c`. Their
preparation receipts bind every app input and are distinct from runtime evidence.
The filtered event logs contain only app breadcrumbs and timing events; full
system logs remain local in `.logs/home-review/`. No screen or audio was captured.

The two layout studies live in `docs/design/home-comparison/`, served locally at
http://127.0.0.1:4186/docs/design/home-comparison/ . They also open directly as
a local HTML file. A was selected under the owner's delegated implementation
instruction; B is a browser proposal only.

The native driver was adapted from the historical non-capture driver. Each
package was installed and launched once. Between packages, this task terminated
only the baseline app it had launched so it could install the new source. It
never restarted the simulator, reset a household, entered a PIN or changed
credentials. Final app is left running for owner review.

The first build needed the existing generated Shaka distribution and polyfills.
They were copied into the isolated checkout, with all build inputs hashed in
the preparation receipt. A normal SDK build then hit the sandbox on the shared
workspace link. A separate writable SDK workspace was used with the unchanged
installed toolchain/packages; the original link remained pointed at the Claude
candidate. Network fetch, device access and localhost serving used approved
access. No approval denial was bypassed.

The full app run initially found one wording mismatch with the established
phrase 'two scheduled practice holds'. The sentence was corrected, then the
full non-capture gate passed. The historical test expectation that Details
uses a 184-unit title was updated to the selected shared 120-unit heading scale.

Log observations establish reported navigation, focus IDs, media events and
still-load callbacks. They do not prove actual pixels, audible continuity,
caption contents, visible focus contrast, VoiceView or protected settings.
Pause/resume, seek and caption menus were not re-observed in these sessions.
Those remain separate from the older package-specific evidence.
