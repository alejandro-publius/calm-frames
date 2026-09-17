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
| 1 | Vega day-one probes | Done on the virtual device. The app plays a Blender title, the cover harness runs, and the GATE 1 analysis is rehearsed. The parts that need a screen wait for the stick. |
| 2 | flashmap v1 and screening day | flashmap v1 is built and tested. Screening media is downloaded with licences recorded. GATE 2 is Fri Sep 25. |
| 3 | Pipeline and Plan B | Local pipeline, verify step and CDK skeleton are in. Nothing is deployed. GATE 3 is Fri Oct 2. |
| 4 | The app | Not started beyond the cover layer and the harness. Kid mode, the parent area, seek safety and the hook come next. |
| 5 | Evaluation | docs/EVAL_PLAN.md is committed. Runs Oct 5 to 16. |
| 6 | Security and engineering | gitleaks in CI with a config that was checked both ways. Make targets and release builds still to do. |
| 7 | Submission package | Not started. Oct 14 to 22. |

## What the kits were meant to bring, and what replaced it

The head-start kits (`day-one-head-start.zip`) never arrived. Rather than
wait, each piece was built here:

| Missing | Replaced by |
|---|---|
| flashmap | `flashmap/`, written from scratch, with every threshold quoted in docs/SPEC_SOURCES.md |
| calm-timing | `eval/marker_clip.py` for the marker clip and schedule, `eval/vvd_timing_run.py` for a run, `eval/gate1_rehearsal.py` for the analysis |
| evkit.readme_sync | `eval/readme_sync.py`, checked both ways |
| evkit.friction | `docs/friction_pending.md`, which moves into the kit's format if it ever turns up |
| calm-vega-notes | Measured directly: the device facts in docs/GATES.md and CLAUDE.md came from running the thing |
| rubric-amazon.md | The rules were read from Devpost and recorded in docs/STATUS.md |
| outreach-kit.md | `docs/outreach/`, written from the build prompt's constraints |

If the kits turn up, treat them as a second opinion rather than a drop-in
replacement, and re-record any number that came from our version.

## The next three gates

1. **GATE 1, overlay timing on the stick.** Wed Sep 23, Fri Sep 25 at the
   latest. Needs the stick, a phone at 240 fps and a TV in game mode. The
   harness and the analysis are ready and rehearsed.
2. **GATE 2, screening day.** Fri Sep 25. Needs at least 15 real flagged
   segments from at least 4 sources.
3. **GATE 3, end to end on the stick.** Fri Oct 2. Upload a title, get a
   verified map and a safe rendition, play it in kid mode.
