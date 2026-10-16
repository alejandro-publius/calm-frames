# Proposed duration-aware area refinement

Design only, October 16, 2026. No production implementation or approved policy
change. This follows the [reproduced mismatch](detector-area-review-2026-10-16.md)
on the separate detector review branch. Acadia, thresholds, signed artifacts,
preparation and the installed app remain unchanged.

## Decision proposed

Replace the spatial union across an entire second only when a conservative
bound on actual temporal overlap can be established. Keep the current pooled
finding when relevant event timing is unresolved. Do not substitute a mask of
flashes completing on the current frame: the existing offset-completion
positive control demonstrates the false-negative risk of that shortcut.

The [WCAG definition](https://www.w3.org/TR/WCAG22/#dfn-general-flash-and-red-flash-thresholds)
and [ITU-R BT.1702-3 Annex 1, Guideline 1](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1702-3-202311-I!!PDF-E.pdf)
refer to "combined area of flashes occurring concurrently". WCAG Note 2 defines
transitions through adjacent peaks and valleys. These support distinguishing
overlap from a whole-second union. Neither source specifies the sampled event
interval, plateau handling, endpoint convention, or a per-pixel counting
algorithm. The choices below are proposed engineering conventions, not extra
normative thresholds. The primary texts were read on October 16.

## Event contract before changing area calculation

For each currently qualified, non-overlapping pair of transitions retain:

- Kind: general or red. Keep the existing amplitude, darker-state, red ratio,
  chromatic distance and pairing rules unchanged in this work.
- Pixel identity or a mask whose pixels share the same timing. Distinct
  per-pixel timings must not be collapsed into one guessed common interval.
- `completed_ms`: the current second qualifying transition timestamp. Keep this
  for count compatibility; it is not necessarily the physical end of the flash.
- `start_lower_ms`, `end_upper_ms`: a conservative temporal envelope containing
  both transitions, including the excursion between them.
- `timing_resolved`: whether evidence establishes both envelope bounds.

Support is the whole paired excursion, not just the bright portion and not
just its two completion frames. A dark pulse on a bright background needs the
same treatment. The fixture's known bright intervals are an independent
schedule, not a recipe for deriving event duration from arbitrary footage.

The onset bound must include the last sample preceding departure from the
first transition's starting extreme. Do not use the timestamp at which its
amplitude first crosses the threshold. End support must include the final
extreme of the second transition and its sampling uncertainty. Ending at the
second threshold crossing can truncate a continuing ramp and miss overlap.
Use observed neighboring presentation timestamps to bound uncertainty, not a
new fixed duration or assumed frame rate. For known piecewise constant fixture
signals, exact supplied excursion bounds are permitted in the oracle.

Plateau convention proposed for review: a constant plateau at the starting
extreme is not itself a transition; departure begins after its last sample.
A plateau at the return extreme begins at its first sample, but finalize that
extreme only after reversal or end-of-stream evidence. An ambiguous plateau,
sub-threshold reversal, long ramp or unfinished pair must not silently acquire
a short support interval. A relevant unresolved envelope keeps the pooled
finding. No timeout may drop pending state just to save memory.

This metadata contract is new work. The current Boolean completion mask alone
cannot reconstruct these envelopes. Same-direction threshold crossings and
minor reversals make the present anchor state insufficient as an unreviewed
substitute for adjacent extrema. Prototype timing extraction separately and
prove it with signal traces before enabling any suppression.

## Candidate calculation, conditional on resolved envelopes

This is a conservative refinement of the current candidate set, not a complete
new standards-conformance algorithm. For evaluation time `t`, keep the existing
closed frequency window `W = [t - 1000, t]` and completion counts:

```
N[k,p,t] = number of qualified events of kind k at pixel p with completion in W
R[k,t]   = pixels where N[k,p,t] > 3
A[k,t,u] = pixels in R[k,t] covered by at least one relevant event envelope at u
```

Maintain separate indexes for counts and support. Count events by completion in
W; include every qualified support intersecting W even if its completion lies
outside W. A pending possible next flash on an eligible pixel also makes timing
unresolved until its qualification and support are established. Otherwise a
fifth pending flash could overlap another patch while the first four already
qualify its pixel for R, and a completed-event-only filter would miss that
overlap. Evaluate support intersections with W. For every existing spatial
window placement, measure the union of pixels in
`A` at each time slice. A pixel shared by two envelopes counts once. Retain a
finding if any slice exceeds the existing area limit. If relevant timing is
unresolved, retain the current pooled finding for that kind and window instead.
Suppress a pooled finding only when all relevant timing is resolved and every
slice is at or below the limit.

For a finite set of resolved intervals, sort their endpoints and evaluate each
non-empty interval between consecutive endpoints, clipped to W. Use half-open
envelopes `[start_lower_ms, end_upper_ms)`: an end and a start at the same exact
time do not create positive-duration overlap. Process removals before additions
at a tied endpoint. If sampled uncertainty makes the envelopes overlap, count
that overlap. Do not add a minimum overlap duration. Do not sum separate maxima
from different time slices or different window placements.

Counts remain separate for general and red. Never make four flashes from two
general plus two red events. A pulse that qualifies for both keeps independent
records; the existing final segment union and opaque red-cover rule remain.
Spatial geometry also remains unchanged: baseline windows always apply, room
windows can only add findings, and broadcast's whole-picture baseline is not
replaced by a room window. Guard bands and interval merging run after detection
exactly as before; they do not define concurrent flash area.

## Deterministic test contract

The machine-readable [case list](../../results/detector-area-review-2026-10-16/design-cases.json)
is a specification for future tests, not a new executed suite. Use tiny numeric
arrays and exact event tables, never encoded or displayed hazardous media.
Run temporal cases through both general and red qualification paths, then the
shared area layer. Use independent interval arithmetic as the expected oracle;
do not compute expectations by calling the implementation under test.

1. Retain the existing separated-burst counterexample and offset-completion
   positive control, with both polarity directions. Also test a long ramp whose
   second threshold crossing precedes its final extreme. Unknown timing must
   fall back to pooled output, not turn the positive case into a pass.
2. Test four and three completions, the exact one-second left boundary and one
   representable time step on either side. Exercise support crossing each
   boundary, a support ending exactly where another starts, and overlap shorter
   than a frame under exact event-table inputs. No cadence assumption or epsilon
   chosen to make a test pass.
3. Exercise general-only, red-only, dual-qualified and mixed sub-limit sequences.
   The case list supplies deterministic linear-light states and arithmetic for
   red-only and dual-qualified pairs, plus gray states for general-only. Check
   the existing ratio and UCS-distance rules independently. The interval assembler
   must receive real tracker output as well as synthetic event records. A
   grayscale-only test of the common accumulator is not red-path coverage.
   These are explicit synthetic analyzer inputs, not decoded-media validation;
   the case list separately supplies the broadcast signal-level convention.
4. Repeat geometry cases for WCAG reference, strict room and broadcast baseline.
   Exact-quarter and one-pixel-over masks use 576/577 pixels in 64 by 36,
   121/122 in 22 by 22, and 5184/5185 in 192 by 108. Place every mask inside its
   tested window, translate it, and test all legal sliding placements. Duplicate
   pixel membership cannot increase area. Baseline plus room cannot remove a
   baseline finding. Keep existing letterbox and physical-room mapping tests.
5. Whole-stream, chunked and overlapping-chunk input must agree. Test variable
   PTS gaps, plateaus, EOF, and multiple per-pixel envelopes. Resource exhaustion
   or missing bounds must preserve a finding or explicitly fail analysis; never
   silently discard timing needed to evaluate overlap.

Known expected outcomes are conditional on supplied event supports. Cases with
ambiguous timing or counting conventions are marked `defer` or `fallback` in
the case list. They must not be converted to permissive expected results merely
to turn the suite green. Existing strict expected-failure cases remain until a
reviewed implementation actually satisfies them.

## Unresolved questions and false-negative risks

- **Event boundaries:** how should the existing first-threshold tracker expose
  adjacent extrema through minor reversals and repeated same-direction threshold
  crossings? End timing must not be inferred solely from completion. A bound
  that is too short can miss simultaneous flashing; a bound that is too long
  preserves excess covers.
- **Frequency convention:** keeping completion counts is a compatibility choice.
  The standards do not explicitly endorse it. A long first transition may start
  before W and finish inside it. Compare leading-edge, completion and full-pair
  interpretations without silently changing counts in an area-only repair.
- **Spatial identity:** the current per-pixel frequency rule can differ from a
  region-based count when flashing moves across the screen. This proposal does
  not validate that pre-existing rule. It cannot support a global no-false-
  negatives or full-conformance claim.
- **Sampling and plateaus:** approve endpoint and uncertainty rules against
  actual presentation timestamps. The half-open convention is proposed, not
  prescribed by either source. Unknown duration must not become zero duration.
- **Streaming finality:** finalized extrema may require future frames. Determine
  how provisional evidence is retained until it can be resolved. A window must
  not be discarded before every event affecting its overlap decision is known. Count expiry must not evict a still-relevant support
  interval or pending possible fifth flash.
- **Evidence identity:** any future enabled behavior needs an explicit algorithm
  revision and documented area basis. Signed maps must not silently inherit a
  different interpretation under an unchanged generator identity.

## Actionable sequence and stop condition

First review and settle the event-boundary contract and the scope of retained
completion counting. Then implement timing extraction and a review-only overlap
oracle with the case list, including negative controls. Prove an attempted
same-completion-frame shortcut fails the positive cases. Next compare both
methods headlessly on existing fixture traces and unsigned source analyses,
recording every removed and retained finding. Inspect removed findings before
considering production changes. Do not regenerate or resign a trusted bundle
as part of that comparison.

Approval to implement a repair is separate from this design follow-up. There is
no validated replacement detector here. This document and case list are the
completed deliverable; stop after saving and checking them. No owner app action
is needed. The remaining decisions are technical review questions, not a request
for the owner to judge footage safety.
