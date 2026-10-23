# Demo script: one Acadia viewing, under three minutes

**Superseded.** The canonical demo script is
[DEMO_RUN_OF_SHOW.md](DEMO_RUN_OF_SHOW.md), which adapts this draft to
installed source `9cc57ca`. This October 16 draft is kept as a dated record. Do
not record from it.

Rules for the recording, when it happens: the television shows only the
prepared Acadia video; no original flashing footage is ever on screen; the
covered moments are the app's own black cover with the card over it; nothing
is cut together to suggest a result the build did not produce.

## Shot list and narration

**0:00 to 0:20. Home.** The dark cinema Home with the Acadia scene, the title,
Watch focused, Details beside it. Narration: "Calm Frames is for a family with
a child who is photosensitive. It plays selected videos that were checked
before they were added, and covers the flashing moments while the sound
continues. This is Acadia, a National Park Service clip."

**0:20 to 0:40. Details.** Press Right, then Select on Details. The same
scene, the running time, Watch and More info. Open More info, read the two
sentences on screen: the purpose line and the one built from the title's own
schedule. Narration: "Details says what the app does with this video, in the
app's words, read from its own data: how many brief parts are covered and
that the sound continues." Back.

**0:40 to 1:40. Watch, a covered moment, pause, seek, resume.** Select Watch.
The opening shell, then the picture. Let it play to the first covered part.
Narration while it plays: "Every frame was analysed before this video was
added, and the result is a signed map the app checks again before it opens the
file." When the card appears: "Here the map says a flashing part begins. The
picture is covered just before it starts, the sound continues, and the card
says what is happening. The cover comes off when the part ends." Press pause
on the card: the card says it is paused. Press play. Press Right on the seek
bar once, into or past a covered part: "Seeking is guarded the same way. The
cover goes on first, then the playhead moves." Let it resume.

**1:40 to 2:00. Back.** Press Back. The return shell, then Home with focus on
Watch, the control that started playback. Narration: "Back brings the remote
back to the control it left."

**2:00 to 2:40. What it refuses, shown where it can be shown.** The consumer
catalog carries no unavailable video, so this part is not faked on the
television. Two options, and the narration must say which one is on screen:

- On the television: Parents, enter the PIN, Videos. The list names each
  checked video and its state. Narration: "A video that did not verify never
  reaches the viewing screen. Parents can see which ones were held back and
  why. And Calm Frames only works with videos inside it: not other apps, not
  live television."
- On a laptop, in a terminal: run the refusal suite,
  `cd app && node_modules/.bin/jest --watchman=false --ci test/calmframes/playerRouteRefusal.test.tsx`,
  and leave the nine refused routes and the one control on screen. Narration:
  "Nine ways of altering a prepared route, each refused: no picture, one
  unavailable card, one way back. The tenth line is the exact compiled Acadia
  route, which plays."

**2:40 to 2:55. Close.** Home again. Narration, word for word: "Calm Frames
reduces exposure to flashing above published limits in the videos it plays;
not a medical device. It is open source, and the analyser and its checks are
in the repository."

## Before anyone presses record

- The Acadia-first build is installed and the whole journey above has been
  walked with the remote, with the receipt updated.
- The first covered part's time in Acadia is read from the map, not guessed,
  so the recording can wait for it.
- Captions: Acadia ships none, so nothing in the narration says captions
  continue. If a captioned title is added later, say it only then.
- No number in the narration beyond what is on screen.
