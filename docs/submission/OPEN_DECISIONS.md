# Open decisions and blockers

Current working candidate: `codex/prepared-video-slice-2026-10-15`, app source
`21f0ea60332b83efe960eb7cf799139ec2d82ae9`. See
[FINAL_HANDOFF.md](../../FINAL_HANDOFF.md) and the
[focus-fix receipt](../../results/transport-focus-2026-10-15/receipt.json) for
the exact installed package and bounded native observations. The approved
Acadia integration is retained; historical package 5 and the old draft ZIP
are not the current candidate. Final judged release selection remains open.

## Engineering and owner acceptance

- The earlier Forward-button check targeted an automotive-only control.
  The real issue was background Details/Home controls taking focus. The
  regression fix and correct TV seek-bar check are in the current receipt.
- Owner checks still needed: readable analysis, visible focus and Back route,
  prepared picture holds, optional menu cue, audio continuity, captions and
  VoiceView. Keep the saved household; only the owner enters the existing PIN.
- Detection can miss flashing. Native log ordering is not paint timing.
  Independent detector assessment, physical-TV acceptance and loop-seam
  validation remain open; none is replaced by unit tests.
- Choose the final source/package after acceptance. No main merge or release
  tag has been made. The working branch is private and the old release/ZIP
  assets are historical.

## Recording and access

The revised [demo script](DEMO_SCRIPT.md) is a draft only. Recording and public
upload require separate authorization. No old screenshots or video should be
presented as the current build. Reviewer access also requires the owner's
chosen route and authorization; nobody has been invited by this pass.

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
- Devpost's early eligibility check on Oct 16 and the office hours on Oct 19
  are recorded from announcements and were not re-read.
- The form's exact field names and limits are unread; read them off the live
  form. The gallery image is proposed (`docs/brand/firetv-app-icon-1280x720.png`)
  and the form's accepted size is unknown.
