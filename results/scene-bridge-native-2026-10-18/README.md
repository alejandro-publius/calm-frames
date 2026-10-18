# Development-only static scene-bridge check

Source checkpoint: 65 focused tests pass across fixture, bridge validation, return
focus and KidModeScreen suites. TypeScript and focused ESLint pass. An independent
read-only review found no blocking trust/guard issue. Its competing preferred-focus
finding was fixed; logs explicitly say `opaque_requested`, and the dismissal button
is labeled “Skip test and return”.

The fixture has double `__DEV__` guards, no player/storage/trust registration, and
only the clearly labeled synthetic text “Test fixture: a card displays one.”
A stale rendition identity requests ordinary fallback. Remote Back and the Skip test
button return to the explicit entry, which restores its preferred focus.

No PIN was read, guessed, reset or entered. A bounded passive log check before the
build yielded no fresh focus/screen event and therefore did not establish an unlocked
Parents state. No personal-cover values were read or changed. The household-wide
editor rehearsal stays pending exact-value preservation and private owner unlock.

## Native checkpoint

App source: `50bc01fcfcfd82f4138b0cd0268beab60da286ee`. One build and one install
succeeded. All 781 tracked/existing generated app inputs match. The strict built
package gate passes with four original verification reports and the sole approved
Acadia bundle unchanged. Package SHA-256:
`44322944fc3fee3b353e5b20f12133a89273773ce57c742cbac10abdb6187bbd`.
The simulator's transferred copy matches that hash, and the app is running.

Nine bounded native log checks passed, listed in `native-results.json`. The explicit
Home → How it works → Scene bridge test route requested verified test text. Test
stale identity requested ordinary opaque fallback; Show test text restored the
verified text. Both remote Back and Skip test and return dismissed the fixture and
restored entry focus. How it works Back restored Home's opener; Parents cancel
restored Parents without PIN entry. The app was left at Home Watch and the owned
collector was stopped. Initial launch-focus logging was absent; later explicit
remote navigation established each tested state. No media played.

These logs establish React presentation requests and native focus/dismissal events.
They do not establish actual pixels, opacity, readable layout or audio quality.
Headless tests check the opaque style and text tree. No real authored bridge is
registered or claimed as native-tested. Device log timestamps are stale simulator
time; receipts and action timestamps use host UTC. Full raw logs remain outside
the repository at `../scene-bridge-native/`; the filtered trace is retained here.

## Exact remaining owner steps

1. On the installed Debug build, open Home → How it works → Scene bridge test to
   judge text legibility, layout, visible covering and focus. Use Test stale identity,
   Show test text, and either return control. This static test deliberately has no
   audio or video. Existing Acadia still needs separate look/listen acceptance.
2. Privately unlock Parents for the pending personal-cover rehearsal. Before any
   reversible addition, establish an exact snapshot of the existing household-wide
   additions and a way to restore those same values. An isolated profile does not
   isolate covers. No such state snapshot or native editor test is claimed here;
   no owner additions were changed or removed.
3. Any future real bridge needs owner-verified wording and an eligible immutable
   base cover. No new narrative, source acquisition or trust tuple was added.

No capture, recording, content search, push, publication, service restart, PIN
access, signing change or trust change occurred in this pass.
