# What the analyser measures, and what it costs

Every number on this page comes from `results/*.json` through the marker form that
`eval/readme_sync.py --check` verifies, so it cannot drift from what was measured. Nothing here
is an estimate and nothing here is a target.

Written Thu Sep 17, 2026, against `docs/EVAL_PLAN.md`, which was committed before any of it ran.
Where this lane departed from that plan, the departure is in `eval/DEVIATIONS.md` with the
reason.

## 1. The conformance suite

Generated clips, one second windows, ground truth computed from the quoted spec text by
`eval/conformance/truth.py`, which does not import flashmap and is held to that by a test. The
generator knows what it drew, so it knows the true answer; that is the whole reason these clips
are worth measuring.

**Sample.** The committed design is
<!--n results/conformance.json:published.clips_designed -->3000<!--/n--> clips.
<!--n results/conformance.json:published.clips_measured -->475<!--/n--> of them have been
measured so far and
<!--n results/conformance.json:published.clips_kept -->467<!--/n--> were kept, giving
<!--n results/conformance.json:published.windows -->1401<!--/n--> one second windows, of which
<!--n results/conformance.json:published.positive_windows -->324<!--/n--> are ground truth
positives. The run order is the whole spine first, which walks one axis at a time, then the
cross product shuffled with the committed seed, so this is a stratified sample with every sweep
complete rather than a truncated list. `make conformance-full` finishes the rest and rebuilds
every table here.

**Precision and recall per one second window**, Wilson 95%:

| | precision | recall |
|---|---|---|
| over every window | <!--n results/conformance.json:published.flashmap_precision -->0.65<!--/n--> [<!--n results/conformance.json:published.flashmap_precision_lo -->0.605<!--/n-->, <!--n results/conformance.json:published.flashmap_precision_hi -->0.693<!--/n-->] | <!--n results/conformance.json:published.flashmap_recall -->0.895<!--/n--> [<!--n results/conformance.json:published.flashmap_recall_lo -->0.857<!--/n-->, <!--n results/conformance.json:published.flashmap_recall_hi -->0.924<!--/n-->] |
| over the windows every detector saw | <!--n results/conformance.json:published.flashmap_shared_precision -->0.954<!--/n--> [<!--n results/conformance.json:published.flashmap_shared_precision_lo -->0.924<!--/n-->, <!--n results/conformance.json:published.flashmap_shared_precision_hi -->0.972<!--/n-->] | <!--n results/conformance.json:published.flashmap_shared_recall -->0.895<!--/n--> [<!--n results/conformance.json:published.flashmap_shared_recall_lo -->0.857<!--/n-->, <!--n results/conformance.json:published.flashmap_shared_recall_hi -->0.924<!--/n-->] |

The two rows differ for one reason, and it is not a defect. flashmap hides the whole failing one
second period, which starts in the calm second before the flashing. Counting every window, that
shows up as false positives in the lead-in. Counting only the windows every detector saw, which
excludes the first second of each clip because ffmpeg's filter drops it, those windows are gone.
Both numbers are here because neither one on its own is the honest one.

The split is not a matter of opinion: of
<!--n results/conformance.json:published.false_positives_total -->156<!--/n--> false positive
windows,
<!--n results/conformance.json:published.false_positives_in_the_calm_lead_in -->142<!--/n--> are the
calm second before the flashing starts and
<!--n results/conformance.json:published.false_positives_elsewhere -->14<!--/n--> are anywhere
else.

The denominators are
<!--n results/conformance.json:published.flashmap_precision_denominator -->446<!--/n--> predicted
positive windows and
<!--n results/conformance.json:published.flashmap_recall_denominator -->324<!--/n--> ground truth
positive windows.
<!--n results/conformance.json:published.excluded_clips -->8<!--/n--> clips were excluded and
counted, for the reasons listed under `exclusions` in the result file.

At clip level, which is what `flashmap check` answers, precision is
<!--n results/conformance.json:published.clip_level_precision -->0.954<!--/n--> and recall is
<!--n results/conformance.json:published.clip_level_recall -->0.895<!--/n-->.

**Where the recall goes.** Split the clips by whether any governing quantity sits within 15% of
its limit and the number stops being one number. On the
<!--n results/conformance.json:published.recall_away_from_limits_clips -->289<!--/n--> clips clear
of every limit, flashmap found every positive window: recall
<!--n results/conformance.json:published.recall_away_from_limits -->1<!--/n--> over
<!--n results/conformance.json:published.recall_away_from_limits_positive_windows -->244<!--/n-->
positive windows. On the
<!--n results/conformance.json:published.recall_near_limits_clips -->178<!--/n--> clips that sit on
a limit it is <!--n results/conformance.json:published.recall_near_limits -->0.575<!--/n--> over
<!--n results/conformance.json:published.recall_near_limits_positive_windows -->80<!--/n-->
positive windows. Every miss in this suite is a boundary case, and they miss on the permissive
side: a step drawn just over the luminance limit can decode just under it, and an area drawn
just over the field limit can measure just under it on the analyser's working grid.

**Error curves** along every axis, one at a time, are in `results/figures/`. The interesting
regions rather than the headline:

- at exactly three flashes a second the ground truth and flashmap disagree, because the spec
  does not say whether a one second period includes both its ends. Ours is half open, flashmap's
  trailing window is closed, and a closed period finds one extra flash in a clean 3 Hz square
  wave;
- the misses sit in a narrow band a few percent wide on the permissive side of each limit:
  the ones read off the raw rows are a luminance step drawn 0.9% over the limit, a field
  coverage drawn 5% over it, and a red distance drawn 5% over it, each of which came back under
  the limit after the encode and the decode.

## 2. Baselines

The same clips, the same windows, the same metrics, over the windows every detector saw:

| detector | precision | recall |
|---|---|---|
| flashmap | <!--n results/conformance.json:published.flashmap_shared_precision -->0.954<!--/n--> | <!--n results/conformance.json:published.flashmap_shared_recall -->0.895<!--/n--> |
| naive mean luminance differencing | <!--n results/conformance.json:published.naive_precision -->0.667<!--/n--> | <!--n results/conformance.json:published.naive_recall -->0.809<!--/n--> |
| ffmpeg photosensitivity filter | <!--n results/conformance.json:published.ffmpeg_precision -->0.368<!--/n--> | <!--n results/conformance.json:published.ffmpeg_recall -->0.951<!--/n--> |

Both baselines were swept on this suite and are shown at the threshold that maximises their F1
here, which is the friendliest reading of each. flashmap's thresholds come from the spec and
were not tuned on either set.

Two baselines did not run, and the reason is in `results/baselines.json` with the machine probe
that supports it: **EA IRIS**, whose pinned image has never built and whose build would have
taken over a Docker VM that another project's stack was already using, and **Apple
VideoFlashingReduction**, which needs Xcode on a machine that has Command Line Tools only. No
number from either appears anywhere.

What the baselines cannot do is measured rather than asserted, in
`results/baselines.json` under `blind_spots_measured`: the area axis, the colour pair axis and
the flash rate axis, where neither baseline has a rule at all.

## 3. Ablations

One thing off at a time, on the same clips, against the same committed ground truth. The default
arm is compared against the main run clip for clip first:
<!--n results/ablations.json:published.default_arm_mismatches -->0<!--/n--> mismatches over
<!--n results/ablations.json:published.default_arm_clips_compared -->150<!--/n--> clips, on
<!--n results/ablations.json:published.clips -->150<!--/n--> clips in total.

| arm | precision | recall | change in recall |
|---|---|---|---|
| default | <!--n results/ablations.json:published.default_precision -->0.672<!--/n--> | <!--n results/ablations.json:published.default_recall -->0.898<!--/n--> | |
| red rule off | <!--n results/ablations.json:published.red_rule_off_precision -->0.674<!--/n--> | <!--n results/ablations.json:published.red_rule_off_recall -->0.653<!--/n--> | <!--n results/ablations.json:published.red_rule_off_recall_change -->-0.245<!--/n--> |
| area rule off | <!--n results/ablations.json:published.area_rule_off_precision -->0.508<!--/n--> | <!--n results/ablations.json:published.area_rule_off_recall -->0.918<!--/n--> | <!--n results/ablations.json:published.area_rule_off_recall_change -->0.02<!--/n--> |
| darker image rule off | <!--n results/ablations.json:published.darker_image_rule_off_precision -->0.657<!--/n--> | <!--n results/ablations.json:published.darker_image_rule_off_recall -->0.898<!--/n--> | <!--n results/ablations.json:published.darker_image_rule_off_recall_change -->0<!--/n--> |
| sRGB linearisation off | <!--n results/ablations.json:published.srgb_linearization_off_precision -->0.661<!--/n--> | <!--n results/ablations.json:published.srgb_linearization_off_recall -->0.857<!--/n--> | <!--n results/ablations.json:published.srgb_linearization_off_recall_change -->-0.041<!--/n--> |

**Cover, dim against opaque.** Each flagged clip is rendered again with the cover over it in
linear light and analysed again, which is what the verify step does. Of
<!--n results/ablations.json:published.cover_red_clips -->30<!--/n--> clips with a red segment,
<!--n results/ablations.json:published.cover_red_dim_flagged -->27<!--/n--> still fail under a dim
cover and <!--n results/ablations.json:published.cover_red_opaque_flagged -->0<!--/n--> under an
opaque one. Of <!--n results/ablations.json:published.cover_non_red_clips -->30<!--/n--> clips
with only general segments,
<!--n results/ablations.json:published.cover_non_red_dim_flagged -->0<!--/n--> still fail under a
dim cover. Dimming multiplies all three channels by the same factor and leaves the chromaticity
where it was, and the red rule reads chromaticity, which is why a red segment always gets an
opaque cover.

**Guard band**, simulated over the measured flash maps through the app's own
`coverSchedule.ts`, on <!--n results/ablations.json:published.guard_clips -->144<!--/n--> clips.
There is no measured cover latency yet, because `results/gate1_timing.json` does not exist, so
the table is read as "in place before the flashing starts, if the player takes no longer than
this":

| guard band | latency 0 ms | latency 100 ms | latency 200 ms |
|---|---|---|---|
| 0 ms | <!--n results/ablations.json:published.guard_0ms_latency_0ms -->1<!--/n--> | <!--n results/ablations.json:published.guard_0ms_latency_100ms -->0.979<!--/n--> | <!--n results/ablations.json:published.guard_0ms_latency_200ms -->0.979<!--/n--> |
| 100 ms | <!--n results/ablations.json:published.guard_100ms_latency_0ms -->1<!--/n--> | <!--n results/ablations.json:published.guard_100ms_latency_100ms -->1<!--/n--> | <!--n results/ablations.json:published.guard_100ms_latency_200ms -->0.979<!--/n--> |
| 250 ms | <!--n results/ablations.json:published.guard_250ms_latency_0ms -->1<!--/n--> | <!--n results/ablations.json:published.guard_250ms_latency_100ms -->1<!--/n--> | <!--n results/ablations.json:published.guard_250ms_latency_200ms -->1<!--/n--> |
| 500 ms | <!--n results/ablations.json:published.guard_500ms_latency_0ms -->1<!--/n--> | <!--n results/ablations.json:published.guard_500ms_latency_100ms -->1<!--/n--> | <!--n results/ablations.json:published.guard_500ms_latency_200ms -->1<!--/n--> |

## 4. Real clips

Prepared, not labelled. Nobody on this lane labels a segment.

<!--n results/realclips_status.json:segments -->40<!--/n--> ten second segments were cut from
<!--n results/realclips_status.json:titles -->16<!--/n--> titles across
<!--n results/realclips_status.json:source_count -->7<!--/n--> sources, as the
union of what flashmap, ffmpeg's filter and naive differencing each flagged, plus time none of
them flagged. That is
<!--n results/realclips_status.json:windows_to_label -->400<!--/n--> one second windows to call.
Each segment has an opaque id and one plot, with no title, no source, no position in the film and
no detector output anywhere on the figure. `eval/labeling/GUIDE.md` quotes the spec conditions
and says what is not a flash.

The analysis is written and tested end to end on fabricated labels, so the only missing step is
two people filling in `eval/labeling/labels_*.csv`. IRIS is not one of the candidate lists,
because the image has never built, and the four Theora titles had no flashmap intervals when the
pool was cut, so their windows came from the two ffmpeg based lists only.

One thing to do before anybody starts labelling: flashmap's Theora decoding has since been
fixed, and `results/screening.json` still holds the run where those four titles failed. Rescreen
them, then run `make labeling-pool` again. Rebuilding the pool after labelling has begun would
throw the labels away, because a segment id is a position in a shuffled list.

## 5. How to rebuild all of it

```
make reproduce          # every table and figure, offline, from results/*.json
make conformance-full   # the rest of the 3000 clip design, then the tables again
make ablations          # the ablation arms
make eval-checks        # the tests, including the guards that keep truth independent
```

Hazard clips are generated, analysed and deleted inside one job. None of them is ever opened.
