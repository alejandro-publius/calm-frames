# Approved TV design implementation

## October 10 cloud polish

The current source adds a more prominent Harbor illustration, taller library
cards, quieter secondary navigation, a clearer viewing settings panel, and
more consistent setup and parental controls layouts and copy. This changes
app inputs after the earlier native build. It has not been packaged, installed
or observed on Vega in this cloud session.

See [POLISH_REVIEW.md](POLISH_REVIEW.md) and
[`design_polish_2026-10-10.json`](../../results/design_polish_2026-10-10.json)
for the current changes and cloud evidence. Rebuild on the Mac, check D-pad
focus, scrolling, saved settings and playback in the Vega Virtual Device,
then record the changed screens and refresh the demo and review assets.
The earlier native receipt remains valid for its recorded package and cannot
be used as native evidence for this polish.

`app/assets/image/tv/harbor.png` was generated with imagegen on October 10 from
the prior Harbor illustration. The supplied output is a 1942 x 809 PNG used
only for library and details presentation. It is neither a frame from the
film nor a signed hold image. The polish receipt records its exact hash.

## Earlier native implementation

The October 10 user-provided archive was found in Documents. Its briefs and
starting tokens are preserved here. The HTML is a reference, not native evidence.

The earlier native design used the supplied Harbor and gradient SVG illustrations
as presentation artwork. The gradient still uses that source; the current Harbor
PNG is described above. Neither is substituted for signed playback hold images.
The Harbor synopsis comes from the existing story captions: a boat in the harbor
on its way home. Catalog identity, verification, rendition selection and holds
remain independent of the display names and art.

## Fonts

The running Vega image exposes Amazon Ember regular and medium, but no semibold
face (`fc-list` and `fc-match`). Licensed Inter from the archive is instantiated
at weights 400, 500 and 600, optical size 24, into static TrueType files. Each face
has its own family and matching filename, and is used at normal weight to avoid
synthetic emboldening. The SIL Open Font License is included beside the files.

Vega loads these custom faces from `app/assets/fonts`, not `assets/raw/fonts`.
This was checked in two native builds: the first used the wrong directory and
showed fallback regular text; the second uses the documented directory and shows
the distinct medium and semibold faces. The same `fontFamily` strings were used
in both builds. Native before/after captures are under `.logs/redesign-first-`
and `.logs/redesign-second-`. Final package and captures are recorded separately.
Amazon documents the matching family/filename convention in its
[Text Style Props reference](https://developer.amazon.com/docs/react-native-vega/0.72/text-style-props).
No Amazon font files are redistributed.

Shared `CALM_TEXT` styles define face, size and line height. All supporting text
retains the 32-unit floor, with six-unit reserved focus outlines. New art is
included in image checks; the final native recording is analyzed separately
because the palette simulation does not inspect image pixels or native layout.

## Earlier native validation

The first native render exposed oversized hero artwork despite a passing type
check. Explicit image heights correct it. Native parent controls, PIN correction, settings persistence, full-plan scrolling,
remote transport and playback have been exercised. The final receipt is
`results/redesign_validation_2026-10-10.json`; it distinguishes intermediate
observations from final-package captures.

The independent Ultracode review prompted removal of repeated schedule copy
and focused text underlines alongside stable six-unit outlines. Native validation
then exposed settings losing focus during saves. The deferred-write regression
failed before the fix; controls now retain focus while blocked handlers prevent
repeat writes. The unavailable badge says "Needs check", without claiming that
analysis is running. No detection, signature or timing threshold was changed.


The final all-screen comparison is `build/submission-redesign/native-screen-review.png`.
Its source hashes and intermediate/final scope are in the native receipt.
It caught a repeated unavailable-title explanation. The last one-sentence fix
now renders that reason once; 85 affected tests, type checking, rebuild/install,
PIN unlock, native unavailable-title display, loading Back/replay and cold launch
were rerun. The demo's playback scenes are from the preceding otherwise
identical build, explicitly identified by hash rather than relabelled as final.
