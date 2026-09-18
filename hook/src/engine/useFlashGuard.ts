/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run `node hook/tools/sync.mjs`.
 */
/**
 * useFlashGuard: the whole guard, as one hook.
 *
 * Give it a player and where the map is, and it does the rest: verify the map,
 * build the schedule, drive the cover, decide the card, announce it, and hand
 * back the one seek function every control has to use.
 *
 * This is also what `hook/` ships for any Vega app using
 * @amazon-devices/react-native-w3cmedia, so it deliberately knows nothing
 * about Calm Frames screens, navigation or storage.
 *
 *     const guard = useFlashGuard({
 *       mediaRef: videoRef,
 *       mapUrl: title.mapUrl,
 *       expectedSha256: title.sha256,
 *       publicKeyBase64: OUR_KEY,
 *       ready: isVideoInitialized,
 *     });
 *
 *     <CoverLayer visible={guard.covered} mode={guard.coverMode} />
 *     <CalmCard card={guard.card} onSkip={guard.skipTo} />
 *
 * Fail closed is the default state, not an error path: `covered` starts true
 * and only a verified map can turn it off.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { announceForAccessibility } from './announce';
import { Card, cardAt, cardChanged, NO_CARD } from './cards';
import {
  buildCoverIntervals,
  CoverInterval,
  intervalAt,
} from './coverSchedule';
import {
  MapRejection,
  rejectionMessage,
  VerifiedFlashMap,
  verifyFlashMap,
} from './flashMap';
import {
  coverOptionsFor,
  DEFAULT_SETTINGS,
  HouseholdSettings,
  mapCoversRoom,
  PRESETS,
  unionSegments,
} from './household';
import { HideCause, HideLogEntry } from './hideLog';
import {
  createSeekEngine,
  SeekEngine,
  SeekPlan,
  SeekSource,
} from './seekSafety';
import { MediaElementLike, useCoverHarness } from './useCoverHarness';

export type GuardStatus = 'loading' | 'verified' | 'blocked';

export interface FlashGuardOptions {
  /** The W3C media element, once it exists. */
  mediaRef: { current: MediaElementLike | null };
  /** Where the maps are. One entry per profile name the preset asks for. */
  mapUrls?: Partial<Record<string, string>>;
  /** Or the map text itself, for a title bundled in the package. */
  mapTexts?: Partial<Record<string, string | null>>;
  /** SHA-256 of the file about to play, from the catalog entry. */
  expectedSha256: string;
  /** The public key this app ships. */
  publicKeyBase64: string;
  settings?: HouseholdSettings;
  /** True once the player exists. Before that the hook waits. */
  ready?: boolean;
  /** False when the app is in the background. */
  foreground?: boolean;
  durationMs?: number;
  titleId?: string;
  titleName?: string;
  /** Injected so tests do not need a network and a device does not need one. */
  fetchText?: (url: string) => Promise<string | null>;
  /** Injected so tests can choose the time. */
  nowMs?: () => number;
  maxMapAgeMs?: number;
  /** Called once per cover, for the parent area's log. */
  onHide?: (entry: HideLogEntry) => void;
}

export interface FlashGuardState {
  status: GuardStatus;
  rejection?: MapRejection;
  /** Plain wording for why the picture is hidden, when it is not a segment. */
  blockedReason?: string;
  covered: boolean;
  coverMode: 'opaque' | 'dim';
  card: Card;
  intervals: CoverInterval[];
  mediaTimeMs: number;
  /** Total milliseconds hidden so far in this sitting. */
  hiddenMs: number;
  /** The one seek funnel. Every control calls this. */
  requestSeek: (source: SeekSource, targetMs: number) => Promise<SeekPlan>;
  /** What the Skip button on a countdown card calls. */
  skipTo: (targetMs: number) => void;
  /** Hand this to VideoPlayer.setMediaControlFocus. */
  seekEngine: SeekEngine;
}

async function defaultFetchText(url: string): Promise<string | null> {
  try {
    const response = await fetch(url, { headers: { 'cache-control': 'no-cache' } });
    if (!response.ok) {
      return null;
    }
    return await response.text();
  } catch {
    // No network is a missing map, which keeps the picture hidden.
    return null;
  }
}

export function useFlashGuard(options: FlashGuardOptions): FlashGuardState {
  const {
    mediaRef,
    mapUrls,
    mapTexts,
    expectedSha256,
    publicKeyBase64,
    settings = DEFAULT_SETTINGS,
    ready = true,
    foreground = true,
    durationMs,
    titleId = 'unknown',
    titleName = 'this title',
    fetchText = defaultFetchText,
    nowMs = Date.now,
    maxMapAgeMs,
    onHide,
  } = options;

  const [status, setStatus] = useState<GuardStatus>('loading');
  const [rejection, setRejection] = useState<MapRejection | undefined>(undefined);
  const [blockedReason, setBlockedReason] = useState<string | undefined>(
    'Checking this title.',
  );
  const [segments, setSegments] = useState<CoverInterval[]>([]);
  const [seekHolding, setSeekHolding] = useState(false);
  const [hiddenMs, setHiddenMs] = useState(0);

  const coverOptions = useMemo(() => coverOptionsFor(settings), [settings]);

  const intervals = useMemo(() => segments, [segments]);
  const intervalsRef = useRef<CoverInterval[]>(intervals);
  intervalsRef.current = intervals;

  // Load and check the maps. Anything that goes wrong leaves the picture
  // hidden and names a reason.
  useEffect(() => {
    let cancelled = false;
    const preset = PRESETS[settings.preset] ?? PRESETS.wcag;

    const run = async () => {
      setStatus('loading');
      setBlockedReason('Checking this title.');
      const verifiedMaps: VerifiedFlashMap[] = [];
      for (const profile of preset.mapProfiles) {
        let text: string | null | undefined = mapTexts?.[profile];
        if (text === undefined && mapUrls?.[profile]) {
          text = await fetchText(mapUrls[profile] as string);
        }
        const verdict = verifyFlashMap(text ?? null, {
          publicKeyBase64,
          expectedSha256,
          nowMs: nowMs(),
          maxAgeMs: maxMapAgeMs,
        });
        if (!verdict.ok) {
          if (cancelled) {
            return;
          }
          setStatus('blocked');
          setRejection(verdict.reason);
          setBlockedReason(rejectionMessage(verdict.reason));
          setSegments([]);
          return;
        }
        if (!mapCoversRoom(verdict.map, settings)) {
          if (cancelled) {
            return;
          }
          setStatus('blocked');
          setRejection('missing');
          setBlockedReason(
            'This room is stricter than the check that was run, so the picture stays hidden.',
          );
          setSegments([]);
          return;
        }
        verifiedMaps.push(verdict.map);
      }
      if (cancelled) {
        return;
      }
      const built = buildCoverIntervals(unionSegments(verifiedMaps), {
        ...coverOptions,
        durationMs,
      });
      setSegments(built);
      setRejection(undefined);
      setBlockedReason(undefined);
      setStatus('verified');
    };

    void run();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [expectedSha256, publicKeyBase64, settings, durationMs, coverOptions]);

  // The schedule itself, on the harness that GATE 1 measured.
  const harness = useCoverHarness(mediaRef, {
    mode: status === 'verified' && ready ? 'timing' : 'off',
    intervals,
    foreground,
    ready,
    scheduleLabel: `flash-guard:${titleId}`,
  });

  const seekEngine = useMemo(
    () =>
      createSeekEngine({
        getIntervals: () => intervalsRef.current,
        getDurationMs: () => durationMs,
        setCover: (covered) => setSeekHolding(covered),
        seekTo: (targetMs) => {
          const element = mediaRef.current as
            | (MediaElementLike & { currentTime?: number })
            | null;
          if (element) {
            element.currentTime = targetMs / 1000;
          }
        },
        announce: (text) => announceForAccessibility(text),
      }),
    // A new engine per title, not per render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [durationMs, mediaRef, titleId],
  );

  // Feed the engine the positions the harness already computed, so a held
  // cover comes off only once playback is confirmed outside the interval.
  useEffect(() => {
    seekEngine.notePlayback(harness.mediaTimeMs);
  }, [harness.mediaTimeMs, seekEngine]);

  const covered =
    status !== 'verified' || !ready || harness.covered || seekHolding;

  const card = useMemo(
    () =>
      status === 'verified'
        ? cardAt(intervals, harness.mediaTimeMs)
        : cardAt([], 0, {
            rejection: rejection ?? 'missing',
            blockedDetail: blockedReason,
          }),
    [status, intervals, harness.mediaTimeMs, rejection, blockedReason],
  );

  // Say each card once, and never the same words twice in a row.
  const lastCard = useRef<Card>(NO_CARD);
  useEffect(() => {
    if (card.kind !== 'none' && cardChanged(lastCard.current, card)) {
      announceForAccessibility(card.announcement);
    }
    lastCard.current = card;
  }, [card]);

  // One log entry per interval that was actually covered.
  const loggedIntervals = useRef<Set<number>>(new Set());
  useEffect(() => {
    if (!covered || status !== 'verified') {
      return;
    }
    const interval = intervalAt(intervalsRef.current, harness.mediaTimeMs);
    if (!interval || loggedIntervals.current.has(interval.startMs)) {
      return;
    }
    loggedIntervals.current.add(interval.startMs);
    const durationCovered = interval.endMs - interval.startMs;
    setHiddenMs((previous) => previous + durationCovered);
    const cause: HideCause = seekHolding ? 'seek' : 'schedule';
    onHide?.({
      atMs: nowMs(),
      titleId,
      titleName,
      positionMs: interval.startMs,
      durationMs: durationCovered,
      cause,
      reason: interval.reason,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [covered, harness.mediaTimeMs, status]);

  const requestSeek = useCallback(
    (source: SeekSource, targetMs: number) => seekEngine.requestSeek(source, targetMs),
    [seekEngine],
  );

  const skipTo = useCallback(
    (targetMs: number) => {
      void seekEngine.requestSeek('seek-bar', targetMs);
    },
    [seekEngine],
  );

  return {
    status,
    rejection,
    blockedReason,
    covered,
    // Dim is only ever allowed for general segments, and only when the
    // pipeline's verify step modelled it. Nothing here opts into that yet, so
    // the cover is always opaque.
    coverMode: 'opaque',
    card,
    intervals,
    mediaTimeMs: harness.mediaTimeMs,
    hiddenMs,
    requestSeek,
    skipTo,
    seekEngine,
  };
}
