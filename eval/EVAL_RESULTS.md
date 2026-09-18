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

Two baselines did not run **on this suite**, and the reason is in `results/baselines.json` with
the machine probe that supports it: **EA IRIS**, which is built and has run over the real clip
pool but is not in this loop, because a conformance clip is generated, analysed and deleted
inside one job and handing it to a second process means keeping three thousand flashing clips
alive for it; and **Apple VideoFlashingReduction**, which needs Xcode on a machine that has
Command Line Tools only. No number from either appears in this table. IRIS's numbers on the real
clip pool are in `results/baselines/iris/` and `results/pool_recall.json`.

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

<!--n results/realclips_status.json:segments -->34<!--/n--> ten second segments were cut from
<!--n results/realclips_status.json:titles -->9<!--/n--> titles across
<!--n results/realclips_status.json:source_count -->5<!--/n--> sources, as the
union of what flashmap, ffmpeg's filter, naive differencing and EA IRIS each flagged, plus time
none of them flagged. That is
<!--n results/realclips_status.json:windows_to_label -->340<!--/n--> one second windows to call.
Each segment has an opaque id and one plot, with no title, no source, no position in the film and
no detector output anywhere on the figure. `eval/labeling/GUIDE.md` quotes the spec conditions
and says what is not a flash.

The analysis is written and tested end to end on fabricated labels, so the only missing step is
two people filling in `eval/labeling/labels_*.csv`. `eval/labeling/GUIDE.md` says who takes
which sheet, how much of it, and what to run afterwards.

IRIS is a candidate list now. It was built on Sep 18, natively rather than in the shared Docker
VM, and it has run over every clip it can decode, so the recall estimate is no longer optimistic
by an unknown amount. The amount turned out to be
<!--n results/pool_recall.json:published.iris_only_windows -->0<!--/n-->: not one window in the
union came from IRIS alone, so flashmap's coverage of the union is
<!--n results/pool_recall.json:published.flashmap_pool_recall -->0.626263<!--/n--> with IRIS in it and
<!--n results/pool_recall.json:published.flashmap_pool_recall_before_iris -->0.626263<!--/n--> without.
IRIS flagged <!--n results/pool_recall.json:published.iris_flagged_segments -->6<!--/n--> segments
across the whole pool, against flashmap's
<!--n results/screening.json:totals.flagged_segments -->456<!--/n-->, and raised
<!--n results/pool_recall.json:published.iris_warning_segments -->32<!--/n--> pass-with-warning
stretches it does not treat as flags. It is a much stricter reading of the same rules, which is
worth knowing and is not a verdict on either tool.

`results/pool_recall.json` reports every detector against the four list union and against the
three list union that stood before, side by side, in two scopes: every window of every title in
scope, and the windows of the blinded segments. It also says plainly what the measurement is
not. A window is positive there because a detector proposed it, not because a person called it,
so it is an upper bound, it is not ground truth, and it is not comparable with the conformance
recall in section 2. The union is also dominated by ffmpeg's filter, which is the only proposer
of more than a third of it, so flashmap's share is as much a statement about that filter's
breadth as about flashmap. The four
Theora titles were screened again before this pool was cut: the decoder was
fixed, the four were re-run on Sep 17, and `results/screening.json` records that under
`rescreens`. Three of them are ISS night time-lapses that flash at nothing, and the fourth is a
fireworks display with five flagged segments.

A title joins the pool only when every candidate list has analysed it. Sixteen clips downloaded
later in the day have no candidate list from either ffmpeg based baseline, so their time is not
unflagged in the sense this pool means and they are skipped, with the reason recorded per title
in `pool_key.json`. IRIS has run over those sixteen, so the two ffmpeg based lists are the only
thing still holding them out; `make ffmpeg-ps-pool` and `make naive-luma-pool` would close it.
A title IRIS could not decode is kept out by the same rule, and `results/baselines/iris_failures.json`
names each one.

Do not rebuild the pool once labelling has begun: a segment id is a position in a shuffled list,
so the answers would end up describing different segments. `make_pool` refuses while any sheet
has an answer in it, and the plot run deletes a figure before re-rendering it, so no figure from
an earlier pool can survive under a new id.

### Positives per source, and the gap that has to be filmed

`results/screening.json` carries the per source table: titles, titles that flashed, segments,
and the split by which rule fired. Every flagged segment in the pool fired the **general** flash
rule. **Not one fired the red flash rule**, so the pool holds no saturated red strobe and no
sustained regular strobe, and no free footage was found that covers either.

The clips that have to be filmed are listed in the same file under `self_filmed_needed`: what
each has to show, how long to roll, and how fast it has to flash, written as a multiple of the
analyser's own per second flash limit rather than as a number of its own. Two of the five are
negative controls, because a red flag that only says "the picture was red" measures nothing.

## 5. How to rebuild all of it

```
make reproduce          # every table and figure, offline, from results/*.json
make conformance-full   # the rest of the 3000 clip design, then the tables again
make ablations          # the ablation arms
make eval-checks        # the tests, including the guards that keep truth independent
```

Hazard clips are generated, analysed and deleted inside one job. None of them is ever opened.
