# Verify pass 2: pattern segments through the hide plan and verify

Date: 2026-09-17, late. Every run below was made with the tree at `a253210` (one commit after
`98b181b`, the pattern rule; the runner printed `repo HEAD a253210`), with other lanes'
uncommitted files left alone. Python 3.12.13 from `.venv`, ffmpeg 8.1.2. While this was being
written HEAD moved on to `71c31b5` and another lane began editing
`flashmap/src/flashmap/pattern.py` (file changed 23:46:18, after the last run here finished at
23:45). That live diff widens `_span_mask` by half a bar at each end and reworks the diagonal
scan, so the area fractions quoted below (0.922, 0.531) will move under it; it does not touch
`picture.py`, `analyze.py`, `pipeline/flashmap_adapter.py`, `pipeline/hideplan.py` or
`pipeline/verify.py`, which is where everything else on this page lives.

Claim under test: "The hide plan and verify step treat pattern segments exactly like flash
segments." Everything below was run, not read. Every clip was made with
`flashmap/tests/clipgen.py` (`grating`, `solid`, `write_clip`), analysed and deleted in the
same job by a `finally` block; each runner ended with `media files left ... after cleanup: []`.
Nothing was opened in a player. Nothing was committed.

Verdict in one line: the claim holds. A pattern segment gets the same cover interval as a flash
segment, is never dimmed, and the real `pipeline.ingest` plus `pipeline.verify` pass a pattern
title with "cover proven drawn". Two things need saying, and one of them is a miss in the
analyzer that sits outside the six items but was found by them, so it comes first.

## FAILS (extra finding, not one of the six): a black edge bar is cropped as a pillarbox and a six pair pattern passes

- Command: `clipgen.grating(384, 216, 6, (0,0,0), (255,255,255))` x 40 frames at 20 fps, then
  `python -m flashmap analyze HAZARD_pattern6_fullswing.mkv --profile broadcast --out fullswing.broadcast.json --quiet`
- Output: `exit 0`, `summary: {"pass": true, "flash_pass": true, "pattern_pass": true,
  "pattern_segment_count": 0, "pattern_rule_applied": true}`. Picture block of that map:
  `"pillarbox": true, "left": 0, "width": 175` of 192 analysis pixels (350 of 384 coded).
- Why: the outermost bar of a six pair grating is always dark on one side, and at code 0 it sits
  under `LetterboxSettings.max_bar_luminance = 0.02` on every sampled frame, so the picture
  detector took it for a pillarbox bar and cropped it. Eleven bars were left. Eleven bars is
  five pairs, and five pairs is not "more than five". Same clip with the black bar on the other
  edge (`invert=True`): `"left": 17, "width": 175`, same pass. Seven pairs with a black edge
  bar: flagged (`exit 1`), but the segment says `stripe_pairs: 6`, because thirteen bars
  remained after the crop.
- What it means: the most severe pattern this generator can make (black to peak white, six
  pairs, the whole frame, a 200 cd/m2 bar difference) is passed by the broadcast profile, and
  any pattern at the count boundary loses a pair whenever its edge bar is near black. The
  hide plan and verify never see a segment, so they are not at fault; the segment is never
  produced. The grey clips in the six items (codes 96 and 160) are not affected, which is why
  they all tripped the rule.

## The six items

1. **HOLDS.** Clip: `clipgen.grating(384, 216, 6, (96,96,96), (160,160,160))` x 40 at 20 fps,
   vertical, stationary, `area=1.0`. Bars through the profile's own curve (`bt1886_nits`, peak
   200): `DARK 19.18 cd/m2, BRIGHT 65.35 cd/m2, difference 46.17` against the quoted Guideline 1
   difference of 20 cd/m2 with the darker bar under 160 (`BROADCAST_SDR.general.min_delta=20.0,
   dark_image_below=160.0`). Six pairs is twelve bars, the first count that can fail
   (`more_than_pairs=5`). Deleted in the same job:
   `deleting scratch/verify2/clips: ['HAZARD_pattern6_stationary_full.mkv', ...]`,
   `media files left under scratch/verify2 after cleanup: []`.

2. **HOLDS, one cosmetic caveat.** Command:
   `python -m flashmap analyze HAZARD_pattern6_stationary_full.mkv --profile broadcast --out pattern6.broadcast.json`.
   Output: `exit 1`; stderr `no segment broke the thresholds` then `1 regular pattern
   segment(s), from ITU-R BT.1702-3 Attachment 1 to Annex 1, which is informative and is not a
   WCAG rule.` and `0 to 1950 ms  pattern  6 light and dark pairs  area 0.922 over 0.25  motion
   mixed`. Map segment: `{"start_ms": 0, "end_ms": 1950, "reason": "pattern", "stripe_pairs":
   6, "area_fraction": 0.921875, "area_limit": 0.25, "motion": "mixed", "is_a_wcag_finding":
   false, "source": "ITU-R BT.1702-3 Attachment 1 to Annex 1 (informative), ..."}` with none of
   the flash fields. Summary: `{"pass": false, "flash_pass": true, "pattern_pass": false,
   "segment_count": 1, "general_segment_count": 0, "red_segment_count": 0,
   "pattern_segment_count": 1, "pattern_exemption_count": 0, "pattern_rule_applied": true,
   "hidden_ms": 1950}`. The verdicts are separate. Caveat: a plainly stationary pattern is
   reported as `motion: "mixed"` with `area_limit: 0.25`, because the first frames are
   `uncertain` until the motion history fills and the span reports the strictest limit it ever
   had; a reviewer will never see `stationary` on a segment that starts with the pattern.

3. **HOLDS.** Command:
   `python -m flashmap analyze HAZARD_pattern6_stationary_full.mkv --profile wcag --out pattern6.wcag.json`.
   Output: `exit 0`; `no segment broke the thresholds`; `segments: []`, `pattern_exemptions:
   []`; `profile.pattern_rule: null`; `summary: {"pass": true, "flash_pass": true,
   "pattern_pass": true, "pattern_segment_count": 0, "pattern_rule_applied": false}`;
   `rules_not_implemented` ends with `'any regular pattern rule, because WCAG 2.2 has none. See
   the broadcast profile'`. The pipeline's third preset too:
   `FlashmapAdapter().analyze(clip, profile="extra-cautious")` (wcag rules in a 75 in / 5 ft
   room window) gave `profile='wcag' preset='extra-cautious' is_clean=True segments=[]`. No
   pattern finding was ever reported under WCAG. Small note: the wcag map still carries
   `"pattern_pass": true`, which is only readable beside `"pattern_rule_applied": false`.

4. **HOLDS WITH A CAVEAT: the cover is identical, the reason is flattened, and to "red", not
   "general".** Command: `pipeline.flashmap_adapter.load_map(pattern6.broadcast.json)` then
   `pipeline.hideplan.build_hide_plan(doc, duration_ms=2000, preset="broadcast")`. Output:
   `interval 0.0..2000.0 ms reason='red' mode='opaque' sources=[(0.0, 1950.0, 'red')]`. The
   same segment times fed in as a general flash give `[(0.0, 2000.0)]` and as a red flash
   `[(0.0, 2000.0)]`: the 500 ms guard band on both sides, clipped to 0 and the duration,
   `min_cover_ms` 400 never needed. Through the real pipeline (item 5's run) the stored plan
   for map segment `(1950, 3950, 'pattern')` was `intervals=[(1450.0, 4450.0, 'red')]
   sources=[(1950.0, 3950.0, 'red')]`, and `plan_matches_map:broadcast` passed `stored=1
   expected=1`. The flattening happens in `pipeline/flashmap_adapter.py::normalise_reason`,
   which knows the general words and the red words and sends everything else to red:
   `normalise_reason('pattern') -> 'red'`. The word "pattern" does not survive into the plan
   at all, not even in `sources`. Consequences: a pattern interval is always opaque (stricter
   than a general flash), a pattern touching a general flash merges into one red interval
   (`[(0.0, 3050.0, 'red')]`), and `HidePlan.has_red` is true for a pattern only title. The
   app reads the signed map the same way (`app/src/calmframes/flashMap.ts`: anything that is
   not the word "general" is red), so what verify models is what the device draws. Nothing
   names "pattern" in a test: `pipeline/tests/test_flashmap_adapter.py` pins only that
   `"something new"` reads as red.

5. **HOLDS WITH A CAVEAT: a pattern interval cannot be dimmed today, and that rests on the
   unknown reason default rather than on a rule about patterns.** Output from the plan above
   with the default household (`allow_dim=True`): `modes=['opaque'] dim_intervals=0`. From the
   real verify run: `red_always_opaque:broadcast PASS red_dimmed=[]` and
   `cover_model_clean:broadcast PASS violations=0 dim_intervals=0`.
   The arithmetic, from the quoted thresholds (SPEC_SOURCES sections 5 and 8: a difference of
   20 cd/m2 or more with the darker bar under 160 cd/m2) and the dim ceiling
   (`DIM_MAX_LUMINANCE = 0.10` of the light, modelled in linear light by
   `pipeline/render.py`, code scale `0.1 ** (1/2.4) = 0.3831`; BT.1886 nits are linear light, so
   every bar and every difference scales by 0.10):
   `this clip 19.18/65.35, diff 46.17 -> dimmed 1.92/6.53, diff 4.62: under the line`;
   `just over the line, codes 96/130: 19.18/39.70, diff 20.52 -> dimmed 1.92/3.97, diff 2.05:
   under the line`; `full swing, codes 0/255: 0.00/200.00, diff 200.00 -> dimmed 0.00/20.00,
   diff 20.00: still a pattern`. So the allowed dim brings a just over threshold pattern to a
   tenth of the line, and only a black to peak white pattern lands on it.
   Does verify model that? By re-measurement, not by arithmetic: `cover_model_clean` renders
   the plan over the original and runs the broadcast profile, pattern rule included, on the
   result. Run as verify runs it, with the real plan: `render notes {'dim_spans': 0,
   'opaque_spans': 1}` then `adapter.analyze(model, profile='broadcast', picture_from=map)`
   gave `is_clean=True violations=0`. Counterfactual, the same interval forced to `general` as
   if "pattern" were ever added to the general words: `modes=['dim']`, `render notes
   {'dim_spans': 1, 'dim_alpha_linear': 0.1, 'gamma': 2.4, 'dim_code_scale': 0.3831}`, and the
   dimmed picture re-measured `is_clean=True`, `pattern_segment_count: 0`: the 46 cd/m2 pattern
   came out at about 4.6 cd/m2, under the quoted line, and verify would accept the dim, which
   the quoted text agrees with. The one case the arithmetic says survives a dim, black to peak
   white, could not be exercised because of the crop finding at the top. Caveat: the opacity of
   every pattern cover rests on two readers' "anything unknown is red" default (the adapter and
   `flashMap.ts`), not on a decision that names patterns, and no test would go red if
   "pattern" were added to `_GENERAL_WORDS`.

6. **HOLDS.** Five ambiguous clips and two controls, all `clipgen.grating(384, 216, 6, DARK,
   BRIGHT, ...)` at 20 fps for 2000 ms, analysed with
   `python -m flashmap analyze CLIP --profile broadcast --out MAP --quiet`:
   - stutter, moves 2 px for 4 frames then stops for 4 (`area=0.55, shift=travelled`):
     `pattern segments 1 hiding 1950 ms of 2000; motion ['uncertain'] area_limit [0.25];
     exemptions 0`
   - varying speed, 1 px then 5 px alternately: `hiding 1950 ms; ['uncertain'] [0.25];
     exemptions 0`
   - oscillating, 2 px one way for 6 frames then back: `hiding 1950 ms; ['mixed'] [0.25];
     exemptions 0`
   - full screen grating rolled exactly half a period per frame (`np.roll` of the helper's
     frame, 32 px, light and dark swap every frame): `hiding 1950 ms; ['mixed'] [0.25];
     exemptions 0`
   - rolled 28 px per frame, just under half a period, direction not obvious to a viewer:
     `hiding 1950 ms; ['mixed'] [0.25]; exemptions 0`
   - control, block sliding 2 px per frame: `hiding 250 ms; exemptions 1 covering 1650 ms`,
     `exemption logged: 300..1950 ms motion='smooth-flow' confidence=1.0 pairs=6 area=0.53125
     limit=0.25`, text `ITU-R BT.1702-3 Attachment 1 to Annex 1: a pattern that obviously
     flows smoothly ...`, `summary pattern_exemption_count=1`
   - control, full screen grating rolled a quarter period per frame: `hiding 250 ms;
     exemptions 1 covering 1650 ms`, logged the same way.
   Every ambiguous clip stayed hidden at the 25% limit with no exemption, and every exemption
   that was applied is in `pattern_exemptions` with its span, area, pair count and the quoted
   sentence. The first frames of a true flow are hidden until the history fills, which is the
   fail safe direction. A note on method: a first "wagon wheel" attempt used the helper's
   `shift` on a 55% block, which just slides the block off the screen and tests nothing; the
   rolled full screen frames replaced it.

## The whole pipeline, once, on a pattern title

Clip: 2 s of `clipgen.solid(384, 216, DARK)`, 2 s of the six pair pattern, 2 s calm, 120
frames at 20 fps, with a throwaway keypair from `python -m flashmap keygen`. (A first attempt
with the 2 s all pattern clip was refused by ingest: `no calm or covered moment near 0 ms, so
no frame may be taken there`. A 2 s clip flashing end to end would be refused the same way; it
is the clip's size, not the pattern.)

- `python -m pipeline.ingest --workdir WORK --key throwaway.pem --pub throwaway.pub.pem --json HAZARD_pattern6_for_ingest.mkv`:
  `exit 0`, `publishable, 25 step(s) run, 0 skipped`, including `analyze:*`, `plan:*`,
  `rendition:*`, `cover_model:*` for all three presets and `verify`.
- Stored: `[broadcast] map: signed=True segments=[(1950, 3950, 'pattern')] flash_pass=True
  pattern_pass=False`; `[broadcast] stored plan: allow_dim=True guard=500.0
  intervals=[(1450.0, 4450.0, 'red')]`; `[wcag]` and `[extra-cautious]`: `segments=[]`,
  `intervals=[]`.
- `python -m pipeline.verify --workdir WORK --sha 7a8fdf11d138... --pub throwaway.pub.pem --json`:
  `exit 0`, `VERIFY PASSED for 7a8fdf11d138 (42 checks, cover proven drawn)`. Broadcast:
  `plan_matches_map stored=1 expected=1`, `red_always_opaque red_dimmed=[]`,
  `safe_rendition_clean violations=0`, `rendition_matches_source start_offset_ms=0.0`,
  `cover_actually_drawn worst_db=48.13 (need 30.0) at 2.95 s`, `cover_proof proof_ran=True
  proof_passed=True`, `cover_model_clean violations=0 dim_intervals=0`, `bif_calm 0 of 1`,
  `posters_calm 0 of 3`. Catalog entry: `status='verified' verified=True
  notes.verify_outcome='cover proven drawn'`.
- Cleanup: `deleting scratch/verify2/work (82 entries)`, the clip and both keys; `media,
  trickplay, poster or key files left ... after cleanup: []`.
