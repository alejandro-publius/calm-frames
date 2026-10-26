# Detector review: the standards against the code

Integration note, October 15: reviewed and integrated as tests/docs only. The
22 focused boundary tests pass on the current working branch. No detector,
prepared media, maps, trust or app input changed; the installed package remains
from `21f0ea6`. See [integration.json](../../../results/detector-review/integration.json).
The delayed automatic return mentioned below is supported by PlayerScreen's
source; the current native driver uses Back before that delay and does not
independently validate it. The source-fetch and wider test claims below are
Claude's dated evidence, not a new retrieval or rerun by the integrator.

Written Oct 15, 2026 on branch `claude/detector-review-2026-10-15`. A code and
specification review, not independent clinical validation: reading the
standards and running our tests does not certify the product, and nothing here
calls any output seizure-safe. A measured threshold exceedance is a measured
threshold exceedance; whether it would trigger anyone is a clinical question
this review does not answer.

Sources read on 2026-10-15T21:36:40Z: the WCAG 2.2 Recommendation
(<https://www.w3.org/TR/WCAG22/>, the glossary entries "general flash and red
flash thresholds" and "relative luminance", and SC 2.3.1) and Understanding SC
2.3.1 (<https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html>).
The broadcast side is quoted from ITU-R BT.1702-3 as transcribed in
`flashmap/docs/SPEC_SOURCES.md` sections 5 and 8; that recommendation was not
re-fetched for this review. Repository references are to
`flashmap/src/flashmap/` at the commit this file is in.

## 1. The two profiles are not interchangeable

| | `WCAG` (`profiles.py`) | `BROADCAST_SDR` (`profiles.py`) |
|---|---|---|
| Luminance measure | WCAG relative luminance of each pixel, 0 to 1, from sRGB (`color.relative_luminance` after `color.srgb_to_linear`) | screen luminance in cd/m2 from the luma signal level through BT.1886 with gamma 2.4 and an assumed peak white, 200 cd/m2 by default (`color.bt1886_nits`, `--peak-nits`) |
| General flash transition | a change of 0.10 or more where the darker image is below 0.80 | a change of 20 cd/m2 or more where the darker image is below 160 cd/m2 |
| Red flash | R/(R+G+B) at or above 0.8 with more than 0.2 in CIE 1976 UCS (WCAG 2.2 Note 3) | the same working definition, reused because BT.1702-3 gives none (`RedRule.source`) |
| Count rule | more than three general flashes, or more than three red flashes, in any one-second period | the same count, the same window |
| Area rule | more than 25% of any 10 degree field, a sliding 341/1024 by 256/768 window on the picture | more than 25% of the displayed picture, one whole-picture window (`area_window_mode = "whole-picture"`) |
| Regular patterns | none; WCAG 2.2 has no pattern rule | Guideline 2 from the informative Attachment 1, reported separately and never as a WCAG finding |
| HDR | refused (`decode.decide_color` raises on PQ and HLG) | refused; the HDR branch (Michelson 1/17 above 160 cd/m2) is not implemented |

A disagreement between the two profiles on the same clip is therefore the
expected result of two different rules, not a defect. On the Acadia clip the
WCAG profile found one span with no room and the broadcast profile found none:
the broadcast rule measures a 20 cd/m2 step on an assumed 200 cd/m2 display
and a whole-picture area, and whitewater over a quarter of a 10 degree window
is not whitewater over a quarter of the screen.

## 2. The WCAG profile, definition by definition

Quoted text is from the W3C pages above, fetched today.

| Definition (WCAG 2.2) | What the code does | Status |
|---|---|---|
| **relative luminance**: "L = 0.2126 * R + 0.7152 * G + 0.0722 * B" with the sRGB linearisation "if RsRGB <= 0.04045 then R = RsRGB/12.92 else R = ((RsRGB+0.055)/1.055) ^ 2.4" | `color.srgb_to_linear` uses 0.04045, 12.92, 0.055, 1.055, 2.4; `color.relative_luminance` uses the three weights (`test_color.py` pins each coefficient) | Implemented as written. Note 2's 2021 change from 0.03928 to 0.04045 is in. |
| **general flash**: "a pair of opposing changes in relative luminance of 10% or more of the maximum relative luminance (1.0) where the relative luminance of the darker image is below 0.80; and where 'a pair of opposing changes' is an increase followed by a decrease, or a decrease followed by an increase" | `flash.GeneralFlashTracker(min_delta=0.10, dark_image_below=0.80)`: per pixel, a transition is confirmed when the swing from the last confirmed extreme reaches 0.10 and the darker of the two values is below 0.80; a flash is a confirmed transition whose sign opposes the pending one; pairs do not overlap | Implemented, with two readings the text leaves open: transitions are declared on the first frame that reaches the threshold (SPEC_SOURCES decision 2) and paired without overlap (decision 1). **Per pixel, not per image**: the text speaks of "the darker image"; flashmap evaluates each pixel's own trace and then asks how much area flashes together, which is the reading that lets the area rule apply at all. |
| **Note 2**: "A transition is the change in relative luminance ... between adjacent peaks and valleys ... A flash consists of two opposing transitions" | the tracker's anchor and extreme implement peaks and valleys causally; `test_flash_tracker.py` covers a square wave, a single pulse, a staircase and the turn-around case | Implemented with a causal approximation when a peak is recognised. This review does not establish that the resulting timing difference can only lengthen a reported span; exact marginal timing needs separate validation. |
| **red flash** and **Note 3**: "one transition is either to or from a state with a value R/(R + G + B) that is greater than or equal to 0.8, and the difference between states is more than 0.2 (unitless) in the CIE 1976 UCS chromaticity diagram" | `flash.RedFlashTracker(saturated_ratio=0.8, min_distance=0.2)` on `color.red_ratio` (linear light) and `color.ucs_1976` of `color.linear_rgb_to_xyz` (the Understanding document's u', v' formulas and sRGB to XYZ matrix; `test_flash_tracker.py` pins every matrix coefficient and both boundaries) | Implemented. **Opposing** for colour is a reading (decision 4): one entry into the saturated state paired with one exit, each moving more than 0.2. The ratio is computed on linear light; the text does not say which encoding, and Note 3 cites ISO 9241-391, which this review did not read. |
| **count**: "no more than three general flashes and / or no more than three red flashes within any one-second period" | `analyze.StreamingAnalyzer._record`: two tallies, `general` and `red`, each a trailing window [t − 1000 ms, t] closed at both ends, evaluated at every frame; more than 3 fails (`counts > 3`) | Implemented; the window placement is decision 3 and the boundary tests pin the closed window and the separate tallies. "and / or" is read as two independent tallies: four red and zero general fails, two and two passes. |
| **area**: "the combined area of flashes occurring concurrently occupies no more than ... 25% of any 10 degree visual field on the screen" with **Note 1**'s "341 x 256 pixel rectangle ... at 1024 x 768" | `area.wcag_reference_window`: a window of 341/1024 of the picture width by 256/768 of its height on the working frame (64 by 36 on 192 by 108); `area.max_coverage` slides it to every position and takes the busiest; "concurrently" is read as the pixels whose own tallies exceed three in the same trailing window; fails when the fraction is more than 0.25 (`value > 0.25`) | **Approximate**: the window is a fraction of the picture, which follows the Understanding document's argument that the fraction holds on any screen, and it is measured on a 192 pixel wide working frame (decision 7), so one working pixel is about seven source pixels on 1280 wide video and single source pixel exactness is not available; the boundary tests prove exactness at the working-frame layer (576 of 2304 passes, 577 fails). "Typical viewing distance" is not modelled by the WCAG window; the optional room window (decision 8) only adds. The .006 steradian figure is not used. |
| **Exception**: "a fine, balanced, pattern such as white noise or an alternating checkerboard pattern with 'squares' smaller than 0.1 degree" | not implemented; such content is reported as failing (`profile.exceptions_not_implemented` in every map) | Unsupported, in the strict direction. |
| **Understanding**: "Content should be analyzed at the largest scale at which a user may view the content ... the video should be analyzed for risks at full screen" | area is a fraction of the picture after letterbox and pillarbox bars are removed (decision 5), which is the full-screen reading | Implemented by construction; the app shows the picture full screen. |
| **Understanding**: "Where video content is provided in color spaces other than sRGB, the version provided with the highest dynamic range should be tested. In such cases the industry standard definition of a general flash is a change in luminance of 20 cd/m2 or more where the darker image is below 160 cd/m2 (ITU-R BT.1702)" | the WCAG profile decodes BT.601 and BT.709 tagged or inferred video to sRGB-style values and applies the relative-luminance rule; the 20 cd/m2 rule is the broadcast profile; PQ and HLG are refused | **Partial**: SDR video is treated as sRGB-like for the WCAG profile (the matrix and range are taken from the stream tags, `decode.decide_color`); the "highest dynamic range version" guidance cannot be followed because HDR is refused rather than measured. |
| **Understanding**: "For short clips that might be looped (such as GIF animations), the content should be analyzed while looping" | one pass from the first frame to the last; nothing crosses the seam (`test_a_single_pass_does_not_count_flashes_across_a_loop_seam` pins that) | **Unsupported.** The app does not loop a title on its own (playback ends and returns to the launching screen), so the exposure is a replay started by hand, seconds later; a product that loops would need the seam analysed. |
| **Note 4**: "no tool is necessary to evaluate for this condition if flashing is less than or equal to 3 flashes in any one second" | not applicable to a measuring tool | n/a |

## 3. The broadcast profile, rule by rule (BT.1702-3 as transcribed in SPEC_SOURCES.md)

| Rule | What the code does | Status |
|---|---|---|
| Guideline 1, SDR: a flash is a change of 20 cd/m2 or more where the darker image is below 160 cd/m2 | `GeneralRule(metric="bt1886-nits", min_delta=20.0, dark_image_below=160.0)`; luminance from the luma level through `color.bt1886_nits` with gamma 2.4 and `peak_nits` 200 (Note 3's assumed peak white); `test_bt1702_table.py` reproduces all 45 SDR rows of the recommendation's Table 1 within 0.005 cd/m2 | Implemented for SDR. **Assumed display**: 200 cd/m2 peak white is the recommendation's measurement assumption, not a measurement of any television; `--peak-nits` changes it. |
| HDR branch: Michelson contrast 1/17 where the darker image is at or above 160 cd/m2 | not implemented; HDR inputs are refused | Unsupported, by refusal rather than by a wrong measurement. |
| "a transition to or from a saturated red is also potentially harmful" | the WCAG Note 3 working definition is reused, since the recommendation gives no numbers | Approximate by necessity; stated in `RedRule.source`. |
| Area: "more than 25% of the displayed screen area" | one window the size of the whole picture (`bt1702-screen`), bars removed first | Implemented. Note 4's overscan allowance (1% to 3.5%) is not applied, which can only make the measure stricter. |
| Count: "more than three flashes within any one-second period"; the 360 ms / 334 ms leading-edge allowance | the same trailing-window tally as WCAG; the allowance is not implemented | Implemented; the allowance is unsupported, and leaving it out can only add findings. |
| Guideline 2, regular patterns (informative Attachment 1) | `pattern.py`, broadcast profile only; thresholds 5 pairs, 40% stationary, 25% changing; the contrast condition reuses Guideline 1's flash difference; everything else is detector tuning recorded in the map | Implemented from an informative source, labelled as such in every map, never a WCAG finding. |
| Persistence time, stripe width, spatial frequency band for Guideline 2 | none, because the recommendation gives none | Unsupported; recorded in `rules_not_implemented`. |

## 4. Timing, shared by both profiles

| Behaviour | Code | Evidence |
|---|---|---|
| Timestamps come from the container's presentation times, never from a nominal frame rate | `decode.iter_frames` (pts, falling back to dts); `sidecar` records `timestamp_source` | `test_vfr.py`; the 48000/1001 cadence tests |
| The one-second period is a trailing window [t − 1000, t] closed at both ends, evaluated at every frame | `_record`: events older than `pts − 1000` are dropped with `<` | SPEC_SOURCES decision 3; `test_four_flashes_whose_first_and_last_are_exactly_one_second_apart_fail` and its one-millisecond-wider twin |
| A repeated timestamp is dropped; a backwards one is dropped | `StreamingAnalyzer.push` skips `pts <= last` | the two timestamp tests |
| The hidden interval starts one second before the fourth flash, is clamped at the file's start, and lasts until the fourth flash ages out of the window | `_record` sets `start = max(0, pts − 1000)` and extends `end` while the window still fails; `_close_if_stale` closes it | the three hidden-interval tests |
| Chunked analysis equals whole-file analysis | `_chunked` with overlap | `test_chunking.py` (property based) |
| Looping | not analysed | section 2, last row |

## 5. Negative controls for this review

Seven breaks in all: the four from the video reset (window count, area
comparison, window edge, repeated timestamps) and three new ones aimed at the
new tests: the hidden interval no longer extending while the window still
fails, red flashes tallied with the general ones, and the area window one pixel
narrower than the profile says. Each was applied alone, run, and restored;
`results/detector-review/negative-controls.json` lists the tests that went red.

## 6. Material limitations

1. **Per-pixel flashes and a sliding window are a reading of the text, not the
   text.** WCAG speaks of "the darker image" and "the combined area of flashes
   occurring concurrently"; flashmap tracks each pixel's own transitions and
   slides one 10 degree window to the busiest place. A different reading (a
   region's mean luminance, or a fixed grid of fields) would move findings at
   the margin. Source: WCAG 2.2 glossary, "general flash and red flash
   thresholds"; `flash.py`, `area.py`.
2. **The working frame is 192 pixels wide.** Area fractions are ratios and
   survive scaling, but a flash confined to a few source pixels is averaged
   into its neighbours before it is measured, and single source pixel
   exactness does not exist. Source: SPEC_SOURCES decision 7; `decode.probe`
   and `_analysis_size`; the 576 and 577 tests, which hold at the working layer.
3. **Looped playback is not analysed.** The Understanding document asks for
   loopable clips to be analysed while looping; flashmap reads one pass, and
   the loop-seam test pins exactly that. Source: Understanding SC 2.3.1,
   "For short clips that might be looped"; `StreamingAnalyzer.push`.
4. **The broadcast profile assumes a display.** 200 cd/m2 peak white and the
   BT.1886 curve are the recommendation's measurement assumptions; a brighter
   television shows larger steps than the profile measured. The WCAG profile
   assumes sRGB-like decoding of BT.709 and BT.601 video and refuses HDR
   outright, so the "highest dynamic range version" guidance cannot be
   followed. Source: BT.1702-3 Annex 1 Note 3 (as transcribed); Understanding
   SC 2.3.1; `profiles.py`, `color.bt1886_nits`, `decode.decide_color`.
5. **The exceptions and allowances that would excuse content are not
   implemented**: WCAG's fine balanced pattern exception, BT.1702-3's leading
   edge allowance and overscan allowance. Every one of these can only add
   findings, never hide one, which is the direction a safety layer should err
   in, but it means a measured exceedance is not always a standards failure.
   Source: WCAG 2.2 glossary exception; SPEC_SOURCES section 5; `profiles.py`
   `rules_not_implemented` and `exceptions_not_implemented`.
