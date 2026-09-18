# How to label a segment

You are deciding, for each one second window of each segment, whether the window shows flashing
that meets the general flash condition or the red flash condition. That is all. You are not
deciding whether the clip is safe, whether a player should hide it, or whether a detector was
right, and you will not be shown what any detector said.

Please read all of this before the first segment, and keep it open while you work.

## Who does what

Two people label, separately, without talking about any segment until both sheets are saved.
That is the whole point of doing it twice: the agreement between two people who have not
compared notes is a number, and the agreement between two people who have is not.

**Alex**, your sheet is `eval/labeling/labels_labeller_a.csv`. Please do all 40 segments. Each
one is ten rows, so 400 rows in all. A segment takes a minute or two once you have the hang of
the figure, so set aside about an hour and take breaks.

**Rachel**, your sheet is `eval/labeling/labels_labeller_b.csv`. Please do at least the first
15, `seg000` through `seg014`, and as many more as you have time for. The ids are already in a
shuffled order, so the first 15 are a random sample rather than the easy ones. Fifteen is the
floor the evaluation plan sets for the second labeller, and the agreement score uses whatever
you both labelled.

Neither of you sees the other's sheet until both are saved, and neither of you opens
`pool_key.json` at all.

If you find you cannot call a window, mark it unlabelable. An honest "cannot tell" is worth
more than a guess, and the two of you disagreeing about a hard segment is useful information
rather than a problem.

## What you get

- `pool.json`, a list of segment ids. Each segment is ten seconds of some video.
- `plots/segXXX.png`, one figure per segment, with three panels and a vertical line at every
  one second window boundary.
- `labels_<yourname>.csv`, your sheet, one row per window, to fill in.

You do not get the title, the source, where the segment sits in the film, or which detector
proposed it. That is on purpose: the point of the exercise is to compare detectors against the
spec, and knowing that a detector picked a segment would tell you what answer to give.

**Do not open `pool_key.json`.** It holds the mapping back to the titles. Opening it before you
finish unblinds the review.

**Do not play the clips.** Not slowed down, not dimmed, not "just to check". These are hazardous
files and the plots are the whole method. If a window cannot be called from the plot, that is
what the `unlabelable` column is for, and an honest "cannot tell" is worth more to us than a
guess.

## The two conditions, quoted

Both come from WCAG 2.2, and the full quotes with their links are in
`flashmap/docs/SPEC_SOURCES.md`. Nothing here is from memory and nothing here is our
interpretation.

> - A general flash is defined as a pair of opposing changes in relative luminance of 10% or
>   more of the maximum relative luminance (1.0) where the relative luminance of the darker
>   image is below 0.80; and where "a pair of opposing changes" is an increase followed by a
>   decrease, or a decrease followed by an increase, and
> - A red flash is defined as any pair of opposing transitions involving a saturated red

> a flash or rapidly changing image sequence is below the threshold (i.e., content passes) if
> any of the following are true:
>
> 1. there are no more than three general flashes and / or no more than three red flashes
>    within any one-second period; or
> 2. the combined area of flashes occurring concurrently occupies no more than a total of
>    .006 steradians within any 10 degree visual field on the screen (25% of any 10 degree
>    visual field on the screen) at typical viewing distance

And the working definition of a saturated red, from the same glossary entry, Note 3:

> a pair of opposing transitions where, one transition is either to or from a state with a value
> R/(R + G + B) that is greater than or equal to 0.8, and the difference between states is more
> than 0.2 (unitless) in the CIE 1976 UCS chromaticity diagram

## How to read the figure

**Top panel, whole picture relative luminance.** The average brightness of the whole frame, in
linear light. A flash that fills the screen shows up here as a square-ish wave.

**Middle panel, changing region.** The purple line is the average luminance of whichever pixels
changed between the last two frames, so it tracks the flashing part rather than the whole
picture. The solid red line, on the right hand axis, is how much of the busiest 10 degree field
that region fills, which is the quantity the area rule is about; the dotted line across it is
the 25% limit, so red above dotted means the area condition is met. The faint dashed line is the
same region as a share of the whole picture, which is always the smaller number and is there
only for context.

**Bottom panel, red ratio.** R/(R + G + B) in linear light, averaged over the changing region.
The dotted line is 0.8. A trace that never gets near 0.8 cannot be a red flash. A trace that
crosses it might be: red also has to move more than 0.2 in the CIE 1976 UCS diagram, which the
plot cannot show you, so treat a high red ratio as "worth a closer look", not as a yes.

The region series is built with an inspection threshold that is **not** a spec number. It picks
which pixels count as "changing" and nothing else.

## Calling a window

For each window, mark one of:

- `1`, the window shows flashing meeting the general or the red condition: more than three
  flashes inside that one second, each with a luminance change of at least 0.10 with the darker
  state below 0.80 (or a red pair as above), and the flashing covering more than a quarter of a
  10 degree field, which is roughly a third of the picture's width by a third of its height.
- `0`, it does not.
- `x` in the `unlabelable` column, you cannot tell from the plot. Say why in `notes`.

Two things that are not flashing, and that the plots make look like it:

- **a cut.** One step from one level to another, once. A flash is a pair of opposing changes, so
  a single step in one direction is not one. A shot that cuts back and forth more than three
  times a second is a different matter and does count.
- **a slow ramp.** A fade that crosses 0.10 over a second is not a pair of opposing changes.

If a segment is mostly one long cut-heavy sequence rather than flashing, say so in `notes` on
its first row. Those get reported separately.

## Counting flashes

Count the peaks and valleys in the middle panel inside the window. A flash is one peak plus one
valley, so six turning points in a second is three flashes, eight is four. Four or more flashes
in any one second is over the limit; three is not.

The windows are drawn on the figure at whole seconds. If a run of flashing straddles a boundary,
label both windows on what they each contain.

## Filling the sheet

One row per window, already laid out for you. Fill `label` with `1` or `0`, or put `x` in
`unlabelable` and leave `label` empty. `notes` is free text and is read.

Do not go back and change an earlier answer after you have seen a later segment. First answers
are what we compare between the two of you, before any discussion. After we have both sheets we
will look at the disagreements together and agree a final answer, and that agreed set is what
the numbers use.

When you are done, save the file and say so. Nothing is scored until both sheets are in.

## When both sheets are in

In this order, because the plan freezes labels before any comparison and the analysis refuses
to run on a sheet that is not committed:

1. Commit both sheets. `git add eval/labeling/labels_*.csv && git commit`. The analysis records
   the SHA-256 of each sheet in its output, so the numbers always name the labels they came
   from.
2. Run `make realclips-status`, or `python eval/realclips/report.py`. It writes
   `results/realclips.json`: precision and recall per detector against your labels, a bootstrap
   interval over titles, Cohen's kappa between the two of you on the answers as first given, and
   the per source breakdown.
3. Look at the disagreements together. The script holds every window you two called differently
   out of the metrics rather than picking a side, and it says how many there are. Agree an
   answer for each, write the agreed answers into a third sheet, commit that too, and run the
   analysis again with that sheet named:
   `python eval/realclips/report.py --adjudicated eval/labeling/labels_agreed.csv`.
   The agreed answers are then the ones the metrics use, and the kappa stays between your two
   original sheets, which is what it is for.

If a sheet is not committed the analysis stops and says which one. That is the freeze rule
working, not a bug.
