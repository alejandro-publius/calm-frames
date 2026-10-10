# Approved TV design implementation

The October 10 user-provided archive was found in Documents. Its briefs and
starting tokens are preserved here. The HTML is a reference, not native evidence.

The native design uses the supplied Harbor and gradient SVG illustrations as
presentation artwork. They are never substituted for signed playback hold images.
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

## Validation in progress

The first native render exposed oversized hero artwork despite a passing type
check. Explicit image heights correct it. The final parent screens, full native
journey, recording and exact commit receipt are still being completed.
