/** Read-only media-clock observation. It never controls playback or protection. */
import { VideoPlayer } from '@amazon-devices/react-native-w3cmedia';
import { RefObject, useEffect, useState } from 'react';

export const PROGRESS_SAMPLE_MS = 1000;
export const SLOW_WINDOW_MS = 6000;
const RECOVERY_WINDOW_MS = 3000;
interface Sample { wallMs: number; mediaSeconds: number; rate: number; }

/** Sustained progress below half the requested rate, with a separate recovery window.
 * Native evidence showed slow advancing clocks without a waiting event. This says
 * only what the clock establishes, not whether the network, decoder or audio failed.
 */
export function createProgressMonitor() {
  let baseline: Sample | null = null;
  let previous: Sample | null = null;
  let slow = false;
  const reset = () => { baseline = null; previous = null; slow = false; };
  return {
    reset,
    sample(wallMs: number, mediaSeconds: number, rate = 1): boolean {
      if (!Number.isFinite(mediaSeconds) || !Number.isFinite(rate) || rate <= 0) {
        reset(); return false;
      }
      const next = { wallMs, mediaSeconds, rate };
      if (previous) {
        const elapsed = wallMs - previous.wallMs;
        const moved = mediaSeconds - previous.mediaSeconds;
        // Ignore host sleep, clock changes, seeks and rate changes. A late JS
        // callback alone is not evidence that the native player was slow.
        if (elapsed <= 0 || elapsed > 2500 || rate !== previous.rate || moved < 0 ||
            moved * 1000 > elapsed * rate * 2 + 500) reset();
      }
      baseline ??= next;
      previous = next;
      const elapsed = wallMs - baseline.wallMs;
      if (elapsed >= (slow ? RECOVERY_WINDOW_MS : SLOW_WINDOW_MS)) {
        const progress = (mediaSeconds - baseline.mediaSeconds) * 1000 / (elapsed * rate);
        slow = progress < (slow ? 0.8 : 0.5);
        baseline = next;
      }
      return slow;
    },
  };
}

export function usePlaybackProgress(mediaRef: RefObject<VideoPlayer | null>, enabled: boolean): boolean {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    const media = mediaRef.current;
    setSlow(false);
    if (!enabled || !media) return;
    const monitor = createProgressMonitor();
    let seeking = false;
    const reset = () => { monitor.reset(); setSlow(false); };
    const onSeeking = () => { seeking = true; reset(); };
    const onSeeked = () => { seeking = false; reset(); };
    const sample = () => {
      if (mediaRef.current !== media || media.paused || media.ended || media.seeking || seeking) {
        reset(); return;
      }
      setSlow(monitor.sample(Date.now(), media.currentTime, media.playbackRate ?? 1));
    };
    const resetEvents = ['pause', 'play', 'ended', 'error', 'ratechange'];
    resetEvents.forEach(event => media.addEventListener?.(event, reset));
    media.addEventListener?.('seeking', onSeeking);
    media.addEventListener?.('seeked', onSeeked);
    sample();
    const timer = setInterval(sample, PROGRESS_SAMPLE_MS);
    return () => {
      clearInterval(timer);
      resetEvents.forEach(event => media.removeEventListener?.(event, reset));
      media.removeEventListener?.('seeking', onSeeking);
      media.removeEventListener?.('seeked', onSeeked);
    };
  }, [enabled, mediaRef]);
  return enabled && slow;
}
