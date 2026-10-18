/** Deterministic decisions; no player, React, renderer, timer or network. */
import { CoverInterval, intervalAt, nextIntervalAfter } from '../coverSchedule';
import {
  coverageData,
  PlaybackIdentity,
  VerifiedCoverage,
} from './verifiedCoverage';

export interface CoverageSample {
  identity: PlaybackIdentity;
  nowMs: number;
  positionMs: number;
  durationMs: number;
  paused: boolean;
  buffering: boolean;
  seeking: boolean;
  foreground: boolean;
  /** Host confirms the current load/seek generation and presentation timeline. */
  synchronized: boolean;
  playbackRate: number;
}
export interface CoverageDecision {
  action: 'cover' | 'restore' | 'unavailable';
  reason: string;
  interval?: CoverInterval;
  /** Advisory media boundary; never a promise that JS can hit a frame deadline. */
  nextBoundary?: {
    positionMs: number;
    afterMs: number;
    action: 'cover' | 'restore';
  };
}
export function samePlaybackIdentity(
  a: PlaybackIdentity,
  b: PlaybackIdentity,
): boolean {
  return (
    a.uri === b.uri &&
    a.sourceSha256 === b.sourceSha256 &&
    a.assetSha256 === b.assetSha256 &&
    a.editionId === b.editionId &&
    a.timelineId === b.timelineId
  );
}
export function evaluateCoverage(
  token: VerifiedCoverage,
  sample: CoverageSample,
): CoverageDecision {
  const data = coverageData(token);
  if (!data || !data.validAt(sample.nowMs))
    return { action: 'unavailable', reason: 'metadata-unverified-or-stale' };
  if (
    !samePlaybackIdentity(token.identity, sample.identity) ||
    sample.durationMs !== data.durationMs
  )
    return { action: 'unavailable', reason: 'edition-or-timeline-mismatch' };
  if (
    !Number.isFinite(sample.positionMs) ||
    sample.positionMs < 0 ||
    sample.positionMs > data.durationMs ||
    sample.playbackRate !== 1
  ) {
    return { action: 'unavailable', reason: 'unsupported-clock-or-rate' };
  }
  if (
    !sample.foreground ||
    !sample.synchronized ||
    sample.buffering ||
    sample.seeking
  ) {
    return { action: 'cover', reason: 'awaiting-current-timeline' };
  }
  const interval = intervalAt(data.intervals, sample.positionMs);
  const next = interval ?? nextIntervalAfter(data.intervals, sample.positionMs);
  return {
    action: interval ? 'cover' : 'restore',
    reason: interval ? 'scheduled-interval' : 'verified-position',
    interval,
    nextBoundary:
      !sample.paused && next
        ? {
            positionMs: interval ? interval.endMs : next.startMs,
            afterMs:
              (interval ? interval.endMs : next.startMs) - sample.positionMs,
            action: interval ? 'restore' : 'cover',
          }
        : undefined,
  };
}
