# Open decisions and blockers

Product status updated October 18, 2026 for installed source `1d14285`.
Rule-source dates remain those recorded in the canonical checklist. The canonical lists are
[FINAL_REQUIREMENTS_CHECKLIST.md](FINAL_REQUIREMENTS_CHECKLIST.md), which maps
each mandatory rule to evidence, and [DEMO_RUN_OF_SHOW.md](DEMO_RUN_OF_SHOW.md)
for the video. This page keeps the decisions only the owner can make, and the
limits that bear on them.

## Mandatory for submission

### 1. Accept the installed build by eye and ear

The coastal map, both destination/Details flows, Acadia ocean replacements near
7.3 s and 28.1 s, compact Skip, retained Acadia audio and the intentionally silent
19.987-second NOAA sea-otter excerpt. Text logs cannot approve layout or
sound, and every native record says visual and audio acceptance is pending.

### 2. Clear the footage question, then authorize the recording

The FAQ asks entrants to check third-party footage with the organizers.
Office Hours #2 is Monday, October 19, 9:00 am PT. No recording has been made
or authorized.

### 3. Choose judge access

Either public, with the Apache-2.0 licence visible, which leaves the Amazon
sample notice question in item 7 open; or private, with the six Amazon
reviewers and the Devpost testing account invited. The authorized handoff updates the existing private
`codex/creator-editions-2026-10-18` branch; the final remote commit is recorded in
`results/github-coastal-handoff-2026-10-18/`. No invitations or access changes are included.

### 4. Register and complete the form

Registration, the eligibility statements and the form's own fields are
unverified. The drafts are [DEVPOST_DRAFT.md](DEVPOST_DRAFT.md) and
[../FEEDBACK.md](../FEEDBACK.md).

### 5. Engineering limits that bear on these

- The intermittent simulator slowdown is unresolved. Later runs were healthy
  and no fix is claimed, so a take can still be spoiled by it.
- The earlier `6f2570d` rechecked both Acadia replacement intervals, pause/resume, protected
  Skip, both real video identities, controls and return focus using native text logs.
- Forest creek is a newly verified 12-second excerpt, pending exact catalog and packaging
  approval; the map preview cannot be selected. The original full Prairie Creek and
  Redwood remains an unapproved review example outside the
  consumer catalog. Staging records approval state only; it never installs a
  title or enables Watch.
- The earlier setup/persistence and style/attribution fixes are included in the installed
  source. 438 focused app tests and 11 attribution tests pass. The current debug package
  is not a final release package. The WCAG-only legacy playback diagnostic remains
  unavailable under extra-cautious; its gate was not relaxed.
- Detection can miss flashing, and the prototype has not been medically
  validated. Independent detector assessment remains open. Physical TV acceptance
  is outside this simulator-only submission; unit tests establish neither.

## Owner and licensing items

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
- Devpost announced an early eligibility check for October 16. The repository
  has no record of its use.
- The form's exact field names and limits are unread; see section 11 of the
  [checklist](FINAL_REQUIREMENTS_CHECKLIST.md). The gallery image is proposed
  (`docs/brand/firetv-app-icon-1280x720.png`) and the form's accepted size is
  unknown.
