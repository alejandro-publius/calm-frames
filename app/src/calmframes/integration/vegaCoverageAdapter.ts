/** Reference adapter only: not imported by the production player. */
import type { VideoPlayer } from '@amazon-devices/react-native-w3cmedia';
import {
  CoverageDecision,
  evaluateCoverage,
  samePlaybackIdentity,
} from './coverageController';
import { PlaybackIdentity, VerifiedCoverage } from './verifiedCoverage';

export type VegaCoveragePlayer = Pick<
  VideoPlayer,
  | 'currentTime'
  | 'duration'
  | 'paused'
  | 'playbackRate'
  | 'loop'
  | 'seeking'
  | 'readyState'
  | 'src'
  | 'currentSrc'
  | 'pause'
  | 'play'
  | 'addEventListener'
  | 'removeEventListener'
>;
export interface VegaCoverageHost {
  now: () => number;
  /** Read from the current asset loader, never from this adapter's token. */
  identity: () => PlaybackIdentity;
  onDecision: (decision: CoverageDecision) => void;
  /** Must resolve only after an opaque cover is presented. React setState is insufficient. */
  presentCover: () => Promise<void>;
  /** Route into the host's one guarded seek implementation; target is milliseconds. */
  seek: (targetMs: number) => Promise<void>;
}

export function attachVegaCoverage(
  player: VegaCoveragePlayer,
  token: VerifiedCoverage,
  host: VegaCoverageHost,
) {
  let detached = false,
    foreground = true,
    buffering = true,
    synchronized = false;
  let generation = 0,
    terminal = false,
    pending = 0;
  let operationSerial = 0,
    cancellation = 0;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let boundaryFloor: number | undefined;
  const clearTimer = () => {
    if (timer !== undefined) clearTimeout(timer);
    timer = undefined;
  };
  const cover = (reason: string) =>
    host.onDecision({ action: 'cover', reason });
  const invalidate = (reason: string) => {
    generation++;
    synchronized = false;
    boundaryFloor = undefined;
    clearTimer();
    if (!detached) cover(reason);
    return generation;
  };
  const sample = (): CoverageDecision =>
    !samePlaybackIdentity(host.identity(), token.identity)
      ? { action: 'unavailable', reason: 'loader-identity-mismatch' }
      : player.loop
      ? { action: 'unavailable', reason: 'repeat-unsupported' }
      : evaluateCoverage(token, {
          identity: {
            ...host.identity(),
            uri: player.currentSrc || player.src,
          },
          nowMs: host.now(),
          positionMs: player.currentTime * 1000,
          durationMs: player.duration * 1000,
          paused: player.paused,
          playbackRate: player.playbackRate,
          seeking: player.seeking,
          buffering: buffering || player.readyState < 2,
          foreground,
          synchronized,
        });
  const publish = () => {
    if (detached) return;
    clearTimer();
    let decision = terminal
      ? { action: 'unavailable' as const, reason: 'session-invalidated' }
      : sample();
    if (decision.action === 'unavailable') {
      terminal = true;
      synchronized = false;
      if (!player.paused) player.pause();
    }
    if (boundaryFloor !== undefined) {
      if (
        player.currentTime * 1000 < boundaryFloor &&
        decision.action === 'restore'
      ) {
        decision = {
          action: 'cover',
          reason: 'boundary-awaiting-fresh-position',
        };
      } else if (player.currentTime * 1000 >= boundaryFloor)
        boundaryFloor = undefined;
    }
    host.onDecision(decision);
    if (decision.action === 'unavailable' || !foreground || player.paused)
      return;
    const next = decision.nextBoundary;
    // Timers can only hide, never reveal. A late/missing sample hides after 250ms.
    const due = next?.action === 'cover' ? Math.min(250, next.afterMs) : 250;
    const captured = generation;
    timer = setTimeout(() => {
      if (detached || captured !== generation) return;
      if (next?.action === 'cover' && next.afterMs <= 250) {
        boundaryFloor = next.positionMs;
        cover('anticipated-boundary');
      } else {
        invalidate('clock-sample-overdue');
      }
    }, Math.max(0, due));
  };
  const onUncertain = () => {
    buffering = true;
    invalidate('player-discontinuity');
  };
  const onSeeked = () => {
    buffering = false;
    publish();
  }; // Does not certify a generation.
  const onPlaying = () => {
    buffering = false;
    publish();
  };
  const onError = () => {
    terminal = true;
    invalidate('player-error');
    publish();
  };
  const events: Array<[string, () => void]> = [
    ['timeupdate', publish],
    ['pause', publish],
    ['playing', onPlaying],
    ['waiting', onUncertain],
    ['stalled', onUncertain],
    ['seeking', onUncertain],
    ['seeked', onSeeked],
    ['emptied', onUncertain],
    ['loadstart', onUncertain],
    ['loadedmetadata', onUncertain],
    ['ratechange', publish],
    ['error', onError],
    ['ended', onUncertain],
  ];
  invalidate('attached-awaiting-timeline');
  const attached: typeof events = [];
  try {
    events.forEach(([name, listener]) => {
      player.addEventListener(name, listener);
      attached.push([name, listener]);
    });
  } catch (error) {
    detached = true;
    clearTimer();
    attached.forEach(([name, listener]) =>
      player.removeEventListener(name, listener),
    );
    player.pause();
    throw error;
  }
  return {
    /** Capture this after the current seek/load settles; obsolete generations are refused. */
    generation: () => generation,
    synchronize: (expectedGeneration: number) => {
      if (
        detached ||
        terminal ||
        pending !== 0 ||
        !foreground ||
        expectedGeneration !== generation ||
        player.seeking ||
        player.readyState < 2
      )
        return false;
      buffering = false;
      synchronized = true;
      publish();
      return !terminal;
    },
    discontinuity: () => {
      if (detached) return generation;
      cancellation++;
      return invalidate('host-discontinuity');
    },
    setForeground: (active: boolean) => {
      if (detached) return;
      cancellation++;
      foreground = active;
      invalidate(active ? 'resume-awaiting-timeline' : 'background');
      if (!active) player.pause();
    },
    seek: async (targetMs: number) => {
      if (
        detached ||
        terminal ||
        pending !== 0 ||
        !foreground ||
        !Number.isFinite(targetMs) ||
        targetMs < 0 ||
        targetMs > player.duration * 1000
      )
        return false;
      const current = invalidate('seek-awaiting-cover');
      const operation = ++operationSerial;
      const ticket = cancellation;
      pending = operation;
      try {
        await host.presentCover();
        if (detached || terminal || !foreground || current !== generation)
          return false;
        if (sample().action === 'unavailable') {
          terminal = true;
          publish();
          return false;
        }
        await host.seek(targetMs);
        if (ticket !== cancellation || detached || terminal) {
          if (!detached) player.pause();
          return false;
        }
        return true;
      } catch (error) {
        if (!detached) {
          terminal = true;
          invalidate('transport-failed');
          publish();
        }
        throw error;
      } finally {
        if (pending === operation) pending = 0;
      }
    },
    play: async () => {
      if (detached || terminal || pending !== 0 || !foreground) return false;
      const current = invalidate('play-awaiting-cover');
      const operation = ++operationSerial;
      const ticket = cancellation;
      pending = operation;
      try {
        await host.presentCover();
        if (detached || terminal || !foreground || current !== generation)
          return false;
        if (sample().action === 'unavailable') {
          terminal = true;
          publish();
          return false;
        }
        await player.play();
        if (ticket !== cancellation || detached || terminal) {
          if (!detached) player.pause();
          return false;
        }
        return true;
      } catch (error) {
        if (!detached) {
          terminal = true;
          invalidate('transport-failed');
          publish();
        }
        throw error;
      } finally {
        if (pending === operation) pending = 0;
      }
    },
    pause: () => {
      if (!detached) {
        cancellation++;
        invalidate('paused');
        player.pause();
      }
    },
    poll: publish,
    detach: () => {
      if (detached) return;
      cancellation++;
      invalidate('detached');
      detached = true;
      events.forEach(([name, listener]) =>
        player.removeEventListener(name, listener),
      );
    },
  };
}
