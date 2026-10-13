# Calm Frames design

This is the one page to read before designing anything for Calm Frames. It
describes the interface the code draws today. The source of truth is
[`app/src/calmframes/calmStyles.ts`](../../app/src/calmframes/calmStyles.ts):
the palette, type, spacing and focus values below are copied from it, and
[`eval/tests/test_design_page.py`](../../eval/tests/test_design_page.py) fails
if this page, [`tokens.json`](tokens.json) and the code stop agreeing, or if a
contrast ratio on this page is not the one the colours give.

The other files in this folder are the record of how the design got here: the
Oct 10 [brief](IMPLEMENTATION_BRIEF.md) (a proposal written before the
redesign was built; its second teal `#12343F` never shipped), the
[native implementation notes](NATIVE_IMPLEMENTATION.md), the
[polish review](POLISH_REVIEW.md) and the [seamless review](SEAMLESS_REVIEW.md).
Where one of them and this page differ, this page and the code are current.

## Identity

A peaceful monk inside a rounded frame, with one open halo. Deep teal ground,
cream face and text, saffron robe. The mark is still: no pulsing, no animated
halo. The files, sizes and store requirements are in
[`docs/brand/README.md`](../brand/README.md).

The brand line is **A calmer way to watch**. It describes how watching feels.
It is not a clinical claim or a detection guarantee. When the product says what
it does for safety, it uses the approved sentence and no other: "reduces
exposure to flashing above published limits in the videos it plays; not a
medical device."

## Principles

| Principle | What it means on screen |
|---|---|
| Calm | One clear primary action per screen. Secondary navigation is quiet. Sentence case, short lines, no badges or borders competing with the content. |
| Still by default | Nothing moves unless a parent turns on Gentle artwork motion, and then only artwork, once. Text, focus rings, controls, setup and covers never move. Apart from that one entrance, nothing fades, slides or pulses. |
| Nothing flashes | The interface's own frames are run through flashmap under both the WCAG and broadcast profiles (`cd app && npm run ui:flashmap`), and a negative control (`node tools/ui_flashmap.mjs --negative-control`) shows that the check refuses a flashing sequence and a grating. |
| The cover is never decorative | The cover is a safety surface. It is opaque black, or a checked still signed for that title, and red segments always get an opaque cover. Dim mode exists only for non-red segments at 90% or darker. The cover is never used as a transition, a theme, a mood or a background, and presentation artwork is never used as a cover or a hold still. |
| Truthful | No invented ratings, durations, progress or watch history to fill a small library. Practice holds are always labelled as practice. |

## Palette

Thirteen colours, all in `CALM_COLORS`. The `tokens.json` key is the same name
in camelCase.

| Token | tokens.json | Hex | Use |
|---|---|---|---|
| `BACKGROUND` | `background` | `#102F3A` | The ground every screen sits on, and the listing tile ground. |
| `SURFACE` | `surface` | `#1A414B` | Cards, settings rows, resting buttons, notices, badges, the player card and the practice plate. |
| `SURFACE_FOCUSED` | `surfaceFocused` | `#234B55` | The fill of a focused or chosen control, and the quieter edge of an unavailable button. |
| `BORDER` | `border` | `#66A0B4` | Thin edges on cards and the flash map strip, dividers, and the bar on a calm notice. Never text. |
| `FOCUS_RING` | `focusRing` | `#E6A957` | Saffron. The focus ring, the primary action's fill, and the short label above a featured title. |
| `ACCENT_DARK` | `accentDark` | `#B87A2C` | Dark saffron. Edges and fills only, never text. Today only the fold line on the robe in the mark draws it; the flashmap report declares it as a stylesheet variable but draws nothing with it, and no app screen draws it. |
| `TEXT` | `text` | `#F3E8D3` | Cream. Titles, headings, body text and control labels. |
| `TEXT_DIM` | `textDim` | `#BDD0CF` | Supporting text: descriptions, helper lines, shelf qualifiers, the step counter, unavailable labels. |
| `INK` | `ink` | `#17323C` | Text on saffron, and the fill of the focused primary action. |
| `VERIFIED` | `verified` | `#7FD1A3` | The Ready to watch badge. |
| `PENDING` | `pending` | `#E2C275` | The Preparing badge, the bar on a waiting notice, and the non-red marks on the flash map strip in title details. |
| `FAILED` | `failed` | `#F2BDB1` | The Unavailable badge, the bar on a blocked notice, and the red marks on the flash map strip. |
| `COVER` | `cover` | `#000000` | The cover. `CoverLayer.tsx` paints the same `#000000` itself. |

## Contrast

Contrast is the WCAG 2.2 contrast ratio, (L1 + 0.05) / (L2 + 0.05), over
relative luminance. [`flashmap/docs/SPEC_SOURCES.md`](../../flashmap/docs/SPEC_SOURCES.md)
section 3 quotes the relative luminance half; the ratio formula and the two
floors below are the app's own constants. WCAG 2.2's contrast ratio definition,
SC 1.4.3 and SC 1.4.11 still have to be quoted here with links: the Oct 11 cloud
box could not reach w3.org, and they are not quoted from memory. The app's own arithmetic in `app/src/calmframes/uiContrast.ts` uses
the older 0.03928 break point that WCAG's Note 2 mentions; for 8-bit colours
the two give the same answer, because no value n/255 falls between 0.03928 and
0.04045. Ratios here are truncated to two decimals, the way `roundRatio` in
`uiContrast.ts` truncates them, so a ratio is never rounded up past a floor.

The floors are the code's: `MINIMUM_TEXT_CONTRAST` is 4.5 to 1 for every line
of text and `MINIMUM_FOCUS_CONTRAST` is 3 to 1 for the focus ring against both
of its neighbours. All Calm Frames text is large text by WCAG's definition,
where AA asks only 3 to 1, so holding it to 4.5 is stricter than the rule on
purpose: a television is read from across a room.

### Text on background

Every pair Calm Frames draws text in.

| Text | On | Ratio | Where |
|---|---|---|---|
| `TEXT` | `BACKGROUND` | 11.60 | Headings, titles, body text and quiet navigation on the ground. |
| `TEXT` | `SURFACE` | 9.09 | Button labels at rest, settings rows, notices, the player card. |
| `TEXT` | `SURFACE_FOCUSED` | 7.82 | Labels on a focused or chosen control. |
| `TEXT_DIM` | `BACKGROUND` | 8.78 | Synopsis, shelf qualifiers, the step counter, the brand line in setup. |
| `TEXT_DIM` | `SURFACE` | 6.88 | Helper text in rows and cards, the practice plate, unavailable button labels. |
| `TEXT_DIM` | `SURFACE_FOCUSED` | 5.92 | Helper text inside a focused or chosen row. The lowest pair. |
| `FOCUS_RING` | `BACKGROUND` | 6.83 | The short label above the featured title, such as "Original story". |
| `INK` | `FOCUS_RING` | 6.53 | The primary action at rest, such as Watch now. |
| `TEXT` | `INK` | 11.10 | The primary action with focus on it. |
| `VERIFIED` | `SURFACE` | 6.07 | The Ready to watch badge. |
| `PENDING` | `SURFACE` | 6.41 | The Preparing badge. |
| `FAILED` | `SURFACE` | 6.67 | The Unavailable badge. |

`ACCENT_DARK`, `BORDER` and `COVER` never carry text. Saffron carries text
only on the dark ground. The ten-foot test,
[`app/test/calmframes/tenFoot.test.tsx`](../../app/test/calmframes/tenFoot.test.tsx),
measures every rendered line against whatever is painted behind it on every
screen and state it renders, so a colour used in the wrong place fails there.
Its fixtures do not reach the saffron label, the focused primary action or the
Needs check badge as text, so those three rows rest on the code and on the
arithmetic here.

Text drawn straight over the moving picture, such as the sample player's own
header in `app/src/w3cmedia`, has no fixed background and is not in this
table. Calm Frames' own words on the player sit on a `SURFACE` card or plate.

### Focus ring

| Ring | Beside | Ratio | Where |
|---|---|---|---|
| `FOCUS_RING` | `SURFACE_FOCUSED` | 4.60 | Inside the ring of a focused control. The lowest pair. |
| `FOCUS_RING` | `INK` | 6.53 | Inside the ring of the focused primary action. |
| `FOCUS_RING` | `BACKGROUND` | 6.83 | Outside the ring, on the ground. |
| `FOCUS_RING` | `SURFACE` | 5.35 | Outside the ring, on a card or group, such as Skip on the player card. |

## Type

Inter, in three static licensed faces bundled in `app/assets/fonts`
(`CALM_FONT`). Each face is its own family and is drawn at `fontWeight` 400,
so the weight comes from the face and nothing is synthetically emboldened. The
running Vega image has Amazon Ember regular and medium but no semibold, which
is why Inter is bundled ([native notes](NATIVE_IMPLEMENTATION.md)). Sizes are
1080p units. The smallest text anywhere is `MINIMUM_TEXT_SIZE`, 32 units.

| Role | Face | Size / line height | Use |
|---|---|---|---|
| `feature` | InterSemiBold | 80 / 92 | The featured title on the library. |
| `screen` | InterSemiBold | 64 / 76 | Screen titles (setup, parental controls, credits, title details) and the PIN pad. |
| `section` | InterSemiBold | 42 / 54 | Section headings in the library, details and settings. |
| `card` | InterMedium | 38 / 48 | Titles beneath artwork, the player card's title, and the day headings in the hidden-parts history. |
| `body` | InterRegular | 36 / 48 | Short explanations and synopses. |
| `control` | InterSemiBold | 36 / 46 | Buttons, rows and the wordmark. |
| `supporting` | InterRegular | 32 / 42 | Qualifiers, helper text, badges and the practice plate. |

Keep text in sentence case. Shorten the words before shrinking the type.
`CALM_TYPE` in the same file holds older size-only tokens; new work uses the
named `CALM_TEXT` styles above.

The cinematic library and details use a larger title treatment within their
hero composition, with smaller variants for long names. Their exact local
sizes remain in `KidHomeScreen.tsx` and `TitleDetailsScreen.tsx`; the shared
type roles above continue to govern the rest of the interface.

## Spacing and layout

The design canvas is 1920 by 1080 units, and `scale()` turns units into dp
(density-independent pixels) for the current screen height, rounded to the
nearest pixel.

| Token | Units | Use |
|---|---|---|
| `TIGHT` | 12 | Between a label and its helper line, and small paddings. |
| `ROW` | 20 | Between rows and neighbouring controls, and a button's vertical padding. |
| `BLOCK` | 32 | Between groups, and a button's horizontal padding. |
| `EDGE` | 64 | Generous separation, such as the player card's side padding. |
| `SAFE_X` | 96 | The left and right safe margin, 5% of 1920. |
| `SAFE_Y` | 54 | The top and bottom safe margin, 5% of 1080. |

Televisions still overscan, by different amounts, so nothing a person reads or
presses goes inside the safe margins. The ten-foot test fails any screen whose
content comes closer. On the player the picture and the cover fill the screen;
the practice plate hangs from the top left corner of the safe area, the card
hangs from the upper part of it (`PLAYER_LAYOUT`), and the bottom band belongs
to captions, which must never be covered by our own words.

Corners are modest: 12 units on controls and rows, 16 on cards and notices, 20
on shelf artwork, 26 on its focusable frame, 10 on badges and 6 on the flash map
strip. The featured scene reaches the right screen edge and blends into the
teal background. Title copy and viewing settings sit directly on that background,
with space, headings and fine dividers doing the grouping. Secondary actions rest directly on the background and gain a visible outline
on focus.

## Focus

- Every focusable control carries a `FOCUS_RING_WIDTH` border, 6 units, whether
  it has focus or not. Focus changes the ring's colour and the fill together,
  so nothing moves or grows when focus moves.
- Focus is never colour alone: the focused label is also underlined.
- The primary action inverts with focus: saffron with ink text at rest, ink
  with cream text and a saffron ring when focused.
- Pressing does not dim a control (`activeOpacity` is 1). An unavailable
  control is not faded either: it keeps its background, takes a quieter edge
  and dim text, and says why in words.
- Each screen gives first focus to its main action (`hasTVPreferredFocus`). A
  countdown card moves focus to Skip with `requestTVFocus`, because a Vega app
  cannot rely on the D-pad to get there.
- Coming back from a title puts focus on the card you left from. Returning to
  a choice prefers the selected control, and controls keep focus while a save
  is pending.

## Motion

There is one movement in the whole interface, and it is off unless a parent
turns it on.

- **What:** library and title-details artwork settles upward into place once
  when the page opens: <!--n results/interface_finish_2026-10-10_pacific.json:behavior.motion.translation_scaled_units -->6<!--/n-->
  units over <!--n results/interface_finish_2026-10-10_pacific.json:behavior.motion.duration_ms -->240<!--/n--> ms, easing out
  ([`CalmArtworkMotion.tsx`](../../app/src/calmframes/CalmArtworkMotion.tsx)).
- **Who turns it on:** a parent, with Gentle artwork motion in Parental
  controls. It is off for new households and for every household saved before
  it existed; only an explicit true in the saved record enables it
  (`newFamily` and `clampFamily` in `profiles.ts`).
- **When it stays still anyway:** whenever the system reduced-motion setting
  is anything other than an explicit "off", including unknown or a failed
  query; when the app is not in the foreground; when lifecycle access fails.
  Leaving, backgrounding or turning it off settles the artwork at rest at
  once, and turning it on later never replays the entrance on a page that is
  already open.
- **What never moves:** text, focus rings, controls, setup, the player card,
  the practice plate and the cover.

The rules are tested in `app/test/calmframes/artworkMotion.test.tsx`. The
movement itself has not been seen on a device.

## Sound

Two sounds, kept separate, and neither replaces the other.

| | Warning chime | Selection sound |
|---|---|---|
| What it says | The picture is about to be hidden. | A menu action was accepted. |
| Sound | Two soft tones a fifth apart with a long fade (`calm-chime.mp3`). | A short, softly attacked tone with a quiet octave (`menu-select.mp3`). |
| Default | On (`CHIME_ON_BY_DEFAULT`). A household switch, "Chime before the picture is hidden", turns it off; that changes nothing about what is hidden. | Off. A parent turns on Selection sounds in Parental controls. |
| When | `CHIME_LEAD_MS`, two seconds, before a cover, while the countdown card is already on screen. | Accepted menu actions and successful settings saves. |
| Never | Without a cover following it: `chimeCue.ts` is a state machine whose count of broken promises is always zero. | On focus movement or Watch actions, during playback, while a screen reader is on or its state is unknown, or while the app is blurred or in the background. |
| Volume | `CHIME_VOLUME`, 0.35. | <!--n results/interface_finish_2026-10-10_pacific.json:behavior.sound.volume -->0.22<!--/n-->, at most one request every <!--n results/interface_finish_2026-10-10_pacific.json:behavior.sound.minimum_request_interval_ms -->220<!--/n--> ms, released after <!--n results/interface_finish_2026-10-10_pacific.json:behavior.sound.timeout_ms -->500<!--/n--> ms if the player never says it ended. |
| Code | `chimeCue.ts`, `useChimeCue.ts`, `chimeSound.ts` | `interfaceSound.ts`, `useInterfaceSound.tsx` |

Both are original sounds generated from sine waves; how to regenerate them is
in [`app/assets/raw/sound/README.md`](../../app/assets/raw/sound/README.md).
Neither has been heard on a device.

## Copy

The voice is in [`COPY_GUIDE.md`](COPY_GUIDE.md). Its core rules:

> Use familiar labels and natural sentences. Keep each message focused on what
> the viewer needs to know or do next.

> Avoid paired slogans, repeated sentence fragments, rhetorical contrasts such
> as “not X, but Y,” decorative descriptions of colors and typography, and
> statements about how carefully the interface was designed.

> Do not invent durations, ratings, progress, availability, plot details, or
> medical claims.

The labels are the familiar TV ones: Watch now, Watch demo, Play, More info,
Your library, Parental controls, Back to library. Screen-reader labels add the
context a short label leaves out, such as "Watch now: Harbor". House style on
top of the guide, and enforced by `app/test/calmframes/copy.test.ts` and
`eval/style_check.py`: no em dashes or en dashes anywhere, no exclamation marks
in notices, and never "prevents seizures" or "seizure-proof".

## Accessibility

| Area | Behaviour |
|---|---|
| D-pad | Every action is reachable with the remote, with one focus treatment everywhere. Back returns to the library; Back while a title is loading returns to its focused Watch button. While a countdown card is up, Skip has focus and owns OK. |
| Screen reader | The player card is a polite live region, and its words are also announced through `AccessibilityInfo` with `queue: true`, so an announcement already in progress finishes first (`announce.ts`). Notices are polite live regions that read their title and detail together. Saving feedback appears in a reserved space beside the title and is announced politely. Headings carry the header role, and the two interface preferences carry the switch role and their checked state. |
| Reduced motion | Honoured as described under Motion. Unknown means still. |
| Sound and screen readers | Selection sounds stay silent while a screen reader is on or its state is unknown, so they never talk over it. |
| Reading | Calm Frames draws no text below 32 units or at less than full opacity, and every text pair clears 4.5 to 1. |

## Renders

### Oct 13: water opening and natural copy

The library calls Harbor an Original story. Browsing and screen-reader labels
no longer announce that every title was checked. Loading, unavailable titles
and parental controls describe what is happening and what the viewer can do.
The playback rules and the safety note are preserved.

The opening fills the screen with a close view of Harbor's water and a small
Calm Frames wordmark. It cuts into the library once startup is complete. When
interface motion is enabled, a single 1.4 second drift precedes that cut;
reduced motion, Back, a background event or a failed preference query settles
it. It never replays on returning from a story. Motion remains off by default.

![Water opening, browser approximation](arrival/opening-browser.png)

![Library with Original story and natural browsing copy, browser approximation](arrival/library-browser.png)

[Opening sequence, browser approximation](arrival/opening-browser.mp4).
These are browser renders of the app's component tree, not a Vega recording.
The actual film shown after Watch now still needs its separate artwork update.

### Earlier open-layout checkpoint

These are Chromium renders of the actual rendered React Native component
trees, with the bundled Inter faces and the real artwork, at 1920 by 1080. The
household, focus and saving states are synthetic inputs. **They are not Vega
screenshots**, and browser text and flex layout can differ from the device.
The current library and details refine the cinematic design from `b882d39`,
which includes Claude's work through `49f3a18`. Their exact source and image
hashes are recorded in [`open_layout_design.json`](../../results/open_layout_design.json).
The large Harbor scene is presentation artwork, not a frame from the film.
Text and actions sit on solid teal; the artwork blends into its edge. The
practice-hold demo retains its earlier illustration, so the two versions are
visually distinct. These stills do not demonstrate the optional entry motion.

![Current library with Harbor artwork reaching the screen edge, open title copy and quiet secondary actions](open/library-browser.png)

![Current Harbor details with an unframed title, panoramic illustration and viewing information](open/details-browser.png)

[Viewing settings after scrolling](open/details-bottom-browser.png).

Earlier review images remain below as historical references:

- `cinematic/` records the earlier framed composition on `b882d39`. Receipt:
  [`cinematic_design_2026-10-11.json`](../../results/cinematic_design_2026-10-11.json).
- `polish/` was rendered from `54dab0b` on Oct 10, before the Oct 11 shelf
  copy. Its shelf says "Scheduled scene holds" and "Original story" where the
  later October 11 code said "Practice holds" and "Checked story". Receipt:
  [`design_polish_2026-10-10.json`](../../results/design_polish_2026-10-10.json).
- `seamless/` was rendered on Oct 11 from the sources committed in `85c30f9`, on
  base `5316051`. It has the shelf copy but
  comes before the motion and sound pass, so its parental controls have no
  Interface group with the two opt-in switches. Receipt:
  [`seamless_design_2026-10-11.json`](../../results/seamless_design_2026-10-11.json).

Where an image and the code differ, the code is current. They are stills, so
none of them shows the artwork motion.

![The library from 85c30f9: the Harbor feature with Watch now focused, and three titles on the shelf](seamless/library-family-browser.png)

*The library, `seamless/`, Oct 11. Watch now has focus: ink fill, saffron
ring, underlined cream label. Browser render, not a Vega screenshot.*

![Title details from 54dab0b: Harbor with Watch now, then Before you watch and the viewing settings panel](polish/details-after.png)

*Title details, `polish/`, Oct 10, before the shelf copy changed "Original
story" to "Checked story". Browser render, not a Vega screenshot.*

![Parental controls from 85c30f9 while a save is pending, with Saving your changes beside the title](seamless/parent-saving-browser.png)

*Parental controls while a save is pending, `seamless/`, Oct 11. The message
sits beside the title so no control moves. Before the Interface group existed.
Browser render, not a Vega screenshot.*

![The setup review step from 85c30f9: Step 4 of 4, your household, and how Calm Frames works](seamless/setup-review-browser.png)

*The last setup step, `seamless/`, Oct 11. Browser render, not a Vega
screenshot.*

The rest: [library before the polish](polish/library-before.png),
[library after it](polish/library-after.png),
[family library](polish/library-family-after.png),
[full viewing settings](polish/details-bottom.png),
[setup](polish/setup-after.png),
[parental controls](polish/parent-after.png),
[lower parental controls](polish/parent-bottom.png),
[parental controls at rest](seamless/parent-idle-browser.png) and
[setup actions after scrolling](seamless/setup-review-bottom-browser.png).

## Limits

What has been seen on the Vega Virtual Device, on Oct 9 and 10, from packages
built at `cba1a29` (the recorded demo) and `73fbbed` (the final native check),
recorded in
[`redesign_validation_2026-10-10.json`](../../results/redesign_validation_2026-10-10.json):
setup with the PIN, presets and room; saved settings surviving a restart;
parental controls, the PIN keypad, details scrolling and credits driven by the
remote with the outline and underline visible; Back during loading; playback
with captions through both practice holds. The Inter medium and semibold faces
rendering as themselves was seen in the second native build and is recorded in
[NATIVE_IMPLEMENTATION.md](NATIVE_IMPLEMENTATION.md).

What has not been seen on a device:

- anything since `73fbbed`: the Oct 10 polish (the new Harbor artwork, taller
  cards, quieter navigation), the Oct 11 seamless pass (the shorter synopsis,
  saving feedback beside the title, Back in setup), and the motion and sound
  pass with its fixes;
- the artwork motion, on any build. Its intermediate frames have not been
  recorded or run through flashmap; the static interface check does not cover
  them;
- either sound, on any build. Neither the chime nor the selection sound has
  been heard on a device;
- reduced motion and screen-reader behaviour on the device, including
  VoiceView reading order. Both rest on unit tests today.

Physical televisions, sticks and camera timing are outside this submission.
The steps that close these gaps are in [`MAC_FINISH.md`](../MAC_FINISH.md), and
the release blockers are in
[`COMPLETION_CHECKLIST.md`](../COMPLETION_CHECKLIST.md).

## How this page is checked

From the repository root:

    .venv/bin/python -m pytest eval/tests/test_design_page.py -q

The test reads `CALM_COLORS`, `CALM_TEXT`,
`CALM_FONT`, `CALM_SPACE` and the focus and contrast constants out of
`calmStyles.ts`, then holds this page's palette, type and spacing tables and
`tokens.json` to them. It recomputes every ratio in the two contrast tables
and in `tokens.json`, and fails on any text pair under 4.5 to 1 or ring pair
under 3 to 1. It also checks that the logo's colours in
`app/assets/brand/make_logo.py` are palette colours, and that the logo table
on the brand page names the right token for each. Three negative controls in
the same file feed its comparisons an altered palette, ratio and pair, and
expect a complaint every time.
