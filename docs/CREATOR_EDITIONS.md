# Creator editions and household picture covers

This branch adds three separate capabilities. It keeps the current Home composition.
Only exact-approved prepared editions can play. Detection can miss flashing; this
prototype has not been medically validated.

## Prepare and deliver an edition

The loopback intake still accepts only non-DRM MP4, 8-bit H.264/yuv420p with AAC,
at most 64 MiB, 60 seconds, 1280x720 and 60 fps. HDR, variable frame rate and embedded
subtitles are rejected. The original is never played by intake.

1. Open the configured local intake, select a rights-cleared file, analyze the whole
   file, and review the interruption schedule before preparation.
2. Prepare with an already authorized signer. Verification and export must pass.
3. Stage delivery, then choose **Show delivery plan**. The page reports the exact
   target checkout and approval tuple. It does not register trust or install software.
4. Have the owner approve the precise bundle ID, catalog digest and public-key
   fingerprint. Signing authority alone is insufficient. Record that exact approval
   in `app/config/approved-prepared-libraries.json`; do not change other approvals.
5. In an isolated checkout, run these commands with the plan's actual paths:

```sh
python -m pipeline.edition_delivery plan --staging-root REVIEW_DIRECTORY --ticket TICKET --app APP_DIRECTORY
python -m pipeline.edition_delivery apply --staging-root REVIEW_DIRECTORY --ticket TICKET --app APP_DIRECTORY
```

`apply` checks current package bytes and the target approval again, validates a
proposed copy, imports only missing immutable bundle/report files, and runs the
catalog generator and strict package gate. It preserves the regression catalog and
old bundles. Repeated application is idempotent. Failed validation rolls back only
files it added and its generated module, when they still match its writes. Use a
quiescent isolated checkout; this is not a general transaction against other editors.
A successful import still needs the checked build/install and native review.

Acadia exercises the already-approved path. The existing 20-second creator-controlled
Harbor fixture was used only for a staging regression, not new acquisition or fresh
analysis. Its delivery review and approval request are withdrawn: the owner disliked
that film and prefers real footage such as Acadia. It is not proposed consumer content. Prairie remains excluded;
its high coverage is not worked around by weaker detector settings.

## Add personal covers

On the TV, open **Parents**, unlock with the existing PIN, and choose **Extra picture
covers** beside a verified prepared title. Set start/end with the remote, review the
times and choose **Add these times**. The editor plays no video. Each addition has a
half-second guard on either side, clipped to the video. Up to 32 additions persist
locally for the household and exact source/rendition/duration/offset identity.

Removing an addition removes only that household entry. The immutable checked covers
remain. Changing edition or rendition does not reuse old additions. A malformed or
unreadable record blocks playback; the editor can retry reading it. There is no
silent reset of the record. A missing record means no additions. Back returns focus
to the title's Extra picture covers button.

## Write a scene bridge

Open `tools/scene-bridges/editor.html` locally in a browser. It needs no server and
loads no media. Supply the exact identity and the exact boundaries of an existing
base cover, then write a short verified description. The static preview and export
use ordinary text. Test fixtures are clearly labeled by default.

A bridge needs at least six seconds, at most 120 characters and 20 words, with two
seconds to settle plus half a second per word. The creator must confirm authorship.
Export makes a draft only. Review the words against the source separately, then pin
the exact JSON text and its SHA-512 in `approvedSceneBridges.ts`. This is compiled
presentation metadata, not signer or playback authority. No uploaded or route-supplied
checksum can authorize text. Changes require a fresh review and checked build.

The player checks exact identity, checksum and existing base-cover boundaries.
Personal additions cannot make an interval eligible. Missing, stale or malformed
metadata, short covers, loading, uncertain playback, pause, buffering and end keep
the ordinary cover. The text never changes cover timing, opacity, soundtrack or
controls. There is no generated narrative or live AI.

No real bridge text is registered in this branch. Acadia has no verified authored
narrative and its two Extra cautious covers are shorter than six seconds. Automated
tests use an explicitly labeled synthetic card description. The local editor is
reviewable without pretending that this fixture describes Acadia.

## Evidence and owner work

See `results/creator-editions-2026-10-18/` for focused source checks and native evidence.
Text logs establish route/focus events and guard/player state, not what the screen
looked like or whether audio sounded correct. Native checks of Acadia do not establish
native use of the PIN-protected personal editor or an unregistered bridge fixture.

The owner supplies suitable rights-cleared source media and verified scene wording,
approves any future exact new tuples, and performs the final look/listen acceptance. The current
PIN stays private. Capture, publication and submission remain separate actions.

## Development-only scene-bridge presentation test

A Debug build exposes **Home → How it works → Scene bridge test**. Release
builds have neither an entry nor a rendered fixture. This explicitly labeled static
test uses “Test fixture: a card displays one.” with pinned synthetic metadata and
no media, persistence or registry entry. **Test stale identity** requests the ordinary
opaque cover; **Show test text** restores the verified test description. **Skip test
and return** or remote Back restores focus to Scene bridge test; the next Back
returns to Home → How it works. Production cover eligibility and guard paths are
unchanged. This is presentation verification, not approval of any real narrative.

See `results/scene-bridge-native-2026-10-18/` for its separate verification record.
