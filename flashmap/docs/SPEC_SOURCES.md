# SPEC_SOURCES

Every number flashmap uses lives here with the exact quoted text it came from and a link
to the page it was read on. Nothing in the code may introduce a threshold that is not on
this page. If you need a new number, quote it here first.

Fetched on 2026-09-17. Re-read the source pages before quoting them anywhere else.

Two kinds of entry appear below:

- **Verified** means the wording is quoted from the primary document and the number is in
  that wording.
- **Not verified** means we could not read the number in a primary document. Those numbers
  are not used as thresholds anywhere in the code. Where an under-specified part of a spec
  forced a choice, the choice is written out under "Implementation decisions" and is named
  in the sidecar so a reader can see what was assumed.

---

## 1. WCAG 2.2, Success Criterion 2.3.1 Three Flashes or Below Threshold

Source: Web Content Accessibility Guidelines (WCAG) 2.2, W3C Recommendation.
URL: https://www.w3.org/TR/WCAG22/#three-flashes-or-below-threshold

Verified quote:

> **Success Criterion 2.3.1 Three Flashes or Below Threshold**
> (Level A)
> Web pages do not contain anything that flashes more than three times in any one second period,
> or the flash is below the general flash and red flash thresholds.
>
> Note
> Since any content that does not meet this success criterion can interfere with a user's
> ability to use the whole page, all content on the web page (whether it is used to meet other
> success criteria or not) must meet this success criterion. See Conformance Requirement 5:
> Non-Interference.

Used for: the pass or fail verdict of `flashmap check` and of the GitHub Action.

---

## 2. WCAG 2.2, definition of "general flash and red flash thresholds"

Source: WCAG 2.2, Appendix A Glossary.
URL: https://www.w3.org/TR/WCAG22/#dfn-general-flash-and-red-flash-thresholds

Verified quote:

> **general flash and red flash thresholds**
>
> a flash or rapidly changing image sequence is below the threshold (i.e., content passes) if
> any of the following are true:
>
> 1. there are no more than three general flashes and / or no more than three red flashes
>    within any one-second period; or
> 2. the combined area of flashes occurring concurrently occupies no more than a total of
>    .006 steradians within any 10 degree visual field on the screen (25% of any 10 degree
>    visual field on the screen) at typical viewing distance
>
> where:
>
> - A general flash is defined as a pair of opposing changes in relative luminance of 10% or
>   more of the maximum relative luminance (1.0) where the relative luminance of the darker
>   image is below 0.80; and where "a pair of opposing changes" is an increase followed by a
>   decrease, or a decrease followed by an increase, and
> - A red flash is defined as any pair of opposing transitions involving a saturated red
>
> Exception: Flashing that is a fine, balanced, pattern such as white noise or an alternating
> checkerboard pattern with "squares" smaller than 0.1 degree (of visual field at typical
> viewing distance) on a side does not violate the thresholds.
>
> **Note 1**
> For general software or web content, using a 341 x 256 pixel rectangle anywhere on the
> displayed screen area when the content is viewed at 1024 x 768 pixels will provide a good
> estimate of a 10 degree visual field for standard screen sizes and viewing distances
> (e.g., 15-17 inch screen at 22-26 inches). This resolution of 75 - 85 ppi is known to be
> lower, and thus more conservative than the nominal CSS pixel resolution of 96 ppi in CSS
> specifications. Higher resolutions displays showing the same rendering of the content yield
> smaller and safer images so it is lower resolutions that are used to define the thresholds.
>
> **Note 2**
> A transition is the change in relative luminance (or relative luminance/color for red
> flashing) between adjacent peaks and valleys in a plot of relative luminance (or relative
> luminance/color for red flashing) measurement against time. A flash consists of two opposing
> transitions.
>
> **Note 3**
> The new working definition in the field for "pair of opposing transitions involving a
> saturated red" (from WCAG 2.2) is a pair of opposing transitions where, one transition is
> either to or from a state with a value R/(R + G + B) that is greater than or equal to 0.8,
> and the difference between states is more than 0.2 (unitless) in the CIE 1976 UCS
> chromaticity diagram. [ISO_9241-391]
>
> **Note 4**
> Tools are available that will carry out analysis from video screen capture. However, no tool
> is necessary to evaluate for this condition if flashing is less than or equal to 3 flashes in
> any one second. Content automatically passes (see #1 and #2 above).

Numbers taken from this quote and used in the code:

| Number | Meaning | Where it is used |
| --- | --- | --- |
| 3 flashes | more than three general or red flashes in any one-second period fails condition 1 | `profiles.WCAG.flash_limit_per_second` |
| 1 second | the counting period | `profiles.WCAG.window_ms = 1000` |
| 0.10 | a general flash transition is 10% or more of the maximum relative luminance (1.0) | `profiles.WCAG.general.min_delta` |
| 0.80 | the relative luminance of the darker image must be below this for a general flash | `profiles.WCAG.general.dark_image_below` |
| 0.25 | 25% of any 10 degree visual field, the area at which condition 2 stops rescuing the content | `profiles.WCAG.area_fraction_limit` |
| 341 / 1024 and 256 / 768 | the 10 degree visual field as a fraction of the screen | `area.wcag_reference_window` |
| 0.8 | R/(R + G + B) at or above this is a saturated red state | `profiles.WCAG.red.saturated_red_ratio` |
| 0.2 | the CIE 1976 UCS chromaticity difference a red transition must exceed | `profiles.WCAG.red.min_ucs_distance` |

Note on .006 steradians: the spec gives it as another way of saying the same thing
("25% of any 10 degree visual field"). flashmap measures the fraction, not the solid angle,
so 0.25 is the number in the code and .006 sr is not used.

The "fine, balanced pattern" exception (white noise, checkerboards below 0.1 degree) is **not
implemented**. flashmap therefore reports some content as failing that the exception would
excuse. That direction is the safe one. It is listed in the sidecar as
`profile.exceptions_not_implemented`.

---

## 3. WCAG 2.2, definition of "relative luminance"

Source: WCAG 2.2, Appendix A Glossary.
URL: https://www.w3.org/TR/WCAG22/#dfn-relative-luminance

Verified quote:

> **relative luminance**
>
> the relative brightness of any point in a colorspace, normalized to 0 for darkest black and
> 1 for lightest white
>
> **Note 1**
> For the sRGB colorspace, the relative luminance of a color is defined as
> L = 0.2126 * R + 0.7152 * G + 0.0722 * B where R, G and B are defined as:
>
> - if RsRGB <= 0.04045 then R = RsRGB/12.92 else R = ((RsRGB+0.055)/1.055) ^ 2.4
> - if GsRGB <= 0.04045 then G = GsRGB/12.92 else G = ((GsRGB+0.055)/1.055) ^ 2.4
> - if BsRGB <= 0.04045 then B = BsRGB/12.92 else B = ((BsRGB+0.055)/1.055) ^ 2.4
>
> and RsRGB, GsRGB, and BsRGB are defined as:
>
> - RsRGB = R8bit/255
> - GsRGB = G8bit/255
> - BsRGB = B8bit/255
>
> The "^" character is the exponentiation operator. (Formula taken from [SRGB].)
>
> **Note 2**
> Before May 2021 the value of 0.04045 in the definition was different (0.03928). It was taken
> from an older version of the specification and has been updated. It has no practical effect
> on the calculations in the context of these guidelines.
>
> **Note 3**
> Almost all systems used today to view web content assume sRGB encoding. Unless it is known
> that another color space will be used to process and display the content, authors should
> evaluate using sRGB colorspace.

Used for: `color.srgb_to_linear` and `color.relative_luminance`, exactly as written, including
the 0.04045 break point, the 12.92 divisor, the 0.055 offset, the 1.055 divisor and the 2.4
exponent.

---

## 4. WCAG 2.2 Understanding 2.3.1: the saturated red arithmetic and the sRGB to XYZ matrix

Source: Understanding Success Criterion 2.3.1: Three Flashes or Below Threshold,
W3C Group Note published by the Accessibility Guidelines Working Group as the companion to
WCAG 2.2.
URL: https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html

Verified quote:

> **Note (new in WCAG 2.2)**
> The new working definition in the field for "pair of opposing transitions involving a
> saturated red" is a pair of opposing transitions where, one transition is either to or from a
> state with a value R/(R + G + B) that is greater than or equal to 0.8, and the difference
> between states is more than 0.2 (unitless) in the CIE 1976 UCS chromaticity diagram.
> [ISO 9241-391]
>
> The chromaticity difference is calculated as:
>
>     SQRT( (u'1 - u'2)^2 + (v'1 - v'2)^2 )
>
> where u'1 and v'1 are chromaticity coordinates of State 1 and u'2 and v'2 are chromaticity
> coordinates of State 2. The 1976 UCS chromaticity coordinates of u' and v' are calculated as:
>
>     u' = 4 * X / (X + 15 * Y + 3 * Z)
>     v' = 9 * Y / (X + 15 * Y + 3 * Z)
>
> where X, Y, and Z are the tristimulus values of a color in the CIE XYZ colorspace, which can
> be calculated as:
>
>     X = 0.4124564 * R + 0.3575761 * G + 0.1804375 * B
>     Y = 0.2126729 * R + 0.7151522 * G + 0.0721750 * B
>     Z = 0.0193339 * R + 0.1191920 * G + 0.9503041 * B
>
> where R, G, & B are values that range from 0-1 as specified in "relative luminance"
> definition.

This settles a question the normative glossary leaves open. The R, G and B in both
`R/(R + G + B)` and the XYZ matrix are the **linear-light** values produced by the relative
luminance definition in section 3, not the gamma encoded values. flashmap follows that.

ISO 9241-391 itself is behind a paywall and we have not read it. Everything flashmap uses from
it is the wording quoted above, which the W3C reproduces.

Verified quote on the size of the 10 degree field and what to analyse:

> In WCAG 2.0, a 1024 x 768 screen was used as the reference screen resolution for the
> evaluation. The 341 x 256 pixel block represents a 10 degree viewport at a typical viewing
> distance. (The 10 degree field is taken from the original specifications and represents the
> central vision portion of the eye, where people are most susceptible to photo stimuli.)
>
> With the proliferation of devices of varying screen sizes (from small handhelds to large
> living room displays), as well as the adoption of CSS pixels as a density-independent unit of
> measurement, the prior assessment criteria may seem outdated. However, an image of a
> consistent size uses up relatively the same percentage of a user's visual field on any device.
> On a large screen, the image takes up less size, but the large screen takes up a larger part
> of the visual field. On a mobile screen, the image may take up most or all of the screen;
> however, the mobile screen itself takes up a smaller portion of the user's visual field. So
> the same dimension of the flashing content, represented in CSS pixels can still provide a
> consistent means of assessment.
>
> Content should be analyzed at the largest scale at which a user may view the content, and at
> the standard zoom level of the user agent. For example, with a video that may play in an area
> of a web page and also at full screen, the video should be analyzed for risks at full screen.

This is why the WCAG area window in flashmap is a **fraction of the picture** (341/1024 of the
width by 256/768 of the height, both very close to one third) rather than a fixed pixel count.
It is also why flashmap measures on the picture and not on a scaled-down box inside a page.

Verified quote on other colour spaces:

> Where video content is provided in color spaces other than sRGB, the version provided with
> the highest dynamic range should be tested. In such cases the industry standard definition of
> a general flash is a change in luminance of 20 cd/m2 or more where the darker image is below
> 160 cd/m2. (ITU-R BT.1702.) This is applicable for standard dynamic range (SDR) and high
> dynamic range (HDR) content. For HDR content when the darker state is 160 cd/m2 or more, a
> general flash is one where the Michelson contrast is 1/17 or greater - where the Michelson
> contrast is calculated as (LHigh - LLow) / (LHigh + LLow), and where LHigh and LLow are the
> luminance of the high and low luminance states, respectively.

---

## 5. ITU-R BT.1702-3, the broadcast profile (SDR only)

Source: Recommendation ITU-R BT.1702-3 (11/2023), "Guidance for the reduction of
photosensitive epileptic seizures caused by television". The full PDF is a free download from
the ITU.
URL: https://www.itu.int/rec/R-REC-BT.1702/en
PDF: https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1702-3-202311-I!!PDF-E.pdf

Verified quote, Annex 1, Guideline 1:

> A potentially harmful flash occurs when there is a pair of opposing changes in luminance
> (i.e. an increase in luminance followed by a decrease, or a decrease followed by an increase)
> as detailed below:
>
> - When screen luminance of the darker image is below 160 cd/m2, a potentially harmful
>   sequence of flashes occurs where there is a difference of 20 cd/m2 or more between the
>   screen luminance of the darker and the brighter images (see Notes 2 and 3). This is
>   applicable for both standard dynamic range (SDR) and high dynamic range (HDR) programmes.
> - When screen luminance of the darker image is not less than 160 cd/m2, a potentially harmful
>   sequence of flashes occurs where there is a difference of more than 1/17 Michelson contrast
>   (see Note 6). For the purpose of this measurement, the Michelson contrast is defined as
>   (LHIGH - LLOW)/(LHIGH + LLOW) [11], where LLOW is the luminance of darker image and LHIGH is
>   the luminance of brighter image of a flash. This is applicable for HDR programmes only.
>
> Irrespective of luminance, a transition to or from a saturated red is also potentially
> harmful.
>
> Isolated single, double, or triple flashes are acceptable, but a sequence of flashes is not
> permitted when both the following occur:
>
> - the combined area of flashes occurring concurrently occupies more than 25% of the displayed
>   (see Note 4) screen area; and
> - there are more than three flashes (i.e. six changes in luminance as described above) within
>   any one-second period. For clarification, successive flashes for which the leading edges are
>   separated by 360 ms or more are acceptable in a 50 Hz environment or separated by 334 ms or
>   more are acceptable in a 60 Hz environment, irrespective of their brightness or screen area.

Verified quote, Annex 1, Note 3:

> NOTE 3 - For the purpose of measurements to check compliance with these guidelines by
> assuming a relationship between video signal level and screen luminance, SDR pictures are
> assumed to be displayed with peak white corresponding to a screen luminance of 200 cd/m2 and
> HDR pictures with Hybrid Log-Gamma (HLG) format are assumed to be displayed with peak white
> corresponding to a screen luminance of 1 000 cd/m2.

Verified quote, Annex 2, note to Table 1:

> Note to Table 1: Video signal level normalized, black at V = 0, to white at V = 1
> (Rec. ITU-R BT.1886). For content mastered per Rec. ITU-R BT.709 10-bit digital code values
> (D) map to V as per the following equation: V = (D-64)/876.

Numbers taken from this quote and used in the `broadcast` profile:

| Number | Meaning | Where it is used |
| --- | --- | --- |
| 20 cd/m2 | the luminance difference that makes a flash, when the darker image is below 160 cd/m2 | `profiles.BROADCAST_SDR.general.min_nits_delta` |
| 160 cd/m2 | the darker image ceiling for the absolute difference rule | `profiles.BROADCAST_SDR.general.dark_image_below_nits` |
| 200 cd/m2 | assumed SDR peak white | `profiles.BROADCAST_SDR.peak_nits` default, overridable with `--peak-nits` |
| 0.25 | 25% of the displayed screen area | `profiles.BROADCAST_SDR.area_fraction_limit` |
| 3 flashes | more than three flashes in any one-second period | `profiles.BROADCAST_SDR.flash_limit_per_second` |
| 2.4 | the exponent of the signal-to-luminance curve, see below | `color.bt1886_nits` |

The 2.4 exponent is not printed in BT.1702-3. It is the BT.1886 reference decoding function
with zero black level, and the recommendation points at BT.1886 for the mapping. We treat the
published Table 1 as the primary evidence for it: `tests/test_bt1702_table.py` asserts that
`200 * V ** 2.4`, with V taken from the printed 10-bit code value as V = (D - 64) / 876,
reproduces all 45 SDR rows of Table 1 to within 0.005 cd/m2, which is the rounding of the two
decimal places the table prints. The measured worst case is 0.005 cd/m2, at code value 880. If
that test ever fails, the exponent is wrong and the profile must not ship. The full table is
transcribed into the test file so the check runs offline.

**Not implemented from BT.1702-3, on purpose:**

- The HDR branch (darker image at or above 160 cd/m2, Michelson contrast 1/17). flashmap is
  SDR only. HLG and PQ inputs are refused rather than analysed with the SDR curve.
- The 360 ms / 334 ms leading-edge allowance. It can only ever excuse flashes that the
  three-per-second rule already flagged, so leaving it out keeps the analyser stricter.
- The overscan allowance in Note 4 (3.5% to 1% of picture width or height).
- Any persistence time, stripe width or spatial frequency band for Guideline 2. BT.1702-3 gives
  none, so none is used as a threshold. See section 8 and implementation decision 9.

**Guideline 2, potentially harmful regular patterns, IS implemented**, in the broadcast profile
only, from the numbers in Attachment 1 to Annex 1. That attachment is informative, so section 8
below carries its quote, its status and the consequences of that status, and the sidecar carries
the attribution beside every pattern segment. Until 2026-09-17 this list said Guideline 2 was
not implemented. It is, so it is not on the list any more.

---

## 6. ITU-R BT.709-6 and ITU-R BT.601-7: which matrix an untagged stream gets

Sources, both free downloads from the ITU:

- Recommendation ITU-R BT.709-6 (06/2015), "Parameter values for the HDTV standards for
  production and international programme exchange".
  https://www.itu.int/rec/R-REC-BT.709/en
  https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.709-6-201506-I!!PDF-E.pdf
- Recommendation ITU-R BT.601-7 (03/2011), "Studio encoding parameters of digital television
  for standard 4:3 and wide-screen 16:9 aspect ratios".
  https://www.itu.int/rec/R-REC-BT.601/en
  https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.601-7-201103-I!!PDF-E.pdf

Verified quote, BT.709-6 Scope and picture characteristics:

> This Recommendation defines the image format parameters and values for HDTV.
> ...
> 2.2 Samples per active line 1 920
> 2.4 Active lines per picture 1 080

Verified quote, BT.601-7 Scope:

> This Recommendation also covers the pixel characteristics that represent a 525- or 625-line
> interlace digital television image.

Verified quote, BT.601-7 Table 1 (the luma coefficients):

> Red 1.0 0 0 0.299
> Green 0 1.0 0 0.587
> Blue 0 0 1.0 0.114

**Not verified: the line count at which an untagged stream switches from BT.601 to BT.709.**
Neither recommendation states a cutoff, because neither is written to cover untagged files.
BT.709 is written for 1080 and 720 line HDTV and BT.601 for 525 and 625 line SDTV, and that
scope difference is the whole of the argument. flashmap uses a picture height of 720 lines or
more as the dividing line. That is our convention, not a threshold from a spec. It is
configurable through `decode.ColorPolicy.hd_min_height` and the choice is recorded in every
sidecar as `color.matrix_source` (`inferred-hd-bt709` or `inferred-sd-bt601`), so a reader can
always see when it was guessed rather than read from the file.

flashmap never multiplies these matrices itself. It hands the inferred matrix and range to
libswscale through PyAV and lets FFmpeg do the conversion, so the coefficients in use are
FFmpeg's, not ours.

---

## 7. Full range pixel formats (yuvj)

Source: FFmpeg, `libavutil/pixfmt.h`, release branch n8.1 (the ffmpeg on this machine is
8.1.2). FFmpeg is the decoder, so its own source is the primary source for what it does.
URL: https://github.com/FFmpeg/FFmpeg/blob/n8.1/libavutil/pixfmt.h

Verified quote:

>     AV_PIX_FMT_YUVJ420P,  ///< planar YUV 4:2:0, 12bpp, full scale (JPEG), deprecated in favor of AV_PIX_FMT_YUV420P and setting color_range
>     AV_PIX_FMT_YUVJ422P,  ///< planar YUV 4:2:2, 16bpp, full scale (JPEG), deprecated in favor of AV_PIX_FMT_YUV422P and setting color_range
>     AV_PIX_FMT_YUVJ444P,  ///< planar YUV 4:4:4, 24bpp, full scale (JPEG), deprecated in favor of AV_PIX_FMT_YUV444P and setting color_range

Verified quote, the two ranges:

>     /**
>      * Narrow or limited range content.
>      *
>      * - For luma planes:
>      *
>      *       (219 * E + 16) * 2^(n-8)
>      *
>      *   F.ex. the range of 16-235 for 8 bits
>      *
>      * - For chroma planes:
>      *
>      *       (224 * E + 128) * 2^(n-8)
>      *
>      *   F.ex. the range of 16-240 for 8 bits
>      */
>     AVCOL_RANGE_MPEG        = 1,

Used for: a `yuvj*` pixel format is treated as full range, whatever the range tag says, and the
sidecar records `color.range_source = "pixel-format-yuvj"`.

**Not verified: what range an untagged, non-yuvj stream should get.** No primary document says.
flashmap assumes limited range, which is what FFmpeg's own converters assume for video, and
records `color.range_source = "default-limited"` so the guess is visible.

---

## 8. ITU-R BT.1702-3, Guideline 2 and Attachment 1 to Annex 1: regular patterns

Source, URL and PDF as in section 5, the same document. Read on 2026-09-17 from the PDF, SHA-256
`9d1167de5553a82c633020a44b5f729118e90ff6536a3b519f1813e235437bf2`. Revision checked the same
day: BT.1702-3 (11/2023) is in force; BT.1702-2, -1 and -0 are superseded.

Two conventions in the quotes below, so the repo style rule and the quote can both be kept:
the ITU prints its bullet markers as dashes and CLAUDE.md forbids en dashes anywhere here, so
the bullets appear as `-`; and whitespace is normalised from the PDF text layer, which inserts
stray spaces inside words. No word, no punctuation and no number is changed.

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

Guideline 2 itself carries no stripe count, no area and no contrast. It defines the hazard and
puts every number in Attachment 1.

### 8.1 Attachment 1 to Annex 1, and what "informative" costs us

**Verified as text. Informative in status.** The quote is exact and from the primary document,
so it meets the bar on this page for a number flashmap may use. What it is not is a requirement:
the ITU marks the attachment `(informative)` and its first sentence says the criteria are used
by some administrations, not by all. So everything flashmap reports from it says where it came
from, in `profile.pattern_rule_source` and on every pattern segment, and nothing reported from
it is presented as a requirement.

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

Numbers taken from this quote and used in the `broadcast` profile:

| Number | Meaning | Where it is used |
| --- | --- | --- |
| more than 5 | light and dark pairs of clearly discernible stripes, printed as "more than five", so six pairs, which is twelve bars, is the first count that can fail | `profiles.BROADCAST_SDR.pattern.more_than_pairs` |
| 0.40 | more than 40% of the displayed screen area, when the stripes are stationary | `profiles.BROADCAST_SDR.pattern.stationary_area_limit` |
| 0.25 | more than 25% of the displayed screen area, when the stripes change direction, oscillate, flash or reverse in contrast | `profiles.BROADCAST_SDR.pattern.changing_area_limit` |

The bar to bar difference is **not a new number**. The attachment defines it by reference to
Guideline 1, so the pattern rule reads the profile's own general flash rule: for SDR that is a
darker bar below 160 cd/m2 and a difference of 20 cd/m2 or more, through the same peak white of
200 cd/m2 and the same BT.1886 curve as section 5. `pattern.py` is handed `profile.general`
and introduces no luminance constant of its own.

Three things the quote settles:

1. the stripe count and the area are one test: the count is a gate and then either area
   condition can trip it;
2. the contrast condition is separate and additional;
3. the static and moving cases differ only in the area limit, 40% against 25%. Nothing in the
   quote gives a duration, a persistence time, a stripe width or a spatial frequency.

On area: BT.1702-3 Note 4 explains "displayed" for Guideline 1 as allowing for overscan of 3.5%
to 1% of picture width or height. Attachment 1 says "displayed screen area" without repeating
the note. flashmap measures the pattern on the picture after letterbox and pillarbox removal
(implementation decision 5) and does not implement the overscan allowance, which makes it
stricter. The pattern rule measures the same way, for the same reason.

### 8.2 WCAG 2.2 does not cover regular patterns at all

**Verified, and it is a negative result worth writing down.**

Source: Understanding Success Criterion 2.3.1: Three Flashes or Below Threshold, W3C, read
2026-09-17. URL: https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html

Every occurrence of the word "pattern" in SC 2.3.1 and its Understanding document is the same
exemption, quoted in full in section 2 of this file: the fine, balanced pattern such as white
noise or a checkerboard under 0.1 degree. The word "stripe" does not occur. There is no WCAG
requirement about stripe counts, static patterns, pattern area or pattern contrast, and the one
pattern sentence WCAG has lets content off rather than catching it.

Consequences, and they are firm:

- the pattern rule is not a WCAG rule. It is absent from the `wcag` profile, it never changes a
  WCAG pass or fail, and it must never be described as WCAG conformance in the README, the
  Devpost text or the video. The map carries `summary.flash_pass` for the WCAG reading and
  `summary.pattern_pass` beside it, and every pattern segment carries
  `"is_a_wcag_finding": false`;
- the house line that room settings can only make things stricter than WCAG is unaffected. A
  pattern hide is strictly extra.

### 8.3 Sources that could not be read, and vendor claims that are not sources

- **Ofcom's guidance note on flashing images and regular patterns.** Every ofcom.org.uk URL
  tried on 2026-09-17 answered HTTP 403 behind a Cloudflare interstitial, to a plain fetch and
  to curl with a desktop user agent alike, and no browser was connected to that session. **No
  number is taken from Ofcom and nothing in the code cites Ofcom.** Worth retrying from a
  machine with a browser: Ofcom's wording states the contrast condition as its own clause that
  must apply in addition to the area condition, where the ITU attachment states it as a
  sentence, and the two read the same way.
- **HardingFPA** is a commercial analyser. Its pages are marketing and product support for a
  closed implementation, not a published threshold, so under CLAUDE.md they cannot supply a
  number. In particular the claim that a pattern must stay stationary for about half a second
  before it fails appears only on vendor and third party pages. No primary document read here
  contains a persistence time for patterns, so flashmap has none.
- **The Japanese NAB and ARIB guidance**, which BT.1702-3 alludes to as regional variation. No
  primary English copy read. Not used.
- **ISO 9241-391**, still behind a paywall, as recorded in section 4.

---

## Implementation decisions where the specs are silent

These are not thresholds. They are choices flashmap had to make to turn the wording above into
code. Each one is named in the sidecar so that a consumer can see the reading that was used.

1. **How transitions are paired into flashes.** WCAG says "A flash consists of two opposing
   transitions" but does not say whether a run of alternating transitions yields overlapping or
   non-overlapping pairs. flashmap pairs them non-overlapping, so a square wave at 5 Hz counts
   as 5 flashes per second and not 9. This matches the plain reading of "flashes more than
   three times in any one second period". Sidecar field: `profile.transition_pairing`.

2. **When a transition is declared.** WCAG defines a transition between "adjacent peaks and
   valleys". A causal analyser cannot know a peak is a peak until the signal turns around.
   flashmap declares a transition on the first frame at which the swing away from the previous
   confirmed extreme meets the threshold, and then makes that value the new anchor. On a slow
   ramp this produces several same-direction transitions, which never pair into a flash, so a
   ramp does not count as flashing. Sidecar field: `profile.transition_rule`.

3. **Where the one-second window is placed.** flashmap evaluates the trailing window
   [t - 1000 ms, t] at every frame timestamp t. If four flashes fall inside any one-second
   period then they also fall inside the trailing window that ends at the fourth of them, so
   the family of trailing windows is complete. Sidecar field: `profile.window_placement`.

4. **What "opposing" means for red.** WCAG gives no sign for a colour transition. flashmap
   calls a transition into the saturated red state and a transition out of it opposing, which
   makes a red flash one entry plus one exit, both of which must move more than 0.2 in the
   CIE 1976 UCS diagram. Sidecar field: `profile.red_opposing_rule`.

5. **Where the flashing area is measured.** On the picture, after letterbox and pillarbox bars
   are removed, never on the coded frame. Bars are not part of the picture and counting them
   would shrink every area fraction. Every sidecar carries `picture.measured_on: "picture"` and
   the bar geometry that was removed.

6. **The bar detector's own numbers** (how dark a row has to be to count as a bar, how uniform
   it has to be, how many frames are sampled) are detector tuning, not thresholds from a spec.
   They live in `picture.LetterboxSettings` with their defaults written out, and the detected
   geometry is in the sidecar so a reviewer can check it by eye.

7. **Analysis resolution.** Frames are scaled to a working width before analysis, which is a
   speed choice. Area fractions are ratios so they survive scaling. The size used is recorded
   in `color.analysis_width` and `color.analysis_height`.

8. **The room window is geometry, not a threshold.** A 10 degree field at a seat distance d
   subtends 2 * d * tan(5 degrees). The 10 degrees is WCAG's, from section 2. The trigonometry
   is not a number that needs a source.

9. **How stripes are counted, and how the motion class is decided.** Attachment 1 says "clearly
   discernible stripes in any orientation" and nothing more, so the detector had to be built
   out of choices rather than numbers. Each one is in `pattern.PatternSettings` with its
   default written out, and the whole block is in the sidecar under
   `profile.pattern_rule.tuning`, the same way the bar detector's numbers are under decision 6.
   None of them is a threshold:

   - stripes are counted along four scan families, rows, columns and the two diagonal shears,
     because the attachment allows any orientation and allows radial, curved and dotted
     patterns. A bar boundary is a swing that reaches the Guideline 1 flash difference with the
     darker level under the Guideline 1 darker image limit, read across the picture instead of
     across time, and only boundaries that oppose the one before them count, so a gradient
     across the screen counts no bars however far it travels. Twelve bars is six pairs;
   - the pattern area is the union of the stretches of those scanlines that lie between their
     outer bar boundaries, as a fraction of the picture;
   - motion is measured on the one dimensional stripe profile of the orientation that counted
     the most bars, not on the picture, because a grating can only be seen to move along its
     own normal. A shift is a whole pixel lag found by normalised cross correlation, searched
     out to just under one bar width. A pattern that travels a whole bar between two frames
     lands on top of itself, so the measurement is reported ambiguous rather than guessed at;
   - **the smooth flow exemption fails safe.** It is applied only when the flow is unambiguous:
     a full history of frame to frame comparisons, all in one direction, none still, none
     ambiguous, none below the match floor. Anything short of that is `uncertain`, and
     `uncertain` takes the 25% area, never the 40% one, and never the exemption. The cost is
     that a pattern between the two area limits is hidden for the first few frames, while the
     detector is still filling its history, and that a fine pattern flowing fast enough to
     alias is hidden rather than exempted. Every exemption that is applied is written into the
     map as its own interval in `pattern_exemptions`, so a reviewer sees what was let through
     instead of finding a silence. docs/DECISIONS.md carries the reasoning.

   There is no persistence time, no stripe width and no spatial frequency band in this list,
   because BT.1702-3 gives none and a vendor page is not a source (section 8.3).

---

## One thing worth knowing about the two red numbers

The red flash test has two thresholds: R/(R + G + B) at or above 0.8, and a move of more than
0.2 in the CIE 1976 UCS diagram. Against a neutral background they overlap heavily. Measured
over the whole sRGB cube, the furthest any colour with a red ratio between 0.5 and 0.78 can get
from mid gray in that diagram is about 0.19, which is under the 0.2 limit. So for flashing
between gray and a colour, lowering the ratio threshold anywhere down to roughly 0.45 changes
nothing: the distance rule stops it first.

That is not a criticism of the spec. It matters for two practical reasons:

- A consumer reading `profile.red_flash` should not assume the ratio alone decides anything.
- A test on a generated clip cannot separate the two numbers, so flashmap pins them at unit
  level instead, in `tests/test_flash_tracker.py`. The geometry above is asserted there too, in
  `test_the_two_red_thresholds_overlap_against_a_neutral_background`, so the claim on this page
  is checked rather than believed.

---

## Things we deliberately did not use

- Any HDR rule. BT.1702-3's HDR branch and BT.2100 are out of scope for version 1. HLG and PQ
  tagged inputs are refused with a clear error rather than measured with the SDR curve.
- The Harding FPA parameters, the Ofcom guidance note and the Japanese NAB/ARIB guidance. We
  could not read a primary copy of any of them, so no number from them appears in the code.
- Any per-frame "risk score" or 0 to 100 scale. Nothing in either spec defines one.
