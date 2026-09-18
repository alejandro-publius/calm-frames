# Plan

The full plan is docs/BUILD_PROMPT.md. This is the short version with where
each phase actually stands, so a fresh session does not have to read the long
one to know what to pick up. Live state is docs/STATUS.md and docs/GATES.md.

Submit Thu Oct 22, 2026. The deadline is Fri Oct 23 at 12:00 PT.

## The thesis

A verified safety layer for kids with photosensitive epilepsy, not a video
player. Every frame of a title is checked before it can play in kid mode, and
the result is a signed flash map. The player hides each flagged segment before
it starts while sound and captions keep going. Household settings can only
make it stricter than WCAG. Voice, D-pad and cards behave as one flow, and
every seek path is safe. Any Vega video app can add it with a small hook.

## Where each phase stands

| Phase | What it is | State |
|---|---|---|
| 0 | Machine, repo, licence, CI | Done. CI green on ubuntu runners. The head-start kits never arrived, so everything they were meant to bring was written here. |
| 1 | Vega day-one probes | Done on the virtual device. The app plays a Blender title and the cover harness runs. The parts that need a screen wait for the stick. No timing number yet: see below. |
| 2 | flashmap v1 and screening day | flashmap v1 is built and tested. Screening media is downloaded with licences recorded. GATE 2's target is already met. |
| 3 | Pipeline and Plan B | Local pipeline, verify step and CDK skeleton are in. Nothing is deployed. GATE 3 is Fri Oct 2. |
| 4 | The app | Not started beyond the cover layer and the harness. Kid mode, the parent area, seek safety and the hook come next. |
| 5 | Evaluation | docs/EVAL_PLAN.md is committed. Runs Oct 5 to 16. |
| 6 | Security and engineering | gitleaks in CI with a config that was checked both ways. Make targets and release builds still to do. |
| 7 | Submission package | **Drafted early, Sep 17.** README, docs/SUBMISSION.md, docs/FRICTION_LOG.md, docs/OPEN_SOURCE_PR.md and docs/VIDEO_SCRIPT.md are written. Each one carries empty rows where a measurement has not happened, and a list of what needs Alex. |

## The withdrawn timing number

There is no screen-level cover lead time, and there will not be one until the
stick arrives. There is now a software-level figure from the virtual device,
and the submission documents say plainly which of the two they are quoting. A
rehearsal run appeared to show all twenty markers covered in time. The run never played: the player reported positions up to about a
quarter of a second and got no further, while the cover scheduler, which runs
on a wall clock by design, kept advancing its own estimate and fired every
cover on time against it. A stricter second script refused to count any of it.
Both analysis scripts now require a position report from the player before a
lead time is counted, and the run was done again on a packed clip under that
rule: 49 usable trials from 22 app launches, 48 covered in time, a median lead
of 488 ms against a 500 ms guard band, and one cover that went on 86 ms after
its marker had started. That last one is the finding that matters. The
scheduler re-checks every 50 ms and re-anchors on every position report, so a
cover that late means the JavaScript thread was unavailable for about a third
of a second, and the guard band has to be wider than the worst such pause.
Nothing yet measures that pause on real hardware.

`results/gate1_software_vvd.json` ships with the events it came from, and
`eval/verify_gate1_archive.py` rebuilds the summary from them in CI. The full
retraction of the original number is in docs/GATES.md.

`results/vvd_timeupdate_stats.json` is unaffected and is still the argument for
scheduling ahead rather than reacting.

## Phase 7, what is written and what it still needs

| File | State |
|---|---|
| README.md | Written. Thesis, architecture diagram, required-tech table with exact file and line, results tables synced from `results/`, install steps for the stick and the virtual device, limits, safety wording, licences. The demo PIN is the one gap: the parent area lands in phase 4. |
| docs/SUBMISSION.md | Every Devpost field drafted. Product feedback answers Amazon's five questions for nine tools. Fourteen feature requests with priorities, led by a system-wide Fire TV "dim flashing lights" setting. Twelve items need Alex, listed in one table at the end. |
| docs/FRICTION_LOG.md | Every entry in Amazon's six-field format, with a table at the end saying where the evidence for each one lives. It is the only friction file. |
| docs/OPEN_SOURCE_PR.md | Target picked, fix written, tests written and seen to fail without the fix. The branch is not created and nothing is pushed: it has to live in a fork under Alex's account. |
| docs/VIDEO_SCRIPT.md | Timed to 2:55, with the safety and rights checks, the shot list, and what has to exist before it can be filmed. |

## The next three gates, plus the one date that is new

1. **GATE 1, overlay timing on the stick.** Wed Sep 23, Fri Sep 25 at the
   latest. Needs the stick, a phone at 240 fps and a TV in game mode. This is
   the only thing that can produce a lead time number.
2. **GATE 2, screening day.** Fri Sep 25. The target of 15 flagged segments
   from 4 sources is already met by `results/screening.json`.
3. **GATE 3, end to end on the stick.** Fri Oct 2. Upload a title, get a
   verified map and a safe rendition, play it in kid mode.
4. **Upstream pull request open.** Mon Oct 12, so the Devpost contribution URL
   exists. The work is done; opening it needs a fork under Alex's account.

## Phase 8, the five features asked for after the recovery

Added Thu Sep 17, 2026, late. Each is complete with tests and docs or it does not
land at all. Order matters: A first, because the pattern rule changes what a map
contains and everything downstream reads maps.

| | Feature | What it means | State |
|---|---|---|---|
| **A** | Regular-pattern rule in flashmap | Ofcom and BT.1702 also flag high-contrast regular patterns, which WCAG 2.3.1 does not cover. A separate rule with its own profile flag, its own conformance clips, and precision and recall with Wilson intervals. The hide plan and verify treat a pattern segment exactly like a flash segment. | Thresholds are being quoted into docs/SPEC_SOURCES.md first. **No code until that lands**, because CLAUDE.md forbids a threshold that is not quoted from a primary source. |
| **B** | Family profiles | Up to four kids, each with a preset and room settings, one household PIN, a picker on the kid home screen, per-profile hidden-segment logs. No profile can be weaker than WCAG. | In progress |
| **C** | Audio cue before a hide | A soft chime a fixed time before the cover, on by default, off in the parent area. It must never fire without a cover following it, as a mutation-checked property. | In progress |
| **D** | Report page | `flashmap report` writes a self-contained HTML report per title: the flash timeline, hidden segments, presets, licence and hashes. Plus an upload page wired to the pipeline so a judge can drop in a clip. Deploy-ready, not deployed, until STATUS.md says the Paid plan is confirmed. Every image in the report passes flashmap. | Not started |
| **E** | Map registry | A static index of signed maps keyed by file hash, served beside the maps, with a lookup in the hook so any Vega app can fetch a map for a file it already has. A tampered index entry fails closed. | In progress |

The three loose ends that came with them are done: the cover-reason logging and
the two lead-time distributions, the verify status for a title with no flagged
segments, and the chaos re-run.
