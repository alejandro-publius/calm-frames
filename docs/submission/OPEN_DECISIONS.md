# Open decisions and blockers

Updated Oct 14, 2026 (evening) for the final integration candidate
`claude/final-candidate-2026-10-14`, package source `93cf800`
([FINAL_HANDOFF.md](../../FINAL_HANDOFF.md)). It is a candidate, not the
final judged release. Mandatory items come
first; the mini challenges are optional and do not block the submission. Where
evidence does not exist, the row says so instead of inventing it.

## Mandatory before submission

### 1. Final release selection: pending

The final candidate `93cf800` carries the approved coastal interface, the
ledger and credits for its artwork, the hook mirror and the fixes that hold
the coastal menus to the ten foot floors; its package and checks are in the
handoff. Underneath it, the reliability candidate `cfddc4a` includes the Oct 14 playback recovery fix (a failed player setup
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

**Needs:** Alex to name the head that becomes the judged release, after the
visual approval and native validation below, then the merge to `main` and the
tag that never moves.

### 2. Final visual approval: done on Oct 14

Alex approved the ivory coast design with the dimensional coastal artwork; it
is applied in `b22d275` and held to the repository's floors in `93cf800`. What
remains is seeing it on the device (item 3). The artwork's ledger row records
its generation provenance without any ownership or dedication claim.

### 3. Native validation: pending

No build of the final candidate has been installed, observed or recorded; the
acceptance checklist is in [FINAL_HANDOFF.md](../../FINAL_HANDOFF.md) section 3. The last
native sessions were on `06190c7` (Oct 13) and `dba88d5` / `00905510` (Oct 14),
and both stopped short: the parent-area interior needs the test household's
PIN, which only Alex has, and the Oct 14 session ended when the Mac locked. The
final walkthrough waits for item 2.

**Needs:** Alex at the Mac with the simulator visible, a fresh test household
or the existing PIN entered by Alex, and the steps in
[../MAC_FINISH.md](../MAC_FINISH.md).

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
description and topics are empty. Going public also needs the merge in item 1,
the audit exception dates in `scripts/audit_exceptions.toml` moved past Dec 3,
private vulnerability reporting switched on, and item 7 settled. The private
route needs invitations sent at submission and accepted within seven days.

**Needs:** Alex's choice; only the owner can change visibility or add
collaborators, and the About box is empty either way.

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
contribution. Without a URL the mini challenge is simply not entered.

### 9. AWS Builder: enter or not, and the inactive cost tag

The stack is deployed and documented, so the entry is possible. The `Project`
cost allocation tag was inactive on Oct 9, so the budget cannot warn anyone,
and whether the account's credits cover this stack has not been verified in
Bills. Nothing in the repository shows the current bill.

**Needs:** Alex to activate the tag, read the bill, and decide whether to
enter and whether to keep the stack up through judging.

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
