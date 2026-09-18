# SPEC_SOURCES

The threshold sources live with the analyser that uses them, at
[`flashmap/docs/SPEC_SOURCES.md`](../flashmap/docs/SPEC_SOURCES.md). That file is the only
place a threshold may come from, as CLAUDE.md says, and it ships inside the Apache-2.0 flashmap
package so a studio using the analyser on its own still has the quoted text and the links.

This page exists so that anyone who looks for `docs/SPEC_SOURCES.md` lands in the right place.
It repeats no number that flashmap already uses, because two copies of a threshold is one copy
too many.

One exception, and it is temporary: the regular-pattern research below. Those quotes are for a
rule that does not exist yet, so they have no home in flashmap's file. When the pattern rule is
built, its quotes move into `flashmap/docs/SPEC_SOURCES.md` and this section shrinks back to a
pointer. **Until they have moved, no code may read a number from this page.**

## What is in there

Quoted text, with a link to the page it was read on, for:

1. WCAG 2.2 Success Criterion 2.3.1, Three Flashes or Below Threshold.
2. The WCAG 2.2 glossary definition of the general flash and red flash thresholds, with all
   four of its notes: what counts as a flash, the three per second limit, the 25% of a 10
   degree visual field rule, and the saturated red working definition.
3. The WCAG 2.2 glossary definition of relative luminance, including the sRGB transfer
   function.
4. Understanding SC 2.3.1, which supplies the CIE 1976 UCS arithmetic for the red flash test,
   the sRGB to XYZ matrix, and the statement that the R, G and B in those formulas are the
   linear light values.
5. ITU-R BT.1702-3, Annex 1 Guideline 1 and Annex 2, for the broadcast profile. Standard
   dynamic range only.
6. ITU-R BT.709-6 and ITU-R BT.601-7, for which matrix an untagged stream should get.
7. FFmpeg's `libavutil/pixfmt.h`, for what a `yuvj` pixel format means.

## What could not be verified

Three things, all named in that file and none of them used as a threshold:

- **The line count at which an untagged stream switches from BT.601 to BT.709.** No spec states
  one. flashmap uses 720 lines as a project convention, records the guess in every map as
  `color.matrix_source`, and lets it be overridden.
- **What range an untagged non-yuvj stream should get.** No primary document says. flashmap
  assumes limited range and records `color.range_source: "default-limited"`.
- **ISO 9241-391 itself**, which is behind a paywall. Everything flashmap uses from it is the
  working definition that the W3C reproduces in WCAG 2.2 and its Understanding document, quoted
  in full.

ITU-R BT.1702-3 was fetched in full from the ITU, so the broadcast profile is grounded. Its HDR
branch is not implemented and flashmap refuses HLG and PQ input rather than measuring it with
the SDR curve.

---

# Regular patterns: sources for a rule that is not built yet

Researched and fetched on 2026-09-17, for the planned flashmap rule on high contrast regular
patterns (stripes, gratings, checkerboards). This is a separate hazard from the general flash
and red flash rules that flashmap already implements, and it needs its own sources.

Two conventions used below, both to keep the repo style rule and the quote honest at the same
time:

- The ITU prints its bullet markers as dashes. CLAUDE.md forbids en dashes anywhere in this
  repo, so the bullets appear below as `-`. No word is changed.
- Whitespace is normalised from the PDF text layer (the extractor inserts stray spaces inside
  words). Wording, punctuation and every number are as printed.

## P1. ITU-R BT.1702-3, Annex 1, Guideline 2, Potentially harmful patterns

**Verified.**

Source: Recommendation ITU-R BT.1702-3 (11/2023), "Guidance for the reduction of
photosensitive epileptic seizures caused by television". The full PDF is a free download from
the ITU. Read on 2026-09-17 from the PDF below, SHA-256
`9d1167de5553a82c633020a44b5f729118e90ff6536a3b519f1813e235437bf2`.
URL: https://www.itu.int/rec/R-REC-BT.1702/en
PDF: https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1702-3-202311-I!!PDF-E.pdf

Revision checked on the same day at the URL above: BT.1702-3 (11/2023) is in force. BT.1702-2
(10/2019), BT.1702-1 (07/2018) and BT.1702-0 (02/2005) are superseded. This is the same
document flashmap already quotes for Guideline 1, so the pattern rule and the flash rule would
share one source.

Verified quote, the scope sentence that governs both guidelines:

> To reduce risk, the following guidelines on visual content should be applied when flashing or
> regular patterns are clearly discernible in normal domestic viewing conditions.

Verified quote, Annex 1, Guideline 2, in full:

> **Guideline 2  Potentially harmful patterns**
>
> Potentially harmful regular patterns occur when an image contains light and dark pairs of
> clearly discernible stripes in any orientation. The stripes may be parallel or radial, curved
> or straight, and may be formed by rows of repetitive elements such as polka dots. If the
> stripes change direction, oscillate, flash or reverse in contrast they are more likely to be
> harmful than if they are stationary.
>
> Attachment 1 to this Annex provides informative guidance for measurement to identify
> potentially harmful patterns.

What this gives us operationally: the definition of the hazard and nothing countable.
Guideline 2 carries no stripe count, no area and no contrast. It defines a pattern as light and
dark pairs of clearly discernible stripes in any orientation, allows them to be parallel or
radial and curved or straight, counts rows of repetitive elements such as polka dots as
stripes, and ranks changing patterns above stationary ones for risk. Every number is in
Attachment 1, which the recommendation labels informative. That distinction is the single most
important thing on this page and section P2 keeps it.

## P2. ITU-R BT.1702-3, Attachment 1 to Annex 1 (informative), the pattern numbers

**Verified as text. Informative in status.** The quote is exact and comes from the primary
document, so it meets the CLAUDE.md bar for a number we may use. What it is not is a
requirement: the ITU marks the attachment `(informative)` and its first sentence says the
criteria are used by some administrations, not by all. Anything flashmap reports from it has to
say where it came from.

Source, URL and PDF as in P1. Read on 2026-09-17.

Verified quote, Attachment 1 to Annex 1, in full:

> **Attachment 1**
> **to Annex 1**
> **(informative)**
>
> **Guidance on measurement criteria to identify potentially harmful patterns**
>
> The following additional guidance on the identification of potentially harmful regular
> patterns is used by some administrations.
>
> Potentially harmful regular patterning may occur if an image contains more than five light
> and dark pairs of clearly discernible stripes in any orientation when either of the following
> two conditions apply:
>
> - the stripes are stationary and the pattern occupies more than 40% of the displayed screen
>   area; or
> - the stripes change direction, oscillate, flash, or reverse in contrast and the pattern
>   occupies more than 25% of the displayed screen area.
>
> For a pattern to be considered potentially harmful, the difference between the luminance of
> the darker and lighter bars of the pattern will be the same as the difference between the
> darker and brighter images of a potentially harmful flash described in Guideline 1 above.
>
> If the patterns obviously flow smoothly across, into, or out of the screen in one direction
> they are exempt from restriction.

Numbers in that quote, and what each one means operationally:

| Number | Meaning | Depends on |
| --- | --- | --- |
| more than five | light and dark pairs of clearly discernible stripes, so six pairs, which is twelve bars, is the first count that can fail | nothing, it is a count over the picture in any orientation |
| 40% | of the displayed screen area, the area at which a stationary pattern becomes potentially harmful | the pattern being stationary |
| 25% | of the displayed screen area, the area at which a pattern becomes potentially harmful when it changes direction, oscillates, flashes or reverses in contrast | the pattern moving, in any of those four ways |
| the Guideline 1 flash difference | the light to dark bar difference a pattern must reach. For SDR that is the number flashmap already has in section 5 of the flashmap file: the darker state below 160 cd/m2 and a difference of 20 cd/m2 or more | the same SDR luminance mapping flashmap already uses, peak white 200 cd/m2 through the BT.1886 curve |
| exempt | a pattern that obviously flows smoothly across, into or out of the screen in one direction is not restricted at all | the motion classification, which is the risky judgement, see the recommendation below |

Three things the quote settles, which matter when this is coded:

1. The stripe count and the area are one test, not two: the count is a gate ("more than five
   light and dark pairs") and then either area condition can trip it.
2. The contrast condition is separate and additional. A pattern only counts if its bar to bar
   difference reaches the flash difference. flashmap has that arithmetic already.
3. The static and moving cases differ only in the area limit, 40% against 25%. Nothing in the
   quote gives a duration, a persistence time, a stripe width, or a spatial frequency.

On area: BT.1702-3 Note 4 explains "displayed" for Guideline 1 as allowing for overscan of
3.5% to 1% of picture width or height. Attachment 1 says "displayed screen area" without
repeating the note. flashmap measures on the picture after letterbox and pillarbox removal
(implementation decision 5 in the flashmap file) and does not implement the overscan allowance,
which makes it stricter. The pattern rule should measure the same way, for the same reason.

## P3. Ofcom's guidance note on flashing images and regular patterns

**Not verified. We could not read Ofcom's own copy.**

Every ofcom.org.uk URL we tried on 2026-09-17 answered HTTP 403 with a Cloudflare "Just a
moment..." interstitial, to a plain fetch and to curl with a desktop browser user agent alike.
No browser is connected to this session, so there was no second route. The documents we wanted,
and could not open:

- Ofcom, Guidance Notes, Section 2: Harm and Offence, Issue Twelve, 18 July 2017. Annex 1 of
  that document is the Ofcom Guidance Note on Flashing Images and Regular Patterns in
  Television. 403 at
  https://www.ofcom.org.uk/siteassets/resources/documents/tv-radio-and-on-demand/broadcast-guidance/programme-guidance/broadcast-code-guidance/section-2-guidance-notes.pdf
- The standalone note, which Ofcom's own listing labels a legacy document. 403 at
  https://www.ofcom.org.uk/siteassets/resources/documents/tv-radio-and-on-demand/broadcast-guidance/gn_flash.pdf
  and at https://www.ofcom.org.uk/__data/assets/pdf_file/0021/16248/gn_flash.pdf
- Ofcom Broadcasting Code, Section Two, rule 2.12, the rule the guidance note serves. 403 at
  https://www.ofcom.org.uk/tv-radio-and-on-demand/broadcast-standards/section-two-harm-offence

So **no number is taken from Ofcom** and nothing in the code may cite Ofcom as its source. The
gap is worth re-trying from a machine with a browser, because Ofcom's wording is more precise
than the ITU attachment on one point, as the next paragraph shows.

What we did read, and why it still does not count: a third party, Clearcast, hosts a copy of
Ofcom's Guidance Notes Section 2, Issue Eleven, 1 July 2015, at
https://clearcast.co.uk/wp-content/uploads/2024/02/Ofcom-Guidance-on-Harm-and-Offence-1.pdf
(read 2026-09-17, SHA-256
`858ef6dc06b1445fff832680c16be7e1a1198a92eb3b222160bceeb35bb6d41b`). It is not Ofcom, it is not
the current issue, and we cannot diff it against the current issue while ofcom.org.uk is closed
to us. It is recorded here only so that whoever can open Ofcom's copy knows what to compare
against.

> **Do not take a number out of the next block.** It is a third-party copy of a superseded
> issue and it is on this page as a lead, not as a source.

Read from that copy, Annex 1, paragraphs 5 and 5.1:

> 5. A potentially harmful regular pattern contains clearly discernible stripes when there are
> more than five light-dark pairs of stripes in any orientation. The stripes may be parallel or
> radial, curved or straight, and may be formed by rows of repetitive elements such as polka
> dots. If the stripes change direction, oscillate, flash or reverse in contrast they are more
> likely to be harmful than if they are stationary. If the patterns obviously flow smoothly
> across, into, or out of the screen in one direction they are exempt from restriction.
>
> 5.1. Potentially harmful patterns are not permitted when either of the following two
> conditions apply:
>
> i. the stripes are stationary and the pattern occupies more than 40% of the displayed screen
> area; or
>
> ii. the stripes change direction, oscillate, flash, or reverse in contrast and the pattern
> occupies more than twenty five per cent of screen area; and in addition to either of the
> above two conditions applying, when
>
> iii. the screen luminance of the darker bars in the pattern is below 160 cd.m-2 and differs
> from the lighter bars by 20 cd.m-2 or more (see notes 1 and 2).

The point of interest: this wording spells the contrast condition out as its own clause iii
that must apply in addition to the area condition, where BT.1702-3's attachment states it as a
sentence. The two read the same way. That is a reason to think our reading of the ITU text is
the intended one, and it is not a reason to cite Ofcom for anything.

## P4. WCAG 2.2 does not cover regular patterns at all

**Verified, and it is a negative result worth writing down.**

Source: Understanding Success Criterion 2.3.1: Three Flashes or Below Threshold, W3C, read
2026-09-17.
URL: https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html

The criterion itself is about flashing:

> Web pages do not contain anything that flashes more than three times in any one second
> period, or the flash is below the general flash and red flash thresholds.

Every occurrence of the word "pattern" in SC 2.3.1 and its Understanding document is the same
exemption, quoted in full in section 2 of the flashmap file:

> Exception: Flashing that is a fine, balanced, pattern such as white noise or an alternating
> checkerboard pattern with "squares" smaller than 0.1 degree (of visual field at typical
> viewing distance) on a side does not violate the thresholds.

The word "stripe" does not occur. There is no WCAG requirement about stripe counts, static
patterns, pattern area or pattern contrast, and the one pattern sentence WCAG has lets content
off rather than catching it.

Consequences, and they are firm:

- The pattern rule is not a WCAG rule. It must not change any WCAG pass or fail verdict, must
  not appear in the WCAG profile, and must never be described as WCAG conformance in the
  README, the Devpost text or the video.
- Our house line, that room settings can only make things stricter than WCAG, is unaffected. A
  pattern hide is strictly extra.

## P5. The Harding test and HardingFPA

**Not a source. Not verified. Nothing from here is used.**

HardingFPA is a commercial analyser sold by Cambridge Research Systems and Whitedot Scientific.
Its own pages are marketing and product support for a closed implementation, not a published
threshold, so under CLAUDE.md they cannot supply a number. Named here because they are the
first thing a search returns and somebody will find them again.

Two specific claims seen only on vendor and third-party pages, and therefore **not usable**:

- That a pattern must stay stationary for about half a second before it fails. No primary
  document we read contains a persistence time for patterns. If the analyser needs one to be
  stable, it is detector tuning and gets written down as tuning, not as a threshold.
- Pattern contrast and area limits attributed to the tool. Where those match BT.1702-3's
  Attachment 1 we already have the number from the ITU, which is where it should be cited from.

Secondary literature exists and was not used for any number either: a 2025 gap analysis of
international photosensitive epilepsy guidelines and a 2025 conformance evaluation of video
safety tools, both on PubMed Central. They are useful reading for whoever picks up the Ofcom
gap. They are not standards.

## P6. Still unread

- The Japanese NAB and ARIB guidance, which BT.1702-3 alludes to as regional variation and
  HardingFPA claims to implement. No primary English copy read. Not used.
- ISO 9241-391, still behind a paywall, as recorded further up this page.

---

## What the pattern rule can defensibly check, given only what is verified

Everything below rests on P1 and P2, which is one document, ITU-R BT.1702-3, read in full from
the ITU on 2026-09-17.

1. **Ship it in the broadcast profile only.** The numbers are BT.1702-3's, and the contrast
   condition is defined by reference to Guideline 1, which flashmap only implements for SDR.
   The WCAG profile gets no pattern rule, because WCAG has none (P4). HLG and PQ input is
   already refused, and the pattern rule inherits that refusal.
2. **Gate on the stripe count.** More than five light and dark pairs of clearly discernible
   stripes in any orientation, so six pairs or more. Radial and curved stripes and rows of
   repeating elements count as stripes, which means an orientation-agnostic detector, not a
   horizontal and vertical one.
3. **Reuse the flash contrast arithmetic for the bars.** Darker bar below 160 cd/m2 and a
   difference of 20 cd/m2 or more from the lighter bar, through the SDR mapping flashmap
   already has pinned by `tests/test_bt1702_table.py`. No new luminance number is introduced.
4. **Two area limits, on the picture.** More than 40% when the pattern is stationary, more than
   25% when it changes direction, oscillates, flashes or reverses in contrast. Measured as a
   fraction of the picture after letterbox and pillarbox removal, the same as every other area
   in flashmap.
5. **When the motion class is uncertain, take the stricter branch.** Stationary against moving
   decides 40% against 25%, so an unsure detector uses 25%. The smooth-flow exemption is the
   one place where a wrong call hides a hazard rather than over-reporting one, so it only
   applies when the flow is unambiguous, and every application of it is recorded in the sidecar
   so a reviewer can see what was let through.
6. **Say where the numbers come from, in the artefact.** Attachment 1 is informative and says
   it describes what some administrations do. The sidecar should carry that, for example
   `profile.pattern_rule_source: "ITU-R BT.1702-3 Attachment 1 to Annex 1 (informative)"`, and
   the pattern verdict should be reportable on its own so a consumer can see which hides came
   from the pattern rule and which from the flash rules.

What it must not check, because no verified source gives a number:

- Any persistence or duration threshold for a pattern, including the half second from the
  vendor pages (P5). BT.1702-3 gives none.
- Any stripe width, spatial frequency, or cycles-per-degree band as a threshold. The specs say
  "clearly discernible" and nothing more. If the detector needs a band to work, it is tuning,
  like the letterbox detector's numbers in implementation decision 6, with its defaults written
  out and recorded in the sidecar.
- Anything cited to Ofcom, until somebody opens Ofcom's own copy (P3).
- Any HDR pattern rule, any pattern rule inside the WCAG verdict, and any pattern risk score.

One more task for whoever builds it, and it is not this lane's file to edit: section 5 of
`flashmap/docs/SPEC_SOURCES.md` currently lists Guideline 2 under "Not implemented from
BT.1702-3, on purpose", and the sidecar says the same in `profile.rules_not_implemented`. Both
have to change in the same commit as the rule, and the quotes in P1 and P2 move there at the
same time.
