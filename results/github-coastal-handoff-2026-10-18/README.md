# Private coastal-world GitHub handoff, October 18, 2026

Destination: `alejandro-publius/calm-frames`, existing private branch
`codex/creator-editions-2026-10-18`. Authenticated GitHub account and repository
owner both resolve to `alejandro-publius`; the repository reports private visibility
and push access. Remote base `59f23834885c3d15acaadac24d4ba912af06883e` is an ancestor
of the outgoing source. Delivery uses an ordinary fast-forward push. The final
remote SHA is reported after transfer; this committed preflight is not a push receipt.

## Installed demo

Source `6f2570da4165acc752882a0c04ffe996cd072880`, package SHA-256
`8311d90bc34db2efaae77a8a5eda144d7d45cc3989035558860c1b4604e3e63b` remains installed.
All 818 app-input hashes still match. No rebuild, reinstall or app relaunch was
performed during this handoff. The existing app remains open on Home with Acadia
selected and Watch focused. Native text checks confirm:

1. **Up, Right, Select** opens Sea Otters Details with Watch focused.
2. **Select** starts the exact approved NOAA clip.
3. **Back, Back, Left, Down, Left** returns to Home, Acadia Watch.

See `native-actions.jsonl`, `native-results.json` and `native-trace.log`.
The collector stopped. No capture, PIN operation or household inspection occurred.
Logs establish selection identity, event order and focus; they do not establish
pixel quality or audible playback. Sea Otters is intentionally silent.

## Review and validation

The installed source passed 534 focused app tests in 38 suites and 11 attribution
tests, TypeScript, lint with zero errors, native-input and media delivery gates.
The broader initial Jest run failed with heap exhaustion; after the duplicate
surface callback fix the bounded suites passed. No current full-suite pass is claimed.
The current native core walkthrough and limits are in
[the build evidence](../sea-otters-flow-2026-10-18/README.md).

This pass corrects README and submission copy only. The independent consistency
review identified and closed stale one-title descriptions, old package/source IDs,
outdated test claims, and the current font attribution. Exact remote keys match
saved native actions. Published-number and attribution checks pass. Outgoing
file contents, including earlier versions in outgoing commits, are secret-scanned
using the unchanged repository configuration before transfer. No detector,
credential, access-policy or AWS change is included.

## Source rights review

Official source pages were checked on October 18:

- [NOAA Sea Otters B-roll](https://videos.fisheries.noaa.gov/detail/video/2789953172001/b-roll%3A-sea-otters): NOAA identifies B-roll as public domain and requests NOAA Fisheries credit, subject to any extra slate attribution or permit conditions. The saved source/slate review records no external attribution or permit on this segment. The exact 19.986633-second silent prepared excerpt, source hashes and location evidence are in [provenance](../sea-otters-2026-10-18/provenance.json). The source original and rejected 40-second alternative are not added to the playable catalog or this outgoing media set.
- [NPS Acadia B-Roll Coastal Scenery](https://npgallery.nps.gov/AssetDetail/6fc09aec-7fc2-47ed-b8cc-e1b10861dd3e): the asset lists NPS Video credit and Public domain / Full Granting Rights. The current ocean rendition and approval remain unchanged.

NOTICE and generated credits match the 56-title ledger. This records source terms;
it does not settle the separate organizer footage question or Amazon sample notice.

## Minimum owner steps

1. Look at the open demo and listen to Acadia. Use the four keys above for Sea Otters; its silence is expected. Native logs cannot replace this acceptance.
2. Resolve the organizer question about third-party footage and the existing Amazon sample notice question before public release.
3. Confirm registration/eligibility, arrange authorized judge access, and approve the final submission package and form. A demo video is still absent; recording needs separate authorization.

No public publication, tag, release, main merge, access change or deployment is part
of this handoff. Physical Fire TV and VoiceView are unverified; they are not asserted
as mandatory rule blockers. The legacy Check playback utility remains unavailable
under extra-cautious because its map is WCAG-only. Rules were last reviewed October
17 in the submission checklist; this pass does not claim a fresh rule assessment.
