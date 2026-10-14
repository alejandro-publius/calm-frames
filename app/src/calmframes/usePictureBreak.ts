/**
 * The picture break, wired to the remote and to time. pictureBreak.ts holds
 * every rule; this hook only feeds it the clock, the playhead and key presses.
 *
 * Menu starts a break or asks for the picture back. OK asks for the picture
 * back while a break is running; the card's focused button asks the same
 * thing, and asking twice changes nothing. A request the rules hold back is
 * settled again whenever the playhead moves, and once more when the minimum
 * break has run out, so the picture returns by itself. For OK_GRACE_MS after
 * a return, OK still belongs to the break, so pressing OK twice to get the
 * picture back cannot pause the film.
 *
 * Nothing here moves the playhead, pauses, touches captions or writes history.
 */

import { HWEvent, useTVEventHandler } from '@amazon-devices/react-native-kepler';
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from 'react';
import { Platform } from 'react-native';
import { DPADEventType, EVENT_KEY_DOWN } from '../constants';
import { CoverInterval } from './coverSchedule';
import {
  breakOwnsSelect,
  expireGrace,
  MIN_BREAK_MS,
  NO_BREAK,
  OK_GRACE_MS,
  PictureBreakState,
  requestReturn,
  settleBreak,
  toggleBreak,
} from './pictureBreak';

export interface PictureBreakOptions {
  /** True only for a verified, guarded title with the prototype switched on. */
  enabled: boolean;
  intervals: CoverInterval[];
  mediaTimeMs: number;
  /** Injected so tests can choose the time. */
  nowMs?: () => number;
}

export interface PictureBreak {
  /** NO_BREAK whenever the break is not enabled. */
  state: PictureBreakState;
  resting: boolean;
  /** OK is the break's, not the player's: during a break and just after. */
  ownsSelect: boolean;
  /** For the card's button: ask for the picture back. */
  requestReturn: () => void;
  /** For the Menu key: start a break or ask for the picture back. */
  toggle: () => void;
}

export function usePictureBreak({
  enabled,
  intervals,
  mediaTimeMs,
  nowMs = Date.now,
}: PictureBreakOptions): PictureBreak {
  const [raw, setRaw] = useState<PictureBreakState>(NO_BREAK);
  const state = enabled ? raw : NO_BREAK;

  // Only committed values reach the key handler and the timers.
  const latest = useRef({ enabled, intervals, mediaTimeMs, nowMs, resting: state.resting });
  useLayoutEffect(() => {
    latest.current = { enabled, intervals, mediaTimeMs, nowMs, resting: state.resting };
  });

  const settleNow = useCallback((previous: PictureBreakState) => {
    const now = latest.current;
    return settleBreak(previous, now.nowMs(), now.mediaTimeMs, now.intervals);
  }, []);

  const toggle = useCallback(() => {
    if (!latest.current.enabled) {
      return;
    }
    setRaw((previous) => settleNow(toggleBreak(previous, latest.current.nowMs())));
  }, [settleNow]);

  const askForPicture = useCallback(() => {
    setRaw((previous) => settleNow(requestReturn(previous)));
  }, [settleNow]);

  // A title that stops being verified, or a player error, ends the break. The
  // guard keeps those covered on its own.
  useEffect(() => {
    if (!enabled) {
      setRaw(NO_BREAK);
    }
  }, [enabled]);

  // The playhead moved or the schedule changed: a held-back return may be due.
  useEffect(() => {
    setRaw((previous) => settleNow(previous));
  }, [mediaTimeMs, intervals, settleNow]);

  // A return held back only by the minimum break comes due on the clock alone.
  useEffect(() => {
    if (!raw.resting || !raw.returnRequested || raw.waitingFor !== 'minimum') {
      return;
    }
    const remaining = raw.startedAtMs + MIN_BREAK_MS - latest.current.nowMs();
    const timer = setTimeout(
      () => setRaw((previous) => settleNow(previous)),
      Math.max(0, remaining) + 1,
    );
    return () => clearTimeout(timer);
  }, [raw, settleNow]);

  // After a return, OK stays the break's for a moment, then goes back.
  useEffect(() => {
    if (raw.resting || raw.endedAtMs === undefined) {
      return;
    }
    const remaining = raw.endedAtMs + OK_GRACE_MS - latest.current.nowMs();
    const timer = setTimeout(
      () => setRaw((previous) => expireGrace(previous, latest.current.nowMs())),
      Math.max(0, remaining) + 1,
    );
    return () => clearTimeout(timer);
  }, [raw]);

  const onRemote = useCallback(
    function pictureBreakRemote(evt: HWEvent) {
      if (!Platform.isTV || !evt || evt.eventKeyAction !== EVENT_KEY_DOWN) {
        return;
      }
      if (!latest.current.enabled) {
        return;
      }
      if (evt.eventType === DPADEventType.MENU) {
        toggle();
      } else if (
        evt.eventType === DPADEventType.SELECT &&
        latest.current.resting
      ) {
        askForPicture();
      }
    },
    [toggle, askForPicture],
  );
  useTVEventHandler(onRemote);

  return {
    state,
    resting: state.resting,
    ownsSelect: breakOwnsSelect(state),
    requestReturn: askForPicture,
    toggle,
  };
}
