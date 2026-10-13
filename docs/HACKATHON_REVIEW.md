# Calm Frames: hackathon assessment, October 2

**Baseline estimate before the Oct 2 follow-up: <!--n results/hackathon_review_2026-10-02.json:overall_out_of_100 -->70<!--/n-->/100.
Submission readiness: incomplete.** This is a subjective engineering and product
assessment, not an official Devpost score or a probability of winning. It reviews
source and recorded evidence before today's demo work. No new native playback
was observed for this score. Shipping more code does not automatically raise it.

The live [rules](https://amazonappdev2026.devpost.com/rules) use equally weighted
Tech Implementation, Design, Potential Impact and Quality of the Idea criteria.
They publish no numeric scoring scale. The scale below is ours; no discretionary
friction-log bonus is assumed.

| Criterion | Estimate out of 10 | Evidence and remaining gap |
|---|---:|---|
| Tech Implementation | <!--n results/hackathon_review_2026-10-02.json:scores.tech_implementation -->7<!--/n--> | Signed maps, guarded seeks, checked renditions, scene holds and durable household state have substantial tests. Current physical composition, transport behavior and delivery integrity remain unproved. |
| Design | <!--n results/hackathon_review_2026-10-02.json:scores.design -->6<!--/n--> | Family profiles, viewing plans and conservative error states form a coherent TV flow. The existing gradient cannot demonstrate captions or holds, and current native navigation lacks a recorded walkthrough. |
| Potential Impact | <!--n results/hackathon_review_2026-10-02.json:scores.potential_impact -->6<!--/n--> | A specific audience and plausible analyzer/hook adoption paths. Local integration checks exist; no outside feedback, independently adopted app integration or studio use is recorded. |
| Quality of the Idea | <!--n results/hackathon_review_2026-10-02.json:scores.quality_of_idea -->9<!--/n--> | Advance analysis, authenticated playback instructions and context-preserving holds make a distinctive accessibility project. The submission must show that complete experience. |

The later terminal follow-up completed the benign fixture, a real checked
preparation-to-package-to-shelf path, exact archive checks and current Debug and
Release builds. The full corrected conformance evaluation is underway. These
changes are recorded in [STATUS.md](STATUS.md); the table above remains the
original assessment, not a new score. Native footage and outside comprehension
feedback remain missing, so this update does not claim a higher score.

## What judges still cannot see

The [official requirements](https://amazonappdev2026.devpost.com/) call for a
public English YouTube or Vimeo video under three minutes, showing the app on
a Fire TV device or simulator. The deadline is October 23 at noon PDT. We do
not have that video, a final judged release or confirmed reviewer access.
The current private repository can qualify through the named reviewer-access
route; public release remains our chosen plan. See [SUBMISSION.md](SUBMISSION.md).

The separate Open Source contribution URL is still missing. The AWS stack is
synthesized and tested, not deployed. Neither mini challenge is complete merely
because its field is selected. The friction log can support a discretionary
bonus, but this review assumes none. Reviewers may assess the submission from
its text and video without running the code.

The strongest missing demonstration is a single journey: a parent chooses a
profile, sees the title's plan, plays a prepared title, follows captions through
a scene hold and resumes the same household after restarting. The implementation
has pieces of this journey; tests and old simulator footage do not establish the
current complete experience.

## Evidence that constrains the score

- The archived conformance run kept
  <!--n results/conformance.json:published.clips_kept -->467<!--/n--> of
  <!--n results/conformance.json:published.clips_designed -->3000<!--/n-->
  designed clips. Recall was
  <!--n results/conformance.json:published.flashmap_recall -->0.895<!--/n-->
  over <!--n results/conformance.json:published.flashmap_recall_denominator -->324<!--/n-->
  positive windows overall, and
  <!--n results/conformance.json:published.recall_near_limits -->0.575<!--/n-->
  over <!--n results/conformance.json:published.recall_near_limits_positive_windows -->80<!--/n-->
  positive windows near limits. This partial run cannot support comprehensive
  detection claims.
- Simulator software timing records
  <!--n results/gate1_software_vvd.json:in_time -->48<!--/n--> on-time results
  from <!--n results/gate1_software_vvd.json:trials_attempted -->55<!--/n-->
  attempts. The <!--n results/gate1_software_vvd.json:trials_counted -->49<!--/n-->
  measurable trials are a narrower denominator: six attempts yielded no usable
  evidence, and one measurable trial was late. Neither is screen-level timing.
- [VALIDATION.md](VALIDATION.md) contains no collected outside feedback.
- [Local preparation](../pipeline/local_library.py) verifies outputs but does
  not connect them to the TV catalog. A trusted source hash in a map is distinct
  from verifying the exact rendition that reaches the player.
- Native builds passed in the prior local check. Fresh GitHub Actions status
  could not be fetched in this sandbox; the last recorded hosted attempt failed
  before runner startup. This review does not promote that historical result to
  current CI evidence.

## Push the project further through story continuity

The central product promise should be understandable on screen: **keep following
the story when a scene is covered.** A checked context image, captions and audio
make that concrete. Three connected improvements would strengthen the project.

| Priority | Deliverable | Acceptance evidence |
|---|---|---|
| Now | A self-contained benign captioned story, with explicitly labelled sham holds and conservative fallback | Analyze source and outputs; verify signatures and packaged bytes; demonstrate every preset; capture current native playback with captions visible and audio continuing. A sham interval is never counted as a detected hazard. |
| Next | Local preparation to the TV shelf | Prepare an owned file, verify it, admit its exact covered rendition, then play it with the required preset maps. Replaced bytes, a missing profile, changed map, failed receipt or unavailable delivery must keep it out. Complete the identity and delivery contract before exporting URLs. |
| Before feature freeze | Evidence of comprehension and developer reuse | Observe consenting reviewers using only static material or approved benign assets; record confusion and resulting changes. Install the packed hook into a separate minimal Vega app and demonstrate guarded transport. Report actual observations, not inferred endorsement. |

The first row is being implemented in the October 2 follow-up. Its native
demonstration remains an acceptance requirement until captured. A passing media
analysis does not prove TV-layer composition or clinical safety.

An optional later experiment is creator-reviewed text that describes hidden
story action. Keep it outside all detector and scheduling decisions, disclose
its origin and prove the schedule is identical with text generation disabled.
Do this only after the complete viewing journey works. A generic chatbot or
additional cloud services would add less evidence for today's largest gaps.

## The opening of the eventual demo

Start with the family choosing a title and show the scene hold early. Keep a
visible label explaining that the clip has no flashing and uses sham intervals.
Show the captions continuing and a guarded seek using the remote. Show the
title's check and the household setting, then briefly explain the signed map
and preparation pipeline. Close with the measured limits and the reusable hook.

Use actual device or simulator footage. Keep the safety sentence intact:
Calm Frames reduces exposure to flashing above published limits in the videos it
plays; not a medical device. It does not protect content in other apps.
