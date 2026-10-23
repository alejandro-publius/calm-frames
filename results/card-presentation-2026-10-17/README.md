# Steadier player cards, October 17, 2026

Source only, following the owner's report that the transition from "Flashing hidden"
to Skip/status cards feels too quick and robotic. No installation, restart, native
navigation, capture, recording, media/trust/detector change or push occurred.

## Exact old sequence

The installed app source 3f681a783c792cc046a704ac6ebb9383a8128e9c and review source
d788a9d1416a86fb0a281142726995c796cca9e3 have identical cards.ts, CalmCard.tsx,
usePlaybackPresentation.ts and useFlashGuard.ts. The source sequence was:

1. Five media seconds before a covered interval, "Flashing coming up" with a
   changing whole-second countdown and a focused Skip button.
2. At the interval start, "Flashing hidden / Sound continues while this scene is
   hidden", removing Skip and changing card height/focus ownership.
3. At the end, "Scene hidden for N seconds / Sound continued" for up to five
   media seconds, unless the next countdown takes priority.
4. Nearby intervals could switch straight back to a countdown and restore Skip.

The hook pushed its raw cards to AccessibilityInfo, while the visible card also
used live-region/alert announcements. The screen adjusted paused text separately.
This allowed changing seconds, multiple status kinds and duplicate/stale speech
paths even though the protective cover itself followed the right schedule.

Skip was and remains an explicit press calling guard.skipTo, then the existing
seek engine. It is not an automatic skip or detector action.

## New consumer sequence

During the existing five-second lead and throughout the covered scene, show one
stable title, "Flashing scenes", and "The picture is hidden during flashing. You
can skip past this scene." Keep Skip in the same action slot through both phases.
When an adjacent scene is already within the lead window, keep the same words and
button while updating its target to that current scene. At the end, return to the
video without the redundant completion card. No counting numbers or fades.

The harmless practice video instead says "Practice cover" and explicitly describes
planned demo scenes. Pause immediately says "Paused. Press Play to continue, or
Skip to jump past this scene." Buffering immediately says "Waiting for playback.
You can skip past this scene." Its card owns the status, suppressing a second
Loading plate. Ended/error removes stale Skip immediately. No copy claims audio
is playing while paused or buffering.

The card width and detail slot are stable at the standard text size. Large-text
accessibility can still expand content rather than clip it. No native visual
acceptance is claimed from these renderer tests.

## Timing and protection boundaries

No media, detector, interval, seek-engine, cover, readiness or teardown timing was
changed. Cover state still reads directly from the guard. The card is a pure
presentation adapter; it neither writes currentTime nor pauses/plays media. Skip
remains immediately actionable and uses the current signed interval end plus the
existing 100 ms margin, including during a cover. Repeated presses go through the
existing guarded seek path. Back remains immediate after confirmed teardown.

Only noncritical speech waits 600 wall-clock milliseconds. This is a short settling
period for fleeting status, not a minimum visual/cover duration or a video wait.
The message itself and Skip render immediately. Disappearing/superseded messages
cancel the pending speech. Identical lead/cover/adjacent messages do not reannounce.
Pause/checking/refusal speech is immediate. The consumer disables the guard's raw
card speech and the card's live-region/alert path, then announces final visible copy
without queueing obsolete status. Other hook consumers retain their default API.
Actual VoiceView/compositor behavior remains for native verification.

## Evidence and remaining step

126 tests across 12 affected suites pass (125 in the initial complete targeted run,
then the additional urgent-refusal case passes in the final focused rerun). Tests
cover short/adjacent intervals with exact unchanged cover boundaries, fixed action
styles, target updates after seek, pause/resume, buffering, ended/error, repeated
Skip, immediate Back, speech cancellation/refusal, route rejection and hook mirror.
Typecheck passes. Targeted lint has zero errors and two existing no-void warnings.

The prior independent cache/teardown review is GO for an owner-approved checkpoint
at d788a9d1416a86fb0a281142726995c796cca9e3. It found no blocking source regression;
37 focused cache/teardown tests passed. Its report is in the performance evidence.

Installation approval is still pending. After approval, use one native checkpoint
to assess card readability, Skip/Back/focus, VoiceView behavior, and actual loading
and playback continuity. Source tests do not prove the app now feels smooth or fast.
