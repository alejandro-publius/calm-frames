# Final requirements checklist

The canonical submission checklist. Updated on Saturday, October 17, 2026, in the evening,
Pacific time, against installed source `9cc57ca` and documentation commit `9f7cc6f`. The
official pages were read live on October 17. Older checklists in this repository point here.
This page is documentation only: nothing was built, installed, launched, recorded, pushed or
submitted to write it.

- **Installed build.** Branch `claude/tv-experience-2026-10-16`, app source `9cc57ca`,
  package SHA-256 `8f3636ec8bcc2a1c2d5ac80e26f7b3024c0b0ff9003bbdb1341569c51adecbfd`
  ([final clarity receipt](../../results/final-clarity-2026-10-18/README.md)).
- **Applied here.** The corrections in
  [SUBMISSION_RECONCILIATION.md](../SUBMISSION_RECONCILIATION.md) and the code-checked
  facts in [ARCHITECTURE_FACTS.md](../ARCHITECTURE_FACTS.md).
- **Status words.** **Done** means the evidence exists now. **Missing** means the item
  does not exist yet. **Unverified** means it may be satisfied, but nothing we can cite
  confirms it.

## October 18 engineering update

The private working branch `codex/creator-editions-2026-10-18` is now pushed at
`a11587e`; the GitHub owner and authenticated account match, visibility is private,
and the remote commit was verified. Judge invitations and submission remain owner
actions. The installed app source is `50bc01f`, with the static Debug fixture and
native evidence in `results/scene-bridge-native-2026-10-18/`.

A subsequent local follow-up fixes the native-input preflight, dependency patch
failure handling, personal-cover persistence recovery and the two failing style/
attribution gates. It also resolves verified file-digest secret-scan false positives
without allowing altered values. It is not pushed or installed yet. See
[the focused change record](../../results/release-blockers-2026-10-18/README.md).
No new content, signer, detector behavior, visual/audio acceptance or recording is
claimed. Dated older build and rule-source entries below retain their original context.

## Blocking now

1. **The demo video does not exist.** It needs owner visual and audio acceptance of the
   installed build, an answer from the organizers on the public domain park footage, the
   owner's authorization to record, and a take that the intermittent playback slowdown
   does not spoil.
2. **Judge access remains pending.** The demonstrated source is on the private
   `codex/creator-editions-2026-10-18` branch. Invitations or a different access
   route still need the owner; the local follow-up is awaiting review before push.
3. **Nothing has been entered on Devpost.** Registration, eligibility and the form's own
   fields are unverified. The text, feedback and track answers exist only as drafts.

## Sources

All read live on October 17, 2026.

| Page | URL |
| --- | --- |
| Overview | https://amazonappdev2026.devpost.com/ |
| Official rules | https://amazonappdev2026.devpost.com/rules |
| FAQ | https://amazonappdev2026.devpost.com/details/faqs |
| Schedule | https://amazonappdev2026.devpost.com/details/dates |
| Resources | https://amazonappdev2026.devpost.com/resources |
| Fire TV forum thread | https://amazonappdev2026.devpost.com/forum_topics/45517-about-fire-tv |
| Strong submission tips | https://amazonappdev2026.devpost.com/updates/46538-strong-submission-tips |
| Office hours | https://amazonappdev2026.devpost.com/updates/46771-office-hours-schedule |
| GitHub collaborator invitations | https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-access-to-your-personal-repositories/inviting-collaborators-to-a-personal-repository |

Not readable: the logged-in "Enter a Submission" form. Its fields are unverified; see
section 11.

## 1. Deadline and time zone

| Requirement | Status | Evidence or gap |
| --- | --- | --- |
| Submit before Friday, October 23, 2026, 12:00 pm Pacific Time (rules, section 2). The overview shows "Oct 23, 2026 @ 12:00pm PDT", which is 19:00 UTC. | Missing | Nothing is entered on Devpost. The project plan is to submit on Thursday, October 22. |
| "Once the Submission Period has ended, you may not make any changes or alterations to your Submission." | Missing | The video link, repository URL and text must be final before the deadline. |
| Everything stays reachable through judging. The rules give November 9 to November 20, 2026. The schedule tab starts judging on October 26. | Missing | Plan for October 26 to November 20: public video, reachable repository, accepted invitations. |

## 2. Eligibility

| Requirement | Status | Evidence or gap |
| --- | --- | --- |
| "at least the age of majority where they reside as of the time of entry" | Unverified | [SUBMISSION.md](../SUBMISSION.md) section 15 marks eligibility as needing the owner. |
| Not a resident of an excluded country or region (Brazil, Quebec, Russia, Crimea, Cuba, Iran, North Korea or a comprehensively sanctioned country) | Done | Section 15 records the United States as the country of residence. |
| Not an employee, representative or agent of Amazon or Devpost, or in their immediate family or household | Unverified | Owner statement needed. |
| Original work, owned by the entrant, infringing no one's rights | Unverified | Third-party code and media are credited in [NOTICE](../../NOTICE) and `media/LICENSES.csv`. The sample notice question in section 6 is open. |
| No funding, contract or commercial license from Amazon or Devpost | Unverified | Owner statement needed. |
| Registered for the hackathon | Unverified | The page read while logged out showed "Join hackathon". The repository holds no registration record. |

## 3. Track fit and judging

| Requirement | Status | Evidence or gap |
| --- | --- | --- |
| Fire TV: "launch a demo-ready app that works on Fire OS or Vega OS." | Done, simulator only | Source `9cc57ca` is installed and running on the Vega Virtual Device ([install record](../../results/final-clarity-2026-10-18/README.md)). No physical Fire TV device was used. |
| A simulator is accepted. FAQ: "a physical device isn't required at any stage of submission or judging." Forum answer: "Yes, virtual device demo is sufficient." | Done | Vega Virtual Device 1.0.67506.0, OS 1.2, Vega SDK 0.24.9914, Vega CLI 1.3.4. |
| Stage One is pass/fail: the project "reasonably fits the theme and reasonably applies the required APIs/SDKs." | Done, with a framing risk | The rules list "simple video player" as an obvious Fire TV idea. The description and video lead with the checked, signed safety layer, not with playback. |
| Stage Two scores four equal criteria: Tech Implementation, Design, Potential Impact, Quality of the Idea. Ties go to the first. Judging may use "automated AI-driven analysis". | Done in drafts | The Devpost draft ties each claim to evidence, since an automated reader may check them. |
| Tips page: "Name your track's tool in your project description, add it to your Built With section, and call it out clearly in your demo video." | Done in drafts | The Devpost draft and the run of show name Vega OS, the Vega SDK and the Vega Virtual Device. |

## 4. Platform integration

| Requirement | Status | Evidence or gap |
| --- | --- | --- |
| Fire TV: "The requirement is that the project runs on Fire OS or Vega OS." Any framework is accepted, and the runtime-import rule for other tracks does not apply. | Done | A React Native for Vega app, built and installed with the Vega CLI, playing through the Vega W3C media player, driven by the remote's D-pad. |
| No further integration is required. | Done | The rules require no Appstore submission and no particular API. Nothing is added only to qualify for a prize. |

## 5. Demo video

| Requirement | Status | Evidence or gap |
| --- | --- | --- |
| "should be less than three (3) minutes. Judges are not required to watch beyond three minutes" | Missing | [DEMO_RUN_OF_SHOW.md](DEMO_RUN_OF_SHOW.md), the canonical script, plans about 90 seconds. Nothing is recorded. |
| "should include footage that shows the Project functioning on the device for which it was built". Fire TV: an actual device or "the Fire TV/Vega simulator". | Missing | The plan records the Vega Virtual Device window. |
| "must be uploaded to and made publicly visible on YouTube or Vimeo" with the link on the form | Missing | The rules do not mention unlisted videos, so choose public. |
| "must not include third party trademarks, or copyrighted music or other material unless the Entrant has permission" | Unverified | Narration only, no music. Acadia is a public domain National Park Service clip. The FAQ asks entrants to "check with us on the specifics (how much of the video it makes up and how it's used) before finalizing." Ask at Office Hours #2, Monday, October 19, 9:00 am PT, or in the forum. Keep other apps, tabs and logos off screen. |
| English | Done in the plan | The narration is written in English. |
| Owner visual and audio acceptance before recording | Missing | The latest native record says `native_visual_audio_acceptance: false` ([final clarity](../../results/final-clarity-2026-10-18/native-results.json)). |
| Owner authorization to record | Missing | No recording is authorized by any document here. |
| A take free of the intermittent slowdown | Unverified | See section 9. |
| No unprotected flashing footage | Done in the plan | The run of show uses only the prepared Acadia copy with covers on, and a review page that shows no frames. |

## 6. Repository and judge access

| Requirement | Status | Evidence or gap |
| --- | --- | --- |
| A GitHub URL whose repository holds "all necessary source code, assets, and instructions required for the project to be functional" | Done for the private candidate | `a11587e` is verified on `codex/creator-editions-2026-10-18`. The local follow-up and judge access remain separate. |
| Public route: an open source license file, "detectable and visible at the top of the repository page (in the About section)" | Unverified | The root [LICENSE](../../LICENSE) is Apache-2.0. The repository is private today. Two sample files carry an "AMAZON PROPRIETARY/CONFIDENTIAL" notice beside the sample's MIT-0 grant ([review](../AMAZON_SAMPLE_LICENSE_REVIEW.md)); the clarification request is unsent. |
| Private route: share with the Devpost testing account and the Amazon team | Missing | Invite all six names the rules give, since one list has five and the other six: chris-trag, knmeiss, giolaq, anishamalde, mosesroth, emersonsklar. Read the testing account's address from the rules page; do not copy it into the repository. GitHub invitations lapse if not accepted within seven days, so check acceptance and re-send. Nobody is invited. |
| Setup instructions that work | Partly verified | A fresh tracked app tree passes TypeScript and strict asset checks using existing dependency versions. The new native preflight correctly identifies missing generated runtime files; full dependency download and Shaka compilation were not repeated. See the October 18 change record and [quickstart](REVIEWER_QUICKSTART.md). |
| "available free of charge and without any restriction, for testing, evaluation and use" | Missing | Follows from the chosen route. |
| Login credentials in the testing instructions if anything is private | Done, none needed | The app has no account. A reviewer sets their own Parents PIN on a fresh install. Private repository access is by invitation. |
| No keys in the code (tips: "Hide your API keys") | Checked locally | The pushed outgoing history and full blobs, including decompressed logs, were scanned. Findings were verified file digests/public test keys. The local follow-up adds exact digest exceptions and negative tests; hosted CI is not claimed. |

## 7. Required submission content

| Requirement | Status | Evidence or gap |
| --- | --- | --- |
| "a text description that should explain the features and functionality" | Done, draft | [DEVPOST_DRAFT.md](DEVPOST_DRAFT.md). |
| Product feedback "for each tool, API, or SDK used", answering five questions | Done, draft | [FEEDBACK.md](../FEEDBACK.md) answers all five for 18 tools. Its frame-count statement now names the run that produced it, against [friction entry 42](../FRICTION_LOG.md#42-the-player-never-reports-a-decoded-frame-on-the-virtual-device), and it records the October 17 slowdown. The Devpost draft carries a short version for the Vega tools. |
| Primary track | Done, draft | Fire TV. |
| Mini challenges | Unverified | Owner decision. None is required; see section 10. |
| "if the Entrant's Project existed prior to the Hackathon Submission Period", explain the significant update | Done, not applicable | The first commit, `387c173`, is dated September 17, 2026, after the window opened on August 31. No commit on any branch is older. The app began as a copy of Amazon's vega-video-sample, which NOTICE and the draft credit. |
| All materials in English | Done | |
| Friction log, optional, "up to 10% bonus" | Done | [FRICTION_LOG.md](../FRICTION_LOG.md) uses the requested fields. A link into a private repository opens only for invited reviewers, so paste the leading entries too. |

## 8. Asset licenses and disclosures

| Item | Status | Evidence or gap |
| --- | --- | --- |
| Acadia video, in the app and the demo | Done for the record, unverified for the video | NPGallery: "Public domain, Full Granting Rights; U.S. government work". Credit: "NPS Video, Acadia National Park. No NPS endorsement is implied." The More info page credits the National Park Service, and NOTICE and the credits screen come from the same ledger rows. |
| Prairie Creek and Redwood, the unapproved review example | Done for the record, not in the app | Ledger rows added in `076247a`. Per its proposal, the NPS source page treats NPS-credited material without a copyright symbol as public domain, and the park's B-roll page permits reuse. Credit: "NPS: G Litten". It is not in the consumer catalog, NOTICE or the credits screen. |
| Credits generated from the ledger | Done locally, not installed | Existing review-source rows now have titles; NOTICE and generated credits match the ledger. These acknowledgments do not add a consumer title or grant playback approval. |
| Amazon sample code (MIT-0) and Shaka Player (Apache-2.0) | Unverified | The proprietary notice question in section 6. |
| Fonts: Fraunces, Source Sans 3 and Inter | Done | SIL Open Font License 1.1, licence texts beside the fonts, sources in `app/assets/fonts/FONT_PROVENANCE.json`. |
| Artwork | Done | Every image has a ledger row in `media/LICENSES.csv`. The Acadia menu image is a still from the prepared video. |
| Safety wording | Done | The approved sentence is used word for word. The app also says "This prototype has not been medically validated." |
| AI-use disclosure | Done, not required | The rules ask for none. The analyzer is numeric and calls no AI service ([architecture facts](../ARCHITECTURE_FACTS.md)); AI-assisted development is a separate matter. |
| Flashing source files kept out of the repository | Done | `HAZARD_` files are gitignored. Only hashes and ledger rows are committed. |

## 9. What the evidence supports

Every native observation below comes from the Vega Virtual Device running a Debug package,
read from device text logs. Logs establish events, ordering, media clock and focus. They do
not establish pixels, sound or VoiceView. A logged "picture-shown" event is a readiness
gate, not proof of a visible frame. Each observation belongs to the build it was made on.

### Installed on the TV: Acadia playback

Source `9cc57ca`. Its consumer catalog is generated from exact approvals in
`app/config/approved-prepared-libraries.json`, and Home lists `consumerTitles(settings)`,
which today is Acadia alone.

- **Before delivery** the build checks packaged file hashes, signed maps and original
  reports. **At playback** the app verifies signed maps and matches the route and source
  metadata to its compiled approved catalog. It does not rehash every MP4 at playback.
- **On `9cc57ca`:** in the installed source, More info and How it works say "Calm Frames works only with prepared
  videos in this app, not other apps or live TV." and "Detection can miss flashing. This
  prototype has not been medically validated." Both routes, Parents cancellation and the
  return to Home Watch were logged. No media played in that check
  ([record](../../results/final-clarity-2026-10-18/native-results.json)).
- **On `6125459`:** Home, Details, Watch on the exact approved Acadia, the picture-shown
  gate, Back to Details, Home Watch and the natural end back to Home Watch were logged
  ([record](../../results/delivery-integration-2026-10-18/native-resume-results.json)).
- **On `3fab999`, October 17:** both cover intervals were logged with the "Scene ahead" and
  "Scene hidden" notice. Pause and resume during a cover kept Skip. Skip requested the cover
  before writing the playhead and released it only after the seek landed outside the
  interval. The natural end reached Home Watch in
  <!--n results/black-gap-2026-10-17/receipt.json:natural_end_to_home_ms -->339.652<!--/n--> ms,
  and manual Back in
  <!--n results/black-gap-2026-10-17/receipt.json:manual_back_to_home_ms -->312.196<!--/n--> ms.
  In the slow run of October 17, manual Back used the fallback teardown and reached Home
  after 2.257 s ([remaining controls](../../results/remaining-controls-2026-10-17/README.md)).
  The player, cover and guarded seek source files are unchanged since `3fab999`, but these
  controls were not repeated on later builds.

### Working on the Mac: local intake, review and staging

Evidence: [intake handoff](../LOCAL_INTAKE_HANDOFF.md),
[delivery integration](../DELIVERY_INTEGRATION_FINAL.md).

- A loopback page copies a chosen MP4 into a private workspace and analyzes the whole file
  under the WCAG 2.2 and ITU-R BT.1702-3 profiles. It shows raw flagged intervals apart from
  padded cover intervals, and covered time per preset. It never displays or serves video.
- Supported input: MP4, 8-bit H.264 yuv420p with AAC, 1 to 60 fps, at most 1280 by 720,
  60 seconds and 64 MiB. HDR, variable frame rate and embedded subtitles are refused, and
  DRM material is outside the workflow.
- Approval prepares, verifies and exports a package only with an authorized signer. One
  project signer was created with the owner's authorization in `076247a`.
- After export, the local tool can stage a delivery review, recheck its files or cancel the
  review. Staging records approval status; it does not install a title or enable Watch.
  The Acadia fixture recheck reads `approved_for_build` with `can_watch: false`
  ([record](../../results/delivery-integration-2026-10-18/acadia-fixture-check.json)).
- Focused tests, each from its own dated pass: the intake landed with
  <!--n results/local-intake-2026-10-17/receipt.json:tests_passed -->40<!--/n--> tests in `e27500b`;
  the delivery integration ran
  <!--n results/package-delivery-2026-10-18/receipt.json:python_tests -->55<!--/n--> Python,
  <!--n results/package-delivery-2026-10-18/receipt.json:node_tests -->32<!--/n--> Node and
  <!--n results/package-delivery-2026-10-18/receipt.json:app_tests -->59<!--/n--> app tests;
  the wording pass ran
  <!--n results/final-clarity-2026-10-18/verification.json:tests_passed -->43<!--/n--> tests in
  <!--n results/final-clarity-2026-10-18/verification.json:test_suites -->4<!--/n--> suites.
  They overlap and none is the full suite, so they are not added together.

### Not approved: Prairie Creek and Redwood

An earlier proposal, committed in `076247a`. Evidence:
[trust proposal](../NEW_VIDEO_TRUST_PROPOSAL.md),
[machine-readable proposal](../../results/new-video-package-2026-10-18/proposal.json).

- The 480p package passed all
  <!--n results/new-video-package-2026-10-18/proposal.json:verification_checks -->51<!--/n-->
  preparation checks with "cover proven drawn", and tampered copies were refused.
- It was never approved for the TV. It is frozen outside the consumer list, and no
  promotion is planned for this submission. If the demo shows its review page, call it a
  review example, not a title on its way to the TV.
- Its Extra cautious plan covers
  <!--n results/new-video-package-2026-10-18/proposal.json:presets.extra-cautious.intervals.0.start_ms -->15367<!--/n--> ms to
  <!--n results/new-video-package-2026-10-18/proposal.json:presets.extra-cautious.intervals.0.end_ms -->48967<!--/n--> ms of a
  <!--n results/new-video-package-2026-10-18/proposal.json:duration_ms -->50500<!--/n--> ms clip,
  most of it.
- A signature and a verified package show that files are intact and were checked. They do
  not establish medical safety.

### Unresolved

- **Owner visual and audio acceptance.** Home Watch beside Details, the Details bar, the
  explanation screens, the cover near 7.3 s and 28.1 s, the corner notice, and sound
  through covers.
- **Intermittent playback slowdown on the virtual device.** Two October 17 isolation runs
  showed
  <!--n results/native-slowdown-isolation-2026-10-17/receipt.json:experiments.fresh-app.media_span_ms -->6010<!--/n--> ms
  of video in <!--n results/native-slowdown-isolation-2026-10-17/receipt.json:experiments.fresh-app.wall_span_ms -->15560<!--/n--> ms,
  and <!--n results/native-slowdown-isolation-2026-10-17/receipt.json:experiments.fresh-simulator.media_span_ms -->5886<!--/n--> ms
  in <!--n results/native-slowdown-isolation-2026-10-17/receipt.json:experiments.fresh-simulator.wall_span_ms -->26435<!--/n--> ms
  after a simulator restart. A minimal SDK playback app, tested outside this repository,
  slowed the same way, and both later recovered with no code change. A later run advanced
  <!--n results/compact-scene-control-2026-10-17/native/summary.json:clock_segments.1.media_ms -->20894<!--/n--> ms
  in <!--n results/compact-scene-control-2026-10-17/native/summary.json:clock_segments.1.wall_ms -->20899<!--/n--> ms.
  The cause is unknown and nothing has fixed it.
- **An encoded near-black opening.** The Acadia source and its prepared copy are near-black
  from 0 to 4.963 s. That is in the content, not a cover.
- **Simulator only.** Physical Fire TV behaviour is not inferred.
- **Detection can miss flashing, and the prototype has not been medically validated.**

## 10. Optional mini challenges

Not required. A project "can only win one (1) track prize and one (1) mini challenge prize."

| Challenge | Rule | Status |
| --- | --- | --- |
| Open Source | "Create a new, additional open-source project or contribute to an existing public repository during the hackathon window". Needs a "contribution URL, project repository URL, GitHub username" and a description. | Missing. The vega-video-sample fix in [OPEN_SOURCE_PR.md](../OPEN_SOURCE_PR.md) has no public fork or branch yet. Whether packages inside the primary repository count is not defined. |
| AWS Builder | "Describe which AWS service(s) you used and how, in your Product Feedback answer." | Optional. The October 9 deployment is documented ([record](../../results/aws_deploy_2026-10-09.json)). The current TV app and local workflow do not call AWS. The rules note on October 7: "We are out of credit codes and will no longer be accepting credit requests." |

## 11. Form fields not yet seen

The "Enter a Submission" page needs a login. Fill these in from the live form before
pasting anything:

- [ ] Field names and character limits: ______
- [ ] Whether product feedback has its own field: ______
- [ ] Where the video URL, repository URL, track and mini challenges go: ______
- [ ] Whether a Built With field exists, as the tips page implies: ______
- [ ] Whether testing instructions have their own field: ______

## 12. Older documents and failing checks

These now point to the canonical checklist, script or description, or were corrected:
[REVIEWER_QUICKSTART.md](REVIEWER_QUICKSTART.md), [OPEN_DECISIONS.md](OPEN_DECISIONS.md),
[CHECKLIST.md](CHECKLIST.md), [DEMO_SCRIPT.md](DEMO_SCRIPT.md),
[DEMO_SCRIPT_ACADIA_2026-10-16.md](DEMO_SCRIPT_ACADIA_2026-10-16.md),
[the packet index](README.md), [FEEDBACK.md](../FEEDBACK.md),
[FRICTION_LOG.md](../FRICTION_LOG.md), [COMPLETION_CHECKLIST.md](../COMPLETION_CHECKLIST.md),
[SUBMISSION.md](../SUBMISSION.md), [SUBMISSION_COPY.md](../SUBMISSION_COPY.md),
[VIDEO_SCRIPT.md](../VIDEO_SCRIPT.md), [RUBRIC.md](../RUBRIC.md),
[SHOT_MANIFEST.md](../SHOT_MANIFEST.md) and the [docs index](../README.md).

Still open, each needing an app or owner decision:

- `eval/style_check.py` fails on one line of `app/src/calmframes/approvedPreparedCatalogs.ts`,
  generated from a dash in the Acadia label in `app/config/approved-prepared-libraries.json`.
  Fixing it changes app inputs.
- `eval/attribution.py --check` fails on the Prairie ledger rows, as in section 8.
- The root [README.md](../../README.md) points to the current state, but its body still
  shows October 14 renders and the older Harbor-first Home.
