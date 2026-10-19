# Current demo run of show

Source: branch `claude/ocean-layout-fix-2026-10-19`, October 19, 2026; app code
last changed in `53a1c51`. Nothing from this branch has been built, installed or
seen on a device. The screens below come from the code (`KidHomeScreen.tsx`,
`homeIslands.ts`, `TitleDetailsScreen.tsx`) and from the browser renders in
[results/home-islands-2026-10-19](../../results/home-islands-2026-10-19/README.md),
which show composition, not native pixels. The last install with a receipt here
is source `805f855` on October 18 (package SHA-256
`8e58685d579a740743e5d6e89b0fa8bbcce42e7a6189b9c92265575ea0c1e511`), with the
earlier island order. The owner's October 19 note says the Mac now runs
`2b78587`, which was never pushed and cannot be inspected from here. No
recording or capture is authorized; whether and when to record is the owner's
decision.

## The route, about 2 minutes 35 seconds

Start on Home in an existing household with Acadia selected (the boat waits by
its island) and Watch focused. A launch lands there: with nothing chosen yet,
Home features the first ready title, Acadia, and focuses Watch. Never press
Back on Home itself; it leaves the app. Times are a plan, not a measurement;
the three clips alone run about 70 seconds (37.6, 20.0 and 12.0).

1. **0:00 Home, no keys.** The coastal map: Calm Frames, then the profile
   button (Everyone in the renders), How it works and Parents in the header.
   "Ocean" over the Acadia and Sea otters cards, "Forest" over the Forest card.
   Second lines: "Silent · 38 sec", "Silent · 20 sec", "Nature audio · 12 sec".
   Watch and Details sit on the sand for the chosen island.
2. **0:15 Right, Select.** Right moves from Watch to Details on the sand; Select
   opens Acadia Details with Watch focused: Back, "Acadia", "38 seconds", Watch,
   More info, "Waves along the coast of Acadia National Park." and "Scenes
   replaced: 2 scenes · 9 seconds" under Extra cautious (7 seconds under WCAG or
   Broadcast).
3. **0:20 Right, Select.** More info opens with Back focused: the ocean
   replacement line, "Calm Frames works only with prepared videos in this app,
   not other apps or live TV.", the detection limits with the approved sentence,
   the NPS credit and Technical details. **Back** returns to Details with More
   info focused; **Left** reaches Watch.
4. **0:40 Select.** A short opening shows the island, then Acadia plays, about
   38 seconds. Under Extra cautious its two flagged intervals, 7.343 to 12.699
   seconds and 28.113 to 31.593 seconds, show approved ocean footage in place of
   the original picture. The audio track is silent (it measures -91 dB), so the
   narration should not promise sound here. At the natural end the app returns
   to Details, Watch focused.
5. **1:22 Back, Left, Up, Right, Select.** Back returns Home with Details
   focused, because Details opened the title. Left reaches Watch, Up the Acadia
   card, Right the Sea otters card, and the boat moves to it. Select opens Sea
   otters Details: "20 seconds · Silent · Plays once" and "Scenes covered: No
   flagged scenes.", which is a finding, not a safety certificate.
6. **1:32 Select.** The 19.987-second silent NOAA Fisheries clip plays once and
   returns to Details, Watch focused.
7. **1:56 Back, Right, Select.** Home with the Sea otters card focused; Right
   reaches Forest; Select opens Forest Details: "12 seconds · Nature sounds ·
   Plays once" and "Scenes covered: No flagged scenes."
8. **2:04 Select.** The 12-second NPS redwood creek excerpt plays once with its
   original nature audio and returns to Details.
9. **2:20 Back.** Home with the Forest card focused and the boat by Forest.
   Close on the scope and the approved sentence: Calm Frames reduces exposure to
   flashing above published limits in the videos it plays; not a medical device.

Back during any of these clips returns to Details with Watch focused, the same
as a natural end. The October 17 rules review asks for under three minutes;
`eval/check_video.sh` refuses a finished file of 180 seconds or longer and runs
the flash check on it.

## How sure each key is

None of these keys has been pressed on a build of this branch. The `805f855`
logs from October 18 recorded Details opening with Watch focused, Right to More
info, Select, Back to More info, Left to Watch, each clip playing to its natural
end and returning to Details Watch, and Back from Details to the card that
opened it. This branch keeps the same Details controls, route and player code;
only the Details photograph moved. On Home those logs recorded Right from Watch
to Details on the sand, Left back, and Up from Watch to Acadia; the sand row
keeps that order here. The islands moved: they now run Acadia, Sea otters,
Forest from left to right (on `805f855` Forest sat in the middle), so the
earlier Right presses between cards do not carry over. Opening Details from
Details on the sand, and Back returning focus to it, follow from the code, not
a log. Rehearse once on a build of this branch before anyone records, and
correct this page where a key lands somewhere else.

## The titles

- Acadia: NPS Acadia National Park coast, about 38 seconds, approved baked ocean
  replacement for its flagged intervals, silent audio track. Credit: NPS Video,
  Acadia National Park. No NPS endorsement is implied.
- Sea otters in Alaska: NOAA Fisheries B-roll at Unalaska/Dutch Harbor,
  19.987-second silent excerpt, plays once. Credit: NOAA Fisheries.
- Forest creek at Redwood: 12-second NPS Prairie Creek and Redwood excerpt,
  original nature audio, plays once. Credit: NPS: G Litten; no NPS endorsement
  implied.

The lighthouse, kelp and pines on the map are illustration; the card and
Details photographs are stills from the prepared videos.

## Evidence and limits

[The October 19 record](../../results/home-islands-2026-10-19/README.md): the
full app suite passes on `53a1c51` (1,676 passed, 0 failed; 18 failed on
`c84f95d`), and `app/test/calmframes/homeIslands.test.tsx` fails if anything on
Home, Details or the opening touches. The [October 18
receipts](../../results/forest-activation-2026-10-18/README.md) for `805f855`
counted a bounded 499 tests in 38 suites and 11 attribution tests.

Native logs establish focus, title identity and playback events, not pixels or
audio. Earlier `6f2570d` evidence separately covers pause/resume, protected Skip
and Parents cancellation. Every native check so far ran on the Vega Virtual
Device only; physical-TV, VoiceView and visual/audio acceptance remain open.
The demo recording, organizer footage question, judge access and submission
remain separate owner steps. Preserve credits for NPS Acadia, NPS: G Litten and
NOAA Fisheries.
