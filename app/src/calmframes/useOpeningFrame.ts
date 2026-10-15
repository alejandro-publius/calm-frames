import React from 'react';

interface OpeningMedia {
  readyState: number;
  currentTime?: number;
  paused?: boolean;
  getVideoPlaybackQuality?(): { totalVideoFrames: number; droppedVideoFrames: number };
}

/** How far the clock has to move, with the picture decodable, before the opening trusts it. */
export const OPENING_CLOCK_ADVANCE_S = 0.25;

/**
 * A presentation gate only. The independent signed-picture cover stays in force.
 *
 * The strong signal is the element's frame counter: a decoded frame that was not
 * dropped, with current data. The Vega Virtual Device's player never fills that
 * counter (every call fails inside the media stack), so a session there sat on
 * the opening shell for the whole 15 second stall allowance while the film
 * played underneath, then showed the recovery screen. When the counter is
 * silent, the media clock moving while the element is playing with current data
 * is the evidence that frames are being delivered; a clock that does not move
 * still reaches the recovery screen.
 */
export function hasOpeningFrame(media: OpeningMedia | null): boolean {
  if (!media || media.readyState < 2) return false;
  try {
    const quality = media.getVideoPlaybackQuality?.();
    return !!quality && Number.isFinite(quality.totalVideoFrames) && Number.isFinite(quality.droppedVideoFrames) &&
      quality.totalVideoFrames > quality.droppedVideoFrames;
  } catch { return false; }
}

/** True when the element offers no frame count at all: missing, throwing, or reporting zero frames. */
export function frameCounterSilent(media: OpeningMedia | null): boolean {
  if (!media) return false;
  try {
    const quality = media.getVideoPlaybackQuality?.();
    return !quality || !Number.isFinite(quality.totalVideoFrames) || quality.totalVideoFrames <= 0;
  } catch { return true; }
}

export default function useOpeningFrame({ media, enabled, verified, surfaceReady, onTimeout }: {
  media: React.MutableRefObject<OpeningMedia | null>; enabled: boolean; verified: boolean; surfaceReady: boolean; onTimeout: () => void;
}) {
  const [ready, setReady] = React.useState(false);
  const failure = React.useRef(onTimeout); failure.current = onTimeout;
  const clockAtStart = React.useRef<number | null>(null);
  React.useEffect(() => {
    if (!enabled || ready) return;
    const timeout = setTimeout(() => failure.current(), 15000);
    return () => clearTimeout(timeout);
  }, [enabled, ready]);
  React.useEffect(() => {
    if (!enabled || ready || !verified || !surfaceReady) return;
    const check = () => {
      const element = media.current;
      if (hasOpeningFrame(element)) { setReady(true); return; }
      if (!element || element.readyState < 2 || !frameCounterSilent(element)) return;
      const clock = typeof element.currentTime === 'number' && Number.isFinite(element.currentTime) ? element.currentTime : null;
      if (clock === null) return;
      if (clockAtStart.current === null) { clockAtStart.current = clock; return; }
      if (!element.paused && clock - clockAtStart.current >= OPENING_CLOCK_ADVANCE_S) setReady(true);
    };
    check();
    const poll = setInterval(check, 100);
    return () => clearInterval(poll);
  }, [enabled, ready, verified, surfaceReady, media]);
  return ready;
}
