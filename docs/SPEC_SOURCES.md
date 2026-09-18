# SPEC_SOURCES

The threshold sources live with the analyser that uses them, at
[`flashmap/docs/SPEC_SOURCES.md`](../flashmap/docs/SPEC_SOURCES.md). That file is the only
place a threshold may come from, as CLAUDE.md says, and it ships inside the Apache-2.0 flashmap
package so a studio using the analyser on its own still has the quoted text and the links.

This page exists so that anyone who looks for `docs/SPEC_SOURCES.md` lands in the right place.
It repeats no number that flashmap already uses, because two copies of a threshold is one copy
too many.

There is no exception and there is nothing else on this page. The regular-pattern research
that used to sit below was for a rule that did not exist yet. That rule is built, so its quotes
moved into `flashmap/docs/SPEC_SOURCES.md` section 8 on 2026-09-17, where the code can read
them, and this section is the pointer it always said it would shrink to.

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
6. ITU-R BT.1702-3, Guideline 2 and Attachment 1 to Annex 1, for the regular-pattern rule in
   the broadcast profile, with the attachment's informative status and the fact that WCAG 2.2
   SC 2.3.1 does not cover regular patterns at all.
7. ITU-R BT.709-6 and ITU-R BT.601-7, for which matrix an untagged stream should get.
8. FFmpeg's `libavutil/pixfmt.h`, for what a `yuvj` pixel format means.

## What could not be verified

Four things, all named in that file and none of them used as a threshold:

- **The line count at which an untagged stream switches from BT.601 to BT.709.** No spec states
  one. flashmap uses 720 lines as a project convention, records the guess in every map as
  `color.matrix_source`, and lets it be overridden.
- **What range an untagged non-yuvj stream should get.** No primary document says. flashmap
  assumes limited range and records `color.range_source: "default-limited"`.
- **Ofcom's guidance note on flashing images and regular patterns.** Every ofcom.org.uk URL
  answered HTTP 403 behind a Cloudflare interstitial on 2026-09-17, with no browser connected
  to that session. Nothing in this repository cites Ofcom, and no number comes from it. Worth
  retrying from a machine with a browser.
- **ISO 9241-391 itself**, which is behind a paywall. Everything flashmap uses from it is the
  working definition that the W3C reproduces in WCAG 2.2 and its Understanding document, quoted
  in full.

ITU-R BT.1702-3 was fetched in full from the ITU, so the broadcast profile is grounded. Its HDR
branch is not implemented and flashmap refuses HLG and PQ input rather than measuring it with
the SDR curve.
