# Final layout and copy evidence, October 15

`receipt.json` identifies the final source and exact package. `preparation.json`
binds 736 app inputs to committed source. Build evidence and native evidence
are separate. The earlier `home-review-2026-10-15` directory records the baseline
and layout-only versions; this directory supersedes them for final acceptance.

The copy audit is in `docs/design/PLAIN_LANGUAGE_REVIEW.md`. Layout A is implemented;
layout B remains a browser comparison. The comparison starts in grayscale and
uses the existing fonts, art and approved colors. No screenshot, recording or
pixel inspection was performed. Browser assertions inspect DOM geometry and focus.

Lint passed with 97 source warnings and four test warnings, all present in the
layout-only log too. This corrects the earlier summary that counted only four.
The hook consumer was rerun with the pinned Node 22 after its expected Node-version
guard rejected the default Node 26. No dependency or engine behavior was changed.

Native results and filtered app events record all seven passing journeys in
the single final-package session. Full device logs stay local. They can establish reported routes, focus,
media events and still-load callbacks. They cannot establish sight, sound,
caption pixels, VoiceView or protected settings. Pause/resume, seek and the
caption menu were not repeated. No household reset, PIN entry or simulator
restart was performed. The final app remains open for the owner.
