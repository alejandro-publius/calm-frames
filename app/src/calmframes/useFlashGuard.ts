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

import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { Image } from 'react-native';
import { announceForAccessibility } from './announce';
import { Card, cardAt, cardChanged, CHECKING_CARD, NO_CARD } from './cards';
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
import { HideCause, HideLogEntry } from './hideLog';
import {
  coverOptionsFor,
  DEFAULT_SETTINGS,
  HouseholdSettings,
  mapCoversRoom,
  PRESETS,
  unionSegments,
} from './household';
import { SceneHold, sceneHoldForInterval } from './sceneHolds';
import {
  createSeekEngine,
  SeekEngine,
  SeekPlan,
  SeekSource,
} from './seekSafety';
import { MediaElementLike, useCoverHarness } from './useCoverHarness';
import { trace } from './trace';

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
  /**
   * How far the rendition about to play sits from the source the map
   * describes, milliseconds, from the catalog entry's
   * `notes.rendition_start_offset_ms` for this preset.
   *
   * Left out it is treated as zero, which is right for a title that plays its
   * source. An offset larger than verify would publish means the map and the
   * file disagree, and the schedule refuses to build rather than put covers in
   * the wrong places.
   */
  renditionStartOffsetMs?: number;
  titleId?: string;
  titleName?: string;
  /** Injected so tests do not need a network and a device does not need one. */
  fetchText?: (url: string) => Promise<string | null>;
  /** Injected so tests can choose the time. */
  nowMs?: () => number;
  maxMapAgeMs?: number;
  /** Called once per cover, for the parent area's log. */
  onHide?: (entry: HideLogEntry) => void;
  /** Presentation copy for a labelled demo. Does not change timing or refusals. */
  cardCopy?: (
    card: Readonly<Card>,
  ) => Pick<Card, 'title' | 'detail' | 'announcement'>;
}

export interface FlashGuardState {
  status: GuardStatus;
  rejection?: MapRejection;
  /** Plain wording for why the picture is hidden, when it is not a segment. */
  blockedReason?: string;
  covered: boolean;
  coverMode: 'opaque' | 'dim';
  /** Only a checked still for the complete current scheduled interval. */
  coverImageUri?: string;
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
    const response = await fetch(url, {
      headers: { 'cache-control': 'no-cache' },
    });
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
    renditionStartOffsetMs,
    titleId = 'unknown',
    titleName = 'this title',
    fetchText = defaultFetchText,
    nowMs = Date.now,
    maxMapAgeMs,
    onHide,
    cardCopy,
  } = options;

  const [status, setStatus] = useState<GuardStatus>('loading');
  const [rejection, setRejection] = useState<MapRejection | undefined>(
    undefined,
  );
  const [blockedReason, setBlockedReason] = useState<string | undefined>(
    'Getting your story ready.',
  );
  const [segments, setSegments] = useState<CoverInterval[]>([]);
  const [seekHolding, setSeekHolding] = useState(false);
  const [hiddenMs, setHiddenMs] = useState(0);
  const [sceneHolds, setSceneHolds] = useState<SceneHold[]>([]);
  const [sceneSeekDisruptions, setSceneSeekDisruptions] = useState(0);

  // Bind a verified result to its actual map texts as well as the title. A
  // replacement map must start covered on the very render that receives it,
  // before the asynchronous check can finish. Compare primitive fields so an
  // inline mapTexts object does not restart verification on every render.
  const verificationInput = useMemo(
    () => ({
      wcagText: mapTexts?.wcag,
      broadcastText: mapTexts?.broadcast,
      wcagUrl: mapUrls?.wcag,
      broadcastUrl: mapUrls?.broadcast,
      expectedSha256,
      publicKeyBase64,
      titleId,
      preset: settings.preset,
      tvDiagonalIn: settings.tvDiagonalIn,
      seatDistanceIn: settings.seatDistanceIn,
      durationMs,
      renditionStartOffsetMs,
      maxMapAgeMs,
    }),
    [
      mapTexts?.wcag,
      mapTexts?.broadcast,
      mapUrls?.wcag,
      mapUrls?.broadcast,
      expectedSha256,
      publicKeyBase64,
      titleId,
      settings.preset,
      settings.tvDiagonalIn,
      settings.seatDistanceIn,
      durationMs,
      renditionStartOffsetMs,
      maxMapAgeMs,
    ],
  );
  const [checkedInput, setCheckedInput] = useState<object | null>(null);
  const activeStatus: GuardStatus =
    checkedInput === verificationInput ? status : 'loading';

  const coverOptions = useMemo(() => coverOptionsFor(settings), [settings]);

  const intervals = useMemo(() => segments, [segments]);
  const intervalsRef = useRef<CoverInterval[]>(intervals);
  intervalsRef.current = intervals;
  const committedSceneIntervalsRef = useRef<CoverInterval[]>(intervals);
  const presentedSceneIntervalRef = useRef<CoverInterval | undefined>(
    undefined,
  );
  const sceneBlackoutsRef = useRef({
    input: verificationInput,
    intervals: new Set<string>(),
    uncertaintyCount: -1,
    seekDisruptions: sceneSeekDisruptions,
  });
  const latchSceneInterval = useCallback((interval?: CoverInterval) => {
    if (interval) {
      sceneBlackoutsRef.current.intervals.add(
        `${interval.startMs}:${interval.endMs}`,
      );
    }
  }, []);
  const latchSceneAt = useCallback(
    (mediaTimeMs: number) => {
      // Preserve every interrupted interval for this map/title session, not
      // just the current playhead. Seeking back must not revive its still.
      latchSceneInterval(presentedSceneIntervalRef.current);
      latchSceneInterval(
        intervalAt(committedSceneIntervalsRef.current, mediaTimeMs),
      );
    },
    [latchSceneInterval],
  );

  // Load and check the maps. Anything that goes wrong leaves the picture
  // hidden and names a reason.
  useEffect(() => {
    let cancelled = false;
    const preset = PRESETS[settings.preset] ?? PRESETS.wcag;

    const run = async () => {
      setStatus('loading');
      setCheckedInput(null);
      setSceneHolds([]);
      setBlockedReason('Getting your story ready.');
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
          setCheckedInput(verificationInput);
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
          setCheckedInput(verificationInput);
          setRejection('missing');
          setBlockedReason(
            'This video is unavailable with your current viewing settings. The picture stays hidden.',
          );
          setSegments([]);
          return;
        }
        verifiedMaps.push(verdict.map);
      }
      if (cancelled) {
        return;
      }
      // Fail closed. An offset the schedule refuses means the map and the file
      // disagree about where the pictures are, and a schedule built anyway
      // would put covers in the wrong places, which is worse than not playing.
      let built;
      try {
        built = buildCoverIntervals(unionSegments(verifiedMaps), {
          ...coverOptions,
          durationMs,
          renditionStartOffsetMs,
        });
      } catch {
        if (cancelled) {
          return;
        }
        setStatus('blocked');
        setCheckedInput(verificationInput);
        setRejection('wrong-file');
        setBlockedReason(
          'The playback information belongs to a different version of this title. The picture stays hidden.',
        );
        setSegments([]);
        return;
      }
      setSegments(built);
      setSceneHolds(verifiedMaps.flatMap((map) => map.sceneHolds ?? []));
      setRejection(undefined);
      setBlockedReason(undefined);
      setStatus('verified');
      setCheckedInput(verificationInput);
    };

    void run();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [verificationInput]);

  // The schedule itself, on the harness that GATE 1 measured.
  const harness = useCoverHarness(mediaRef, {
    mode: activeStatus === 'verified' && ready ? 'timing' : 'off',
    intervals,
    foreground,
    ready,
    scheduleLabel: `flash-guard:${titleId}`,
    onUncertainty: latchSceneAt,
  });

  const seekEngine = useMemo(
    () =>
      createSeekEngine({
        getIntervals: () => intervalsRef.current,
        getDurationMs: () => durationMs,
        onPlan: (plan) => {
          latchSceneAt(plan.targetMs);
          latchSceneInterval(plan.interval);
          setSceneSeekDisruptions((count) => count + 1);
        },
        setCover: (covered, reason) => {
          trace('seek', JSON.stringify({ phase: 'cover-request', covered, reason }));
          setSeekHolding(covered);
        },
        seekTo: (targetMs) => {
          const element = mediaRef.current as
            | (MediaElementLike & { currentTime?: number })
            | null;
          if (element) {
            trace('seek', JSON.stringify({ phase: 'playhead-write', targetMs }));
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
    activeStatus !== 'verified' || !ready || harness.covered || seekHolding;
  const currentInterval = intervalAt(intervals, harness.mediaTimeMs);
  const blackout = sceneBlackoutsRef.current;
  const ownsBlackout = blackout.input === verificationInput;
  const disrupted =
    ownsBlackout &&
    ((blackout.uncertaintyCount >= 0 &&
      blackout.uncertaintyCount !== harness.uncertaintyCount) ||
      blackout.seekDisruptions !== sceneSeekDisruptions);
  // A checked static image can still flash if repeatedly removed and restored.
  // Any disruption therefore keeps this interval black for the whole session.
  const sceneIsLatchedBlack = currentInterval
    ? blackout.intervals.has(
        `${currentInterval.startMs}:${currentInterval.endMs}`,
      )
    : false;
  const coverImageUri =
    ownsBlackout &&
    !disrupted &&
    activeStatus === 'verified' &&
    ready &&
    foreground &&
    covered &&
    harness.covered &&
    !harness.uncertain &&
    !seekHolding &&
    !sceneIsLatchedBlack
      ? sceneHoldForInterval(
          sceneHolds,
          currentInterval,
          renditionStartOffsetMs,
        )?.imageDataUri
      : undefined;

  useLayoutEffect(() => {
    // Render can be abandoned by Suspense. Only a committed identity may
    // replace the one bounded owner or forget its interval history.
    if (sceneBlackoutsRef.current.input !== verificationInput) {
      sceneBlackoutsRef.current = {
        input: verificationInput,
        intervals: new Set<string>(),
        uncertaintyCount: -1,
        seekDisruptions: sceneSeekDisruptions,
      };
      presentedSceneIntervalRef.current = undefined;
    }
    committedSceneIntervalsRef.current = intervals;
    if (
      disrupted ||
      harness.uncertain ||
      seekHolding ||
      !foreground ||
      !ready
    ) {
      latchSceneAt(harness.mediaTimeMs);
    }
    const committed = sceneBlackoutsRef.current;
    committed.uncertaintyCount = harness.uncertaintyCount;
    committed.seekDisruptions = sceneSeekDisruptions;
    presentedSceneIntervalRef.current = coverImageUri
      ? currentInterval
      : undefined;
  }, [
    verificationInput,
    intervals,
    currentInterval,
    coverImageUri,
    disrupted,
    harness.uncertain,
    harness.uncertaintyCount,
    harness.mediaTimeMs,
    sceneSeekDisruptions,
    seekHolding,
    foreground,
    ready,
    latchSceneAt,
  ]);

  const prefetchedImages = useRef<Set<string>>(new Set());
  useEffect(() => {
    prefetchedImages.current.clear();
  }, [verificationInput]);
  useEffect(() => {
    if (
      activeStatus !== 'verified' ||
      !ready ||
      typeof Image.prefetch !== 'function'
    ) {
      return;
    }
    const next = intervals.find(
      (interval) => interval.endMs > harness.mediaTimeMs,
    );
    const uri = sceneHoldForInterval(
      sceneHolds,
      next,
      renditionStartOffsetMs,
    )?.imageDataUri;
    if (uri && !prefetchedImages.current.has(uri)) {
      prefetchedImages.current.add(uri);
      // An unsupported prefetch or a failed decode leaves the opaque black
      // backing in charge. Preloading is never evidence that a still is safe.
      try {
        Image.prefetch(uri).catch(() => {});
      } catch {
        // Some device builds have no prefetch implementation.
      }
    }
  }, [
    activeStatus,
    ready,
    intervals,
    harness.mediaTimeMs,
    sceneHolds,
    renditionStartOffsetMs,
  ]);

  const scheduledCard = useMemo(() => {
    if (activeStatus === 'verified') {
      return cardAt(intervals, harness.mediaTimeMs);
    }
    // Still checking is not a refusal. The refusal card would say "Not
    // checked yet", or repeat why the previous map was turned away, about a
    // check that has not finished. The picture is hidden either way, because
    // covered above never looks at the card.
    if (activeStatus === 'loading') {
      return CHECKING_CARD;
    }
    return cardAt([], 0, {
      rejection: rejection ?? 'missing',
      blockedDetail: blockedReason,
    });
  }, [activeStatus, intervals, harness.mediaTimeMs, rejection, blockedReason]);
  const card = useMemo(() => {
    if (!cardCopy || activeStatus !== 'verified') {
      return scheduledCard;
    }
    const copy = cardCopy(scheduledCard);
    return {
      ...scheduledCard,
      title: copy.title,
      detail: copy.detail,
      announcement: copy.announcement,
    };
  }, [scheduledCard, cardCopy, activeStatus]);

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
    if (!covered || activeStatus !== 'verified') {
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
  }, [covered, harness.mediaTimeMs, activeStatus]);

  const requestSeek = useCallback(
    (source: SeekSource, targetMs: number) =>
      seekEngine.requestSeek(source, targetMs),
    [seekEngine],
  );

  const skipTo = useCallback(
    (targetMs: number) => {
      void seekEngine.requestSeek('seek-bar', targetMs);
    },
    [seekEngine],
  );

  return {
    status: activeStatus,
    rejection,
    blockedReason,
    covered,
    // Dim is only ever allowed for general segments, and only when the
    // pipeline's verify step modelled it. Nothing here opts into that yet, so
    // the cover is always opaque.
    coverMode: 'opaque',
    coverImageUri,
    card,
    intervals,
    mediaTimeMs: harness.mediaTimeMs,
    hiddenMs,
    requestSeek,
    skipTo,
    seekEngine,
  };
}
