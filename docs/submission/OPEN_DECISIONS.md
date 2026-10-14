# Open decisions and blockers

Oct 14, 2026. Only items that stop the submission or that Alex alone can
decide, in order of how much they matter to Stage One (pass or fail on a
working, demonstrated app) and then to the mini challenges. Where evidence does
not exist, the row says so instead of inventing it.

## 1. No native run or video of the final app (blocks Stage One)

The rules require footage of the project running on a Fire TV device or the
Vega simulator, and a public video link. No build of the current source
(`af192ac`, or whichever line is chosen in item 2) has been installed, observed
or recorded. The two Oct 14 packages were built but never launched
(`results/concise-copy-2026-10-14/ARTIFACT_MANIFEST.json`,
`results/dusk-lantern-integration-2026-10-14/ARTIFACT_MANIFEST.json`). The last
native sessions were on `06190c7` (Oct 13) and `dba88d5` / `00905510` (Oct 14),
and both stopped short: the parent-area interior needs the test household's PIN,
which only Alex has, and the Oct 14 session ended when the Mac locked and could
not be unlocked by the agent. The earlier English cut is of the Oct 10 build and
was never uploaded.

**Needs:** Alex at the Mac, unlocked, with the simulator visible; a fresh test
household or the existing PIN entered by Alex; then the steps in
[../MAC_FINISH.md](../MAC_FINISH.md) and [DEMO_SCRIPT.md](DEMO_SCRIPT.md); a
YouTube or Vimeo account for the upload; a logged-out check of the link.

## 2. Which source becomes the judged release (blocks items 1, 3 and 4)

Four lines exist and none is marked final: the shared PR branch
`codex/signed-scene-holds-2026-09-29` at `4c9996d` (hosted `Vega app` job red
on Oct 13), the packet base `codex/dusk-lantern-integration-2026-10-14` at
`af192ac` (no hosted run, no native observation), the native validation line
`codex/native-design-validation-2026-10-14` at `00905510` (observed, older
copy), and the reliability lane `codex/core-reliability-2026-10-14` still in
flight. `main` is at `7110893` and has not moved since Sep 20. A public
repository shows `main`, and the judged tag must never move once it exists.

**Needs:** Alex to name the integration order and the one head that gets
built, observed, recorded, merged to `main` and tagged. Evidence of a green
hosted run on that head does not exist yet.

## 3. Repository access route (blocks Stage One if neither is done)

The rules allow either a public repository with the licence visible in About,
or a private one shared with `testing@devpost.com` and the six Amazon reviewers.
Today the repository is private, GitHub already detects Apache License 2.0, and
the About description and topics are empty. Going public needs the merge in
item 2, the audit exception dates in `scripts/audit_exceptions.toml` moved past
Dec 3, private vulnerability reporting switched on, and item 6 settled. The
private route needs the invitations sent at submission and accepted within
seven days.

**Needs:** Alex's choice, and the About box filled in either way. Only the
owner can change visibility or add collaborators.

## 4. Open Source mini challenge: no contribution URL

The upstream fix for `AmazonAppDev/vega-video-sample` is prepared with its
tests ([../OPEN_SOURCE_PR.md](../OPEN_SOURCE_PR.md)) but no fork or pull
request exists, because it needs a fork under Alex's GitHub account and the
patches need a public author identity. The alternative is to present the
repository's own Apache-2.0 packages (flashmap, the Action, the sidecar
specification, the hook) as the new open-source project once the repository is
public; the rule text says "a new, additional open-source project", and
whether a package inside the primary repository satisfies "additional" is not
defined anywhere on the rules page.

**Needs:** the GitHub username to credit, the fork, and the choice of
contribution. Without a URL the mini challenge cannot be entered.

## 5. Entrant details

Eligibility (age of majority, no Sponsor or Administrator affiliation) and the
contact email are marked NEEDS ALEX in [../SUBMISSION.md](../SUBMISSION.md)
section 15. There is no record of a Devpost registration in the repository.
Name, country and solo status are recorded.

## 6. Licence items before any public release

Owned by the release and licence lane; the decisions are Alex's. The Amazon
sample's player wrapper and Shaka archive carry a proprietary notice beside the
sample's MIT-0 grant, and the clarification request in
[../AMAZON_SAMPLE_LICENSE_REVIEW.md](../AMAZON_SAMPLE_LICENSE_REVIEW.md) is
unsent (the plan had it due Oct 13). The CC0 dedication of the generated Harbor
artwork is for Alex to confirm. `app/assets/image/tv/harbor-illustrated.png`
has no row in `media/LICENSES.csv`. No evidence of an answer from Amazon exists.

## 7. AWS Builder: enter or not, and the inactive cost tag

The stack is deployed and documented, so the entry is possible. The `Project`
cost allocation tag was inactive on Oct 9, so the 20 dollar budget cannot
warn anyone; whether the credits on the account cover this stack has not been
verified in Bills. The stack is planned to stay up until about Dec 3. Nothing
in the repository shows the current bill.

**Needs:** Alex to activate the tag, read the bill, and decide whether to
enter the mini challenge and whether to keep the stack up through judging.

## 8. Approval to publish the friction log and product feedback

Both name real defects in Amazon's tools with exact output. Alex has not yet
confirmed they go out as written ([../SUBMISSION.md](../SUBMISSION.md) section 14).

## 9. Narration voice and hosting

The earlier cut used macOS synthetic speech, disclosed on screen. Decide whether
to keep that or record a voice, and which account hosts the video.

## 10. The Oct 10 draft release on GitHub

A private draft release (`review-redesign-2026-10-10`) holds the Oct 10 build's
package and video. Decide whether it is replaced by the judged release or
deleted before the repository changes visibility.

## Also noted, not blocking

- Devpost's early eligibility check on Oct 16 and the office hours on Oct 19 are
  recorded from announcements and were not re-read.
- The form's exact field names and limits are unread; read them off the live form.
- The gallery image is proposed (`docs/brand/firetv-app-icon-1280x720.png`) and
  the form's accepted size is unknown.
