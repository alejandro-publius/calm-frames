# Pause history race: bounded source correction

Source: `54d0256d2d6a19044be12157b76d14a580c48c2b`, from main `84cd4778`.
The new regression demonstrates a missed announcement when native pause state
arrives before the React pause prop and the controls timer commits between them.
The previous code replaced its observed-playback flag with the current native
paused state, erasing evidence that this player had played. The delayed pause
was consequently treated like an initial paused entry.

The flag now retains an observed playing state for the lifetime of the player.
Initial/restored pauses remain silent, real subsequent pauses retain their
notice, repeated controls show/hide cannot duplicate it, and resume/unmount
still cancel pending speech. No delay, queue option, cover, seek, audio engine,
dependency, media or household behavior was changed.

The new test fails before the fix. Afterward,
<!--n results/pause-history-race-2026-10-26.json:focused_tests.passed -->46<!--/n-->
focused playback/copy/recovery tests, typecheck and focused lint pass. One normal
Debug build passed its existing pre/post gates. Verified generated player inputs
were reused only after their generator inputs matched the prior native source;
no tracked file was overwritten. The resulting package was installed explicitly
on the disposable fictional emulator, preserving its saved data.

This is a proven source race, not proof that it caused every prior native miss.
The earlier failed native speech receipt remains valid for its stated source.
## Bounded native result

**FAIL**, Debug at 1280 by 720 with VoiceView. Focus speech was captured before
the test. Two actual pauses separated by resumed playback show their guidance,
but the offline transcript contains only one pause instruction across the
recording. This does not satisfy one instruction per real pause. Raw recording
identity is in the [machine record](../results/pause-history-race-2026-10-26.json);
raw app-only captures remain outside Git. Machine transcription is not human
listening acceptance, and change-only frames are not decoder timing evidence.

The source race correction is retained as a bounded logical fix. It is not a
reliable native speech fix. No additional delay or speculative audio change was
added, and an unchanged cross-resolution or Release repeat was not run after
this failure. Further diagnosis needs observable native announcement delivery
or focus/speech arbitration evidence. The installed SDK maps the queue option
to its native polite flag; its announcement-finished event is documented as
iOS-only, so no delivery acknowledgement is claimed on Vega.

No whole item closes. Audit and unrelated hosted-test failures remain unchanged.
