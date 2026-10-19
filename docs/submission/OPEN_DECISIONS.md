# Open decisions and blockers

Install status, October 19: nothing from the submission branch
`claude/ocean-layout-fix-2026-10-19` (head `7b3f5b2`) has been built or
installed. The last install with a receipt here is source `805f855` on October
18: one compile needed a bounded recovery of stale media staging, then all
package gates passed and one install completed, and its native text checks
cover all three full clips, Forest More info and How it works Back. The owner's
October 19 note says the Mac now has `2b78587` installed, which was never
pushed. No pixel/audio or owner acceptance is implied.

Product status updated October 19, 2026 for that branch.
Rule-source dates remain those recorded in the canonical checklist. The canonical lists are
[FINAL_REQUIREMENTS_CHECKLIST.md](FINAL_REQUIREMENTS_CHECKLIST.md), which maps
each mandatory rule to evidence, and [DEMO_RUN_OF_SHOW.md](DEMO_RUN_OF_SHOW.md)
for the video. This page keeps the decisions only the owner can make, and the
limits that bear on them.

## Mandatory for submission

### 1. Install the build to be shown, then accept it by eye and ear

Nothing from this branch has been installed. Its Ocean and Forest Home exists
only in browser renders
([evidence](../../results/home-islands-2026-10-19/README.md)), which show
composition, not native pixels. Once a build is installed, accept: the coastal
map with Ocean over Acadia and Sea otters and Forest over Forest, Watch and
Details on the sand, all three destination/Details flows, Acadia ocean
replacements near 7.3 s and 28.1 s, compact Skip, Acadia's retained audio track
(it measures -91 dB throughout, so its card says Silent), the intentionally
silent 19.987-second NOAA sea-otter excerpt and the Forest creek's original
nature audio. Text logs cannot approve layout or sound, and every native record
says visual and audio acceptance is pending.

### 2. Keep or drop the Mac's unpushed navigation work

The owner's October 19 note says the Mac has source `2b78587` installed, with
uncommitted navigation work. Neither is on GitHub, so neither has been read or
tested here, and the installed build is not this branch. To keep it: push it
and port it onto `app/src/calmframes/homeIslands.ts` rather than beside it, then
rerun the full app suite and the 24 layout tests in
`app/test/calmframes/homeIslands.test.tsx`. To drop it: install this branch in
its place. The rules ask for a repository holding all the source the project
needs (checklist section 6), so a recording of unpushed source would show
something judges cannot find.

### 3. Clear the footage question, then authorize the recording

The FAQ asks entrants to check third-party footage with the organizers. All
three clips are third-party government footage: NPS Acadia, the NPS Forest
creek (NPS: G Litten) and NOAA Fisheries sea otters. Office Hours #2 is Monday,
October 19, 9:00 am PT; the repository records no answer. No recording of the
current app has been made or authorized; the October 10 video in the private
draft release shows a superseded build.

### 4. Choose judge access

Either public, with the Apache-2.0 licence visible, which leaves the Amazon
sample notice question in item 8 open; or private, with the six Amazon
reviewers and the Devpost testing account invited. The submission source is
the private branch `claude/ocean-layout-fix-2026-10-19`. The repository's
default branch is still `main`, unchanged since September 20 and not the
submission source, so a repository URL without the branch name opens `main`.
Choose what judges are given: the branch URL, a new default branch or a merge.
The October 18 private handoff to `codex/creator-editions-2026-10-18` is
recorded in `results/github-coastal-handoff-2026-10-18/`. The repository holds
no record of invitations or access changes.

### 5. Register and complete the form

Registration, the eligibility statements and the form's own fields are
unverified. The drafts are [DEVPOST_DRAFT.md](DEVPOST_DRAFT.md) and
[../FEEDBACK.md](../FEEDBACK.md).

### 6. Engineering limits that bear on these

- The intermittent simulator slowdown is unresolved. Later runs were healthy
  and no fix is claimed, so a take can still be spoiled by it.
- The earlier `6f2570d` rechecked both Acadia replacement intervals, pause/resume, protected
  Skip, both real video identities, controls and return focus using native text logs.
- Forest creek is the approved 12-second excerpt with original nature audio,
  installed in `805f855` on October 18. Its exact catalog and existing signer were
  approved before activation; this branch's approved catalog is unchanged since then.
  The full Prairie Creek and Redwood source remains unapproved and outside the
  consumer catalog. The review staging tool alone never installs a title or enables Watch.
- The earlier setup/persistence and style/attribution fixes are included in the
  October 18 installed source, where 499 bounded app tests and 11 attribution tests
  passed. Those bounded runs missed 18 failures that the full app suite showed on
  `c84f95d`; on this branch the full app suite passes 1,676 tests with 0 failures
  (on `53a1c51`) and the full Python suite 1,880 with 0 failures (on `d9c9e2f`).
  The October 18 debug package is not a final release package. The WCAG-only
  legacy playback diagnostic remains unavailable under extra-cautious; its gate
  was not relaxed.
- Detection can miss flashing, and the prototype has not been medically
  validated. Independent detector assessment remains open. Physical TV acceptance
  is outside this simulator-only submission; unit tests establish neither.

## Owner and licensing items

### 7. Entrant details

Eligibility (age of majority, no Sponsor or Administrator affiliation) and the
contact email are marked NEEDS ALEX in [../SUBMISSION.md](../SUBMISSION.md)
section 15. There is no record of a Devpost registration in the repository.
Name, country and solo status are recorded.

### 8. Licence items before any public release

The release and licence lane owns the inspection; the decisions are Alex's.

- **Amazon's sample notices stay unresolved.** The player wrapper and the Shaka
  archive carry a proprietary notice beside the sample's MIT-0 grant. The Oct 14
  read-only inspection classifies this as an unresolved scope of permission due
  to contradictory notices, neither an attribution omission nor proof of a
  prohibition ([`results/release-pin-license-review-2026-10-14.json`](../../results/release-pin-license-review-2026-10-14.json)).
  The clarification request in
  [../AMAZON_SAMPLE_LICENSE_REVIEW.md](../AMAZON_SAMPLE_LICENSE_REVIEW.md) is
  unsent, and no answer from Amazon exists.
- **CC0 dedications.** The completion and approval checklist in
  [../SUBMISSION.md](../SUBMISSION.md) section 16 (item 9e) asks Alex to confirm
  the CC0 dedication of the generated Harbor artwork during the final checks,
  which [../STATUS.md](../STATUS.md) section 2 dates to Oct 21.
- **The illustrated harbor is now ledgered.** `app/assets/image/tv/harbor-illustrated.png`
  entered the tree on Oct 14 in commit `aa8dea1` and is a pixel-identical render
  of our own `app/assets/brand/tv/harbor.svg` at twice its size, verified
  locally by rendering the SVG and comparing every pixel. Its ledger row records
  that and asserts no new dedication.

## Product decision (does not block submitting the current three titles)

### 9. The package budget, or sharing duplicate preset copies

The prepared library uses 66,492,442 of its 67,108,864 byte (64 MiB) budget,
about 602 KB free, so no new clip of useful length can be imported. 37,144,901
of those bytes are byte-identical copies of a rendition that several presets
share; the unique content is 29,347,541 bytes. The current format cannot store
them once: the player and the verifier require each preset's rendition at its
own path, and each bundle's identity is the hash of a manifest listing those
files, which the approval registry pins. Choices: raise the budget, drop or
shorten a title, or approve a format change in the player, verifier, checker
and packager, which gives the four bundles new identities for owner approval
(no maps, signatures, media or presets would change). Nothing has been changed.
Evidence: [results/home-islands-2026-10-19](../../results/home-islands-2026-10-19/README.md),
"Still open".

## Optional mini challenges (do not block the submission)

### 10. Open Source: no contribution URL

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
local contract checks now pass, but the October 15 cloud session's duplicate
recheck returned `Forbidden` and must be completed before publication. The
prepared path can end at a public fork or branch: fork `AmazonAppDev/vega-video-sample`
under Alex's account, apply the two patches in `docs/upstream-pr/` with their
author line set to Alex's public identity, apply the third test patch and run all eight focused tests
as [../upstream-pr/README.md](../upstream-pr/README.md) describes, publish the contribution branch in the public fork after owner approval. A PR is optional;
it need not be opened or merged. Record the public fork/branch contribution URL,
project repository URL, GitHub username and description. Private patch files alone
do not qualify. Publication remains Alex's decision. This follows the
[official Open Source rule](https://amazonappdev2026.devpost.com/rules), checked October 15.

### 11. AWS Builder: enter or not, and the inactive cost tag

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
- Devpost announced an early eligibility check for October 16. The repository
  has no record of its use.
- The official rule pages were not re-read on October 19: the cloud session's
  network policy blocks devpost.com, so every rule quote keeps its October 17
  review date. Re-read them from a machine that can reach them.
- The pattern rule's published text precision was measured on a corpus whose
  colours are hard coded from the Oct 10 palette. Re-running it on today's
  colours would publish a new number, which is the owner's call
  ([evidence](../../results/home-islands-2026-10-19/README.md), "Still open").
- The form's exact field names and limits are unread; see section 11 of the
  [checklist](FINAL_REQUIREMENTS_CHECKLIST.md). The gallery image is proposed
  (`docs/brand/firetv-app-icon-1280x720.png`) and the form's accepted size is
  unknown.
