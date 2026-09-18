/**
 * The chime cue, driven by the guard.
 *
 * `chimeCue.ts` decides when a chime is due and holds the promise that one
 * never sounds without a cover following it. This is the React side: it steps
 * that state machine from the numbers `useFlashGuard` already reports, and
 * plays the sound when the step says so.
 *
 *     const guard = useFlashGuard({ ... });
 *     useChimeCue({
 *       intervals: guard.intervals,
 *       mediaTimeMs: guard.mediaTimeMs,
 *       covered: guard.covered,
 *       verified: guard.status === 'verified',
 *       enabled: family.chimeEnabled,
 *       playChime,
 *       titleId,
 *     });
 *
 * The sound itself is a port rather than something this file knows how to
 * make. Nothing in the app can play a short sound yet: there is no chime asset
 * in the package, and the one audio path Vega gives us is the same
 * w3cmedia player the title is already using, which is one per process. So the
 * default here is silence, and it says so rather than pretending. Everything
 * that decides whether a chime is due is real, tested and mutation checked;
 * what is missing is a waveform and a device to hear it on. See
 * docs/DECISIONS.md, 2026-09-18.
 */

import { useEffect, useRef, useState } from 'react';
import {
  ChimeCueState,
  CHIME_LEAD_MS,
  CHIME_ON_BY_DEFAULT,
  emptyChimeCue,
  resetChimeCue,
  stepChimeCue,
} from './chimeCue';
import { CoverInterval } from './coverSchedule';

/** What actually makes the sound. Handed in, never reached for. */
export type PlayChime = () => void;

export interface UseChimeCueOptions {
  intervals: CoverInterval[];
  mediaTimeMs: number;
  /** True while the picture is hidden, for any reason. */
  covered: boolean;
  /** True only once the map has verified and there is a schedule. */
  verified: boolean;
  /** The household switch. On unless a household turned it off. */
  enabled?: boolean;
  leadMs?: number;
  playChime?: PlayChime;
  /** A new title is a new sitting, so what was announced is forgotten. */
  titleId?: string;
}

export function useChimeCue(options: UseChimeCueOptions): ChimeCueState {
  const {
    intervals,
    mediaTimeMs,
    covered,
    verified,
    enabled = CHIME_ON_BY_DEFAULT,
    leadMs = CHIME_LEAD_MS,
    playChime,
    titleId = 'unknown',
  } = options;

  // The cue is held in a ref as well as in state, so that two renders in the
  // same tick cannot both see the old state and both sound the chime. The ref
  // is what the next step reads; the state is only what the caller sees.
  const cueRef = useRef<ChimeCueState>(emptyChimeCue());
  const [cue, setCue] = useState<ChimeCueState>(cueRef.current);

  useEffect(() => {
    cueRef.current = resetChimeCue(cueRef.current);
    setCue(cueRef.current);
  }, [titleId]);

  useEffect(() => {
    const result = stepChimeCue(cueRef.current, {
      intervals,
      mediaTimeMs,
      covered,
      verified,
      enabled,
      leadMs,
    });
    if (result.state !== cueRef.current) {
      cueRef.current = result.state;
      setCue(result.state);
    }
    if (result.play) {
      playChime?.();
    }
  }, [intervals, mediaTimeMs, covered, verified, enabled, leadMs, playChime]);

  return cue;
}
