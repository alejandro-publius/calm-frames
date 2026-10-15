# Open decisions and blockers

Updated October 15, 2026. Latest implemented source: `69df28c8215920ae5a1cc8e82a3124d4a68d65b3`.
Current package: `home-reading-a-2026-10-15`; native evidence is linked below.

The incoming source was `0e434dc7c89b7fb2dc19a9ca5d4593e5effa6c19`, integrated at
`b6b134c2402bd51e1048178e7e117744ff4ad4f3`. The isolated Mac review branch is
`codex/home-comparison-2026-10-15`. The latest rebuild and native status are in
[the Mac review receipt](../../results/home-review-2026-10-15/receipt.json).
Source tests, package preparation and native runtime are separate evidence.
Package 5 (`4016e8d`) is historical: it lacks the Parents cancellation focus fix.
The two [Home proposals](../design/home-comparison/index.html) are browser studies;
the owner subsequently delegated implementation, and A is selected. Its exact source,
build and native acceptance status are recorded in the Mac receipt above. B is retained
for comparison and has no native implementation.

The mini challenges remain optional.

## Mandatory before submission

Before distribution, Alex must resolve the Amazon sample notice scope and artwork
permissions/dedication decisions. Keep all existing notices; this review changes none
and contacts no third parties.

### 1. Final release selection: pending

The historical package 5, from `4016e8d`, carries the approved
coastal interface, the ledger and credits for its artwork, the hook mirror,
the fixes that hold the coastal menus to the ten foot floors, three Back
fixes, bundled copies of the practice stills and the opening readiness
fallback. It includes the simplified Home from `819de40` (one "Calm Frames"
heading, Play and Details, the practice demo reached from Details), the bordered
icon and tile, and the one-voice copy from `4016e8d`. Package 5 was driven on
the device and judged from its own log: eight journeys reported as happening.
Package 4's second pass separately reported pause, resume, the caption control
and a cover-first remote seek. The package, checks and owner's eyes-and-ears
checklist are in the handoff. Underneath it, the reliability candidate `cfddc4a` includes the Oct 14 playback recovery fix (a failed player setup
reaches the recovery screen at once) and the release helper fix that keeps a
supplied PIN out of reviewer documents. Its bounded checks passed
([`results/core-reliability-2026-10-14.json`](../../results/core-reliability-2026-10-14.json),
[`results/release-pin-license-review-2026-10-14.json`](../../results/release-pin-license-review-2026-10-14.json)).
A package built from it, with its 723 recorded source inputs verified, exists as
build output outside git in the reliability worktree and has not been installed
or run. The candidate has no hosted run because it has no pull request; the
`Vega app` job that failed on Oct 13 ran on the shared PR branch head `4c9996d`
and does not describe this candidate. `main` is at `7110893` and has not moved
since Sep 20.

**Needs:** Alex to select the exact commit or release reference judges will
use, after the native validation below. A merge to `main` and an immutable tag
are release choices, not stated hackathon requirements.

### 2. Composition A selected and implemented under delegated approval

Alex approved the ivory coast design with the dimensional coastal artwork; it
is applied in `b22d275` and held to the repository's floors in `93cf800`. What
remains is seeing it on the device (item 3). The artwork's ledger row records
its generation provenance without any ownership or dedication claim.

### 3. Latest native acceptance: use the Mac review receipt; eyes and ears pending

Package 5 from `4016e8d` was installed over the existing household and
driven on the Vega Virtual Device. Its breadcrumbs and media events reported
cold launch with Play focused, Home controls, Details and return focus,
Harbor start to finish with zero holds, the practice page and both holds with
the still loading, How it works, the Parents PIN gate and a relaunch onto the
saved Home
([`results/native-acceptance-5-2026-10-14/receipt.json`](../../results/native-acceptance-5-2026-10-14/receipt.json)).
Package 4's second pass reported pause and resume (J9), a cover-first remote
seek into the first hold (J10b) and the caption control (J11)
([`results/native-acceptance-4-2026-10-14/second-pass.json`](../../results/native-acceptance-4-2026-10-14/second-pass.json)).
The first seek attempt was too late; the retry reported seeking and seeked
events under the cover. These observations belong to their named packages.

The latest candidate's pixels and audio remain unobserved. The parent settings
interior needs the existing household PIN, and VoiceView and the caption menu's
contents are untested. Back from the PIN gate reported Home with Details
focused. Source `0e434dc7` now fixes this with button and remote regressions;
it is not in package 5. See the current Mac review receipt above for rebuild and runtime results. The checklist is
[FINAL_HANDOFF.md](../../FINAL_HANDOFF.md) section 4. Design approval is done;
native visual and audio acceptance is still pending.

**Needs:** Alex at the Mac with the simulator visible, entering the existing
household PIN himself, and the handoff's eyes-and-ears checklist. Keep household
data; no reset or new household is needed. Recording remains a separate
authorization.

### 4. The demonstration video: pending, recording not authorized

The rules require footage of the project on the simulator and a public YouTube
or Vimeo link. [DEMO_SCRIPT.md](DEMO_SCRIPT.md) is ready; nothing is recorded,
and recording is not yet authorized. The earlier English cut is of the Oct 10
build and was never uploaded.

**Needs:** authorization after items 2 and 3, a hosting account, a decision on
the narration voice (the earlier cut used disclosed macOS synthetic speech),
and a logged-out check of the link.

### 5. Reviewer access: pending

Either a public repository with the licence visible in About, or a private one
shared with `testing@devpost.com` and the six Amazon reviewers. Today the
repository is private, GitHub already detects Apache License 2.0, and the About
description and topics were empty at the Oct 14 check. Before public release,
settle the chosen code reference in item 1, review the audit exception dates in
`scripts/audit_exceptions.toml`, private vulnerability reporting, and item 7. The private
route needs invitations sent at submission and accepted within seven days.

**Needs:** Alex's choice and authorization before changing visibility or
inviting reviewers. Recheck the About box when preparing access.

### 6. Entrant details

Eligibility (age of majority, no Sponsor or Administrator affiliation) and the
contact email are marked NEEDS ALEX in [../SUBMISSION.md](../SUBMISSION.md)
section 15. There is no record of a Devpost registration in the repository.
Name, country and solo status are recorded.

### 7. Licence items before any public release

The release and licence lane owns the inspection; the decisions are Alex's.

- **Amazon's sample notices stay unresolved.** The player wrapper and the Shaka
  archive carry a proprietary notice beside the sample's MIT-0 grant. The Oct 14
  read-only inspection classifies this as an unresolved scope of permission due
  to contradictory notices, neither an attribution omission nor proof of a
  prohibition ([`results/release-pin-license-review-2026-10-14.json`](../../results/release-pin-license-review-2026-10-14.json)).
  The clarification request in
  [../AMAZON_SAMPLE_LICENSE_REVIEW.md](../AMAZON_SAMPLE_LICENSE_REVIEW.md) is
  unsent, and no answer from Amazon exists.
- **CC0 dedications.** The completion checklist asks Alex to confirm the CC0
  dedication of the generated Harbor artwork on Oct 21.
- **The illustrated harbor is now ledgered.** `app/assets/image/tv/harbor-illustrated.png`
  entered the tree on Oct 14 in commit `aa8dea1` and is a pixel-identical render
  of our own `app/assets/brand/tv/harbor.svg` at twice its size, verified
  locally by rendering the SVG and comparing every pixel. Its ledger row records
  that and asserts no new dedication.

## Optional mini challenges (do not block the submission)

### 8. Open Source: no contribution URL

The upstream fix for `AmazonAppDev/vega-video-sample` is prepared with its
tests ([../OPEN_SOURCE_PR.md](../OPEN_SOURCE_PR.md)) but no fork or pull
request exists: it needs a fork under Alex's GitHub account and a public author
identity. The alternative is to present the repository's own Apache-2.0
packages (flashmap, the Action, the sidecar specification, the hook) as the new
open-source project once the repository is public; whether a package inside the
primary repository satisfies the rule's "new, additional open-source project"
is not defined on the rules page.

**Needs:** the GitHub username to credit, the fork, and the choice of
contribution. Without a URL the mini challenge is simply not entered. The
local contract checks now pass, but this cloud session's duplicate recheck
returned `Forbidden` and must be completed before publication. The
prepared path can end at a public fork or branch: fork `AmazonAppDev/vega-video-sample`
under Alex's account, apply the two patches in `docs/upstream-pr/` with their
author line set to Alex's public identity, apply the third test patch and run all eight focused tests
as [../upstream-pr/README.md](../upstream-pr/README.md) describes, publish the contribution branch in the public fork after owner approval. A PR is optional;
it need not be opened or merged. Record the public fork/branch contribution URL,
project repository URL, GitHub username and description. Private patch files alone
do not qualify. Publication remains Alex's decision. This follows the
[official Open Source rule](https://amazonappdev2026.devpost.com/rules), checked October 15.

### 9. AWS Builder: enter or not, and the inactive cost tag

The Oct 9 deployment is documented, so the entry is possible. The `Project`
cost allocation tag was recorded inactive then. That historical record does
not establish the tag's current state, whether the budget now covers the
stack, the current bill or whether account credits cover its costs.

**Needs:** Alex to check the current tag and budget coverage, read the bill,
and decide whether to enter and whether to keep the stack up through judging.
The [cloud read-only checklist](../research/cloud-aws-check-2026-10-15.md)
adds deployed-digest and finding verification. Offline tests passed; live state
is blocked by absent AWS access and the historical findings remain unresolved.

## Also noted, not blocking

- Approval to publish the friction log and product feedback as written
  ([../SUBMISSION.md](../SUBMISSION.md) section 14).
- The private draft release `review-redesign-2026-10-10` holds the Oct 10
  build's package and video; replace or delete it before visibility changes.
- Devpost's early eligibility check on Oct 16 and the office hours on Oct 19
  are recorded from announcements and were not re-read.
- The form's exact field names and limits are unread; read them off the live
  form. The gallery image is proposed (`docs/brand/firetv-app-icon-1280x720.png`)
  and the form's accepted size is unknown.
