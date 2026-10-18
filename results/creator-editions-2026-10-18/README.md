# Creator editions implementation receipt

Source `ce3fae8bd404355c1d3e863887ff7a96d50a9672`, isolated branch
`codex/creator-editions-2026-10-18`, is built and installed on the Vega Virtual Device.
The original checkout remains clean. Nothing was pushed or published.

## Implemented

- Repeatable checked import of an exact-approved edition, with plan/recheck, immutable
  copy, generated catalog check, strict package gate and owned-file rollback. The
  intake page exposes the plan. It cannot approve a tuple, build or install.
- PIN-protected household extra-cover editor, persisted per exact title/source/
  rendition/duration/offset. Additions union with immutable base covers; load failure
  blocks playback. Remove, retry and Back have explicit focus targets.
- Authored scene bridge validation, exact checksum/asset/base-interval matching,
  opaque static presentation and local draft editor. No narrative is registered.
  Acadia has no verified authored text and no qualifying six-second base cover.

See [the workflow](../../docs/CREATOR_EDITIONS.md). Open
`tools/scene-bridges/editor.html` directly in a browser for the authoring tool.

## Verified

206 focused tests pass: 78 Python, 110 React/guard/storage, 8 editor and 10 hook tests.
TypeScript, Ruff, focused ESLint (zero errors, seven warnings), staged style,
whitespace and scoped secret scan pass. Independent review found and fixed stale
intake plans after retry and disappearing editor focus targets. A mutation removing
base coverage failed the monotonic-union test as intended.

Acadia's already-approved delivery applied idempotently: no assets or approvals
changed. Harbor's existing creator-controlled 20-second fixture passed strict staging,
and was then canceled as a consumer candidate. The owner disliked Harbor and prefers
real footage. This was fixture reuse for delivery validation, not new footage
acquisition or fresh analysis. Prairie remains excluded.

There were four build invocations: three failed before packaging due to the isolated
worktree's dependency symlink, a stale Metro directory entry and missing ignored
Shaka outputs. A local copy of existing dependencies, a worktree-specific file cache
and copied existing generated outputs resolved them. No dependency versions or
shared Watchman configuration changed. The fourth build passed with all 779 app and
generated inputs unchanged. The inputs and generated-output hashes are recorded.

The package was installed once and launched once. Its on-device SHA-256 matches:
`9178bdfc5fa0d85d7e3b64a3de5b9fec461e7de17bd768c2d3ff7cea3d2d3bc3`.
The package is at:
`build/release/creator-editions-2026-10-18/calm-frames-editions-aarch64-debug.vpkg`.

Text logs establish nine completed checks: More info and How it works routes/Back,
Parents cancellation returning to Parents, Acadia selected through Details, playback
Back returning to Details, and Home Watch playing through natural end and returning
to Home Watch. The initial launch focus trace was absent; later explicit remote-key
focus transitions were observed. The collector stopped. The app remains Home Watch.

## Limits and approval

No capture, screenshot, video/audio recording, original-video playback, external
publication, trust registration or signing change occurred. Text events do not prove
pixel appearance or audio quality. The private PIN was not entered; personal-editor
native use remains an owner check. No registered bridge was tested natively. Those
capabilities have headless tests, not native visual acceptance. No detector can
promise seizure prevention; this prototype has not been medically validated.

Historical Harbor identity, retained only to identify the canceled staging regression.
No approval is requested and no consumer registration is proposed:

- Bundle: `51b91d7413c50cc020452d4594a493fbf78e6d1ebac40c8066753b76c776d101`
- Catalog: `02f76715d81d263deb556433cb3ddb914ea9c1d8820f9f8054719dda71b88b79`
- Public-key fingerprint: `a3240e9daf33984511014cd7434803ab05a6e8816081f3f0ccfd94995208186b`

The earlier approval request is withdrawn, and the staging ticket is canceled. Neither
an unanswered question nor earlier signing authority grants new consumer trust.
The original review JSON is historical; `harbor-canceled-review.json` is current.

Personal-cover native verification needs the owner to unlock Parents privately and
leave that screen open. No PIN needs to be shared, reset or bypassed. Extra covers
are household-wide, so a test profile does not isolate them; any test addition must
be removed afterward while retaining all existing additions.

There is no supported native scene-bridge fixture route in this build. The only
runtime integration is the accepted prepared-player route with an empty compiled
registry; fixtures exist in unit tests and the local editor. Native fixture testing
would require a separate presentation-only test route and a new build. Acadia must
not be assigned invented narrative or stretched cover boundaries to provide a test.

The local working checkout was fast-forwarded from `639066b` to `787fdea`; all 779
installed app inputs match and its strict package gate passes. Git main and remote
refs were unchanged. The idle intake service was reloaded once at
http://127.0.0.1:8766 with identical arguments, all four jobs and signer status
preserved. The new plan page is live. No key bytes were inspected or changed.
See `integration-receipt.json` and `intake-integration-receipt.json`. Subsequent
documentation commits do not change installed app inputs. Publication and submission
remain separate.
