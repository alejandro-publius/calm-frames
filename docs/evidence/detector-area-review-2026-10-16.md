# Concurrent flashing area review, October 16, 2026

Conclusion: a reproducible standards-mapping discrepancy, with an overinclusive
result on the fixtures below. The detector combines pixels from separate bursts
inside a one-second history, then reports that combined area as a threshold
failure. Those bursts do not overlap. This is not a room-conversion error or a
new Extra cautious setting. No production fix, threshold change, signing,
preparation or app action is part of this review.

## Requirement and implementation

The [WCAG normative definition](https://www.w3.org/TR/WCAG22/#dfn-general-flash-and-red-flash-thresholds)
uses the phrase "combined area of flashes occurring concurrently" for its area
exemption. [ITU-R BT.1702-3, Annex 1, Guideline 1](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1702-3-202311-I!!PDF-E.pdf)
uses the same phrase for the displayed-screen test. Both primary documents were
read on October 16. Frequency and concurrent area are distinct conditions;
a trailing one-second frequency count does not make its entire spatial history
concurrent. This interpretation is sufficient for the separated-burst fixture;
it does not prescribe a complete algorithm for arbitrary footage.

`StreamingAnalyzer._record` first sums completion masks per pixel over the
trailing closed second. It selects pixels with more than three completions,
then measures the union of those pixels in each area window. A pixel remains
in that union after its flashing has ended. The accumulator retains completion
timestamps and masks, but not each paired flash's start and end. The mask
returned by `GeneralFlashTracker.step` identifies completions on that frame.

The same calculation is present in the original implementation, commit
`3915569fefe62780e25315dc44ddbddfc35278e0`. The original commit and the reviewed
implementation decisions in `flashmap/docs/SPEC_SOURCES.md` document pairing,
threshold crossing, window placement and spatial geometry. They do not identify
this temporal area pooling as a deliberate additional policy. The nearby
conservative comment concerns the reported hide interval, not this area rule.
Thus its conservative effect on these fixtures is established; an intentional,
reviewed product-policy rationale is not. It should not be represented as an
exact measurement of concurrent area. This is not a general proof that every
part of the detector is conservative.

## Deterministic evidence

[Fixtures and measurements](../../results/detector-area-review-2026-10-16/fixtures.json)
and [receipt](../../results/detector-area-review-2026-10-16/receipt.json).
The real streaming analyzer consumes numeric grayscale arrays. No video is
encoded, opened or displayed. The broadcast pattern rule is disabled only in
the fixture so that this test isolates general flashing.

Each of two disjoint rectangular patches flashes four times. Patch A is bright
at 40-80, 120-160, 200-240 and 280-320 ms. Patch B is bright at 520-560, 600-640,
680-720 and 760-800 ms. Even including the preceding frame as the beginning of
each transition leaves a gap between the complete bursts. Grayscale changes
from 0.2 to 0.8 in encoded values, comfortably meeting the unchanged luminance
rules after the existing conversions. There is no red stimulus.

| Window | Largest active patch | Reported pooled area | First pooled failure |
| --- | ---: | ---: | ---: |
| WCAG reference, 64 by 36 | 19.44% | 38.89% | 800 ms |
| Room, 22 by 22 | 18.18% | 36.36% | 800 ms |
| Broadcast screen, 192 by 108 | 19.44% | 38.89% | 800 ms |

Each separated case produces a reported segment from 0 to 1080 ms. At no point
do the patches flash together. The unchanged 25% area limit is enough to
explain the mismatch; no more permissive number is proposed.

Controls across all three windows: one patch alone, three flashes per patch,
expired history and a luminance change below threshold produce no segment.
Simultaneous large-area flashes do produce a segment. Overlapping pulses with
different completion frames also produce a segment. That last control matters:
intersecting the pooled mask with only the current completion mask would lose
it, although its two pulses overlap in time. A one-line current-frame filter
is therefore not a justified repair.

The tests record 24 passing characterizations and three strict expected
failures for the unmet concurrent-area expectation. Running with `--runxfail`
reproduces all three failures. Expected failures are known defects, not passing
conformance evidence. The independent schedule uses rectangle dimensions and
known time intervals; it is not a second general-purpose video analyzer.

## Existing otter results and next step

Both existing otter reports were produced by this accumulator. Their stored
maps retain summary areas, time bounds and counts, but not the masks and paired
flash lifetimes needed to attribute an individual finding to temporal pooling.
Consequently this review does not establish what fraction of either otter's
cover time is excessive, or whether either clip would pass a corrected detector.
The original and candidate report hashes are recorded in the receipt; no report,
prepared rendition or signature was changed. The strict room and cover padding
are separate mechanisms and remain unchanged.

Next action: review a duration-aware definition of concurrency, preserving the
positive control for overlapping pulses with offset completion times. The
smallest justified design direction is to retain each paired flash's support
interval and measure temporal overlap of those intervals instead of a spatial
union across the entire second. Keep the frequency and luminance limits. This
is a proposed direction, not a validated algorithm or implemented fix. Only
then repair the detector with negative and positive regressions and compare
unsigned analyses. Existing signed assets stay unchanged; any regenerated
maps and renditions need separate review and verification.
This work does not provide a clinical safety conclusion or clear either clip.

Isolation: this review is on `codex/detector-area-review-2026-10-16` in the
separate `calm-frames-detector-review` worktree. The Acadia branch and running
app were untouched. No screenshot, recording, UI control, new bundle or key.

Design-only follow-up: [duration-aware semantics and test plan](detector-area-design-2026-10-16.md). No production repair is included.
