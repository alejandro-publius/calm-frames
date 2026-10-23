import { nativeRetryProbe } from '../calmframes/nativeRetryProbe';
import RecoverablePlayback, { RecoveryBinding } from '../calmframes/RecoverablePlayback';
import { validateCheckpointIdentity, checkpointIdentityKey } from '../calmframes/playbackCheckpoint';
import { recoverPlayback, RecoveryPhase } from '../calmframes/playbackRecovery';
import { restoreCaptionChoice, usePlaybackMemory } from '../calmframes/usePlaybackMemory';
import CalmButton from '../calmframes/CalmButton';
import AmbientScene, { AmbientArtwork } from '../calmframes/AmbientScene';
import { continuousEndingForRoute } from '../calmframes/continuousScene';
import { bakedAmbientForRendition } from '../calmframes/approvedBakedAmbient';
import { mayShowBakedAmbient } from '../calmframes/bakedAmbient';
import { ambientCoverPredecessor, combineAmbientCovers } from '../calmframes/ambientPersonalCovers';
import {
  ContentPersonalizationServer,
  PlaybackState,
} from '@amazon-devices/kepler-content-personalization';
import {
  BackHandler,
  IComponentInstance,
  IKeplerAppStateManager,
  KeplerAppStateChangeData,
  KeplerAppStateEvent,
  useKeplerAppStateManager,
} from '@amazon-devices/react-native-kepler';
import {
  KeplerCaptionsView,
  KeplerVideoSurfaceView,
  VideoPlayer,
} from '@amazon-devices/react-native-w3cmedia';
import isEqual from 'lodash/isEqual';
import React, { useCallback, useEffect, useRef } from 'react';
import ErrorView from '../components/ErrorView';
import PlayerOpening from '../calmframes/PlayerOpening';
import useOpeningFrame from '../calmframes/useOpeningFrame';
import { focusManager } from '../utils/FocusManager';

import { SafeAreaView } from '@amazon-devices/react-native-safe-area-context';
import { RouteProp } from '@amazon-devices/react-navigation__core';
import { StackNavigationProp } from '@amazon-devices/react-navigation__stack';
import {
  AppStateStatus,
  Platform,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from 'react-native';
import CalmCard from '../calmframes/CalmCard';
import { CoastalAppearance } from '../calmframes/CoastalAppearance';
import { trace } from '../calmframes/trace';
import { bundledStillFor } from '../calmframes/bundledStills';
import { CALM_COLORS } from '../calmframes/calmStyles';
import { concernsPackagedLibrary, packagedLibrary } from '../calmframes/packagedLibrary';
import {
  benignStoryCard,
  BENIGN_STORY_LABEL,
  bundledTitlePublicKey,
  isBundledBenignStory,
} from '../calmframes/benignStory';
import { cardOffersSkip, NO_CARD } from '../calmframes/cards';
import { playChime } from '../calmframes/chimeSound';
import CornerPlate from '../calmframes/CornerPlate';
import CoverLayer from '../calmframes/CoverLayer';
import {
  showDefaultCaptions,
  TextTrackListLike,
} from '../calmframes/defaultCaptions';
import { buildCoverIntervals } from '../calmframes/coverSchedule';
import { recordHide } from '../calmframes/hideLogStore';
import { OFFLINE_PUBLIC_KEY_BASE64 } from '../calmframes/offlineTitle';
import {
  mustStayHidden,
  playbackAccess,
  UNGUARDED_CARD,
} from '../calmframes/playerAccess';
import { SafeMediaControlHandler } from '../calmframes/SafeMediaControlHandler';
import { beacon } from '../calmframes/timingLog';
import { useUiCapture } from '../calmframes/uiCapture';
import { playerFrame } from '../calmframes/uiFrames';
import { useChimeCue } from '../calmframes/useChimeCue';
import { useCoverHarness } from '../calmframes/useCoverHarness';
import { scale } from '../calmframes/calmStyles';
import { playbackCard, usePlaybackCardAnnouncement, usePlaybackPaused } from '../calmframes/usePlaybackPresentation';
import { usePlaybackProgress } from '../calmframes/usePlaybackProgress';
import { useFlashGuard } from '../calmframes/useFlashGuard';
import { sceneBridgesForAsset } from '../calmframes/approvedSceneBridges';
import { resolveSceneBridge } from '../calmframes/sceneBridges';
import { personalCoverAsset } from '../calmframes/personalCovers';
import { usePersonalCovers } from '../calmframes/personalCoverStorage';
import BufferingWindow from '../components/BufferingWindow';
import {
  AppStackParamList,
  AppStackScreenProps,
  Screens,
} from '../components/navigation/types';
import { isContentPersonalizationEnabled } from '../config/AppConfig';
import { CAPTION_DISABLE_ID } from '../constants';
import { getMockPlaybackEventForVideo } from '../personalization/mock/ContentPersonalizationMocks';
import { getBifFrameImageSource } from '../services/bif/bifService';
import { FrameImageSource } from '../services/bif/FrameImageSource';
import { COLORS } from '../styles/Colors';
import { VideoHandler } from '../utils/VideoHandler';
import VideoPlayerUI from '../w3cmedia/mediacontrols/VideoPlayerUI';
import { ShakaPlayer } from '../w3cmedia/shakaplayer/ShakaPlayer';

const BACKGROUND_STATE: AppStateStatus = 'background';

interface PlayerProps {
  navigation: StackNavigationProp<AppStackParamList, Screens.PLAYER_SCREEN>;
  route: RouteProp<AppStackParamList, Screens.PLAYER_SCREEN>;
}

export const PlayerScreen = ({
  navigation,
  route,
  recovery,
}: AppStackScreenProps<Screens.PLAYER_SCREEN> & { recovery?: RecoveryBinding }) => {
  const { data } = route.params;
  // Calm Frames cover harness. "layering" is the phase 1.5 check and "timing"
  // is the GATE 1 harness; without the parameter the player behaves exactly as
  // the sample did. See docs/GATES.md for how to run each one.
  const coverTest = route.params.coverTest ?? 'off';
  const coverIntervals = React.useMemo(
    () =>
      route.params.coverSegments
        ? buildCoverIntervals(route.params.coverSegments, {
            guardBandMs: route.params.guardBandMs,
          })
        : [],
    [route.params.coverSegments, route.params.guardBandMs],
  );
  const { width: deviceWidth, height: deviceHeight } = useWindowDimensions();
  const addKeplerAppStateListenerCallback = (
    eventType: KeplerAppStateEvent,
    handler: (state: KeplerAppStateChangeData) => void,
  ) => keplerAppStateManager.addAppStateListener(eventType, handler);
  const [showBuffering, setShowBuffering] = React.useState<boolean>(true);

  // After media initialization once media loads isVideoInitialized will change to true.
  const [isVideoInitialized, setIsVideoInitialized] =
    React.useState<boolean>(false);
  const [frameGeneration, setFrameGeneration] = React.useState(0);
  const surfaceGeneration = useRef(0);
  const [surfaceReady, setSurfaceReady] = React.useState(false);
  const [returningHome, setReturningHome] = React.useState(false);
  React.useEffect(() => { trace('screen', 'player'); return () => trace('screen', 'player-left'); }, []);
  const surfaceHandle = useRef<string | null>(null);
  const captionViewHandle = useRef<string | null>(null);

  const captionStatus = useRef<boolean | null>(null);
  const setCaptionStatus = (status: boolean) => {
    captionStatus.current = status;
  };
  const captionsDefaulted = useRef(false);
  const [captionID, setCaptionID] = React.useState<string>(CAPTION_DISABLE_ID);
  const setSelectedCaptionInVideoPlayer = (id: string) => {
    captionsDefaulted.current = true; // A user choice always wins over initialization.
    setCaptionID(id);
  };
  const [isVideoEnded, setVideoEnded] = React.useState<boolean>(false);
  const [isVideoError, setVideoError] = React.useState<boolean>(false);
  const [videoPlayElapsedTimeM, setVideoPlayElapsedTimeM] =
    React.useState<number>(0);
  const exitTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const leaving = useRef(false);
  const mounted = useRef(true);
  const [recoveryPhase, setRecoveryPhase] = React.useState<RecoveryPhase>(recovery?.start ? 'covered' : 'ready');
  const [recoveryCoverMounted, setRecoveryCoverMounted] = React.useState(false);
  const [retryBlocked, setRetryBlocked] = React.useState(false);
  const [probeUsed, setProbeUsed] = React.useState(nativeRetryProbe.used());
  const [probeReady, setProbeReady] = React.useState(false);
  const [retryClosing, setRetryClosing] = React.useState(false);
  const retryRelease = useRef<{generation: number; confirmed: boolean} | null>(null);
  const retryGeneration = useRef(0);
  const recoveryAttempt = useRef<ReturnType<typeof recoverPlayback> | null>(null);
  const recoveryStarted = useRef(false);
  const recoveryPending = Boolean(recovery?.start && recoveryPhase !== 'ready');

  const videoRef = useRef<VideoPlayer | null>(null);
  const player = useRef<ShakaPlayer | null>(null);
  const bifFrameImagesRef = useRef<FrameImageSource | null>(null);

  const BACK_NAVIGATION_DELAY = 700;
  const showVideoPlayerUI = !isVideoError && !isVideoEnded && !returningHome;
  const paused = usePlaybackPaused(videoRef, isVideoInitialized);

  React.useEffect(() => {
    beacon('PlayerScreen.mount', { coverTest, uri: route.params.data?.uri });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  React.useEffect(() => {
    beacon('PlayerScreen.videoInitialized', { isVideoInitialized });
  }, [isVideoInitialized]);

  // Apply the title's initial caption default once; then the menu decides.
  // Ambient Harbor descriptions start Off. VideoHandler adds the
  // title's tracks before the media loads, so they exist by the time the
  // player says it is initialized. See defaultCaptions.ts.
  React.useEffect(() => {
    if (!isVideoInitialized || captionsDefaulted.current) {
      return;
    }
    captionsDefaulted.current = true;
    const tracks = videoRef.current?.textTracks as TextTrackListLike | undefined;
    const restored = recovery?.start ? restoreCaptionChoice(tracks, recovery.start.captions) : null;
    const shown = restored ?? showDefaultCaptions(tracks, data.textTrack, data.id);
    if (shown !== CAPTION_DISABLE_ID) {
      console.log(
        `[PlayerScreen.tsx] - captions - on by default, track ${shown}`,
      );
      setCaptionID(shown);
    }
  }, [isVideoInitialized, data.textTrack, data.id, recovery?.start]);

  const cover = useCoverHarness(videoRef, {
    mode: coverTest,
    intervals: coverIntervals,
    toggleEveryMs: route.params.toggleEveryMs,
    scheduleLabel: route.params.scheduleLabel,
    ready: isVideoInitialized,
  });

  // Kid mode. The guard checks the map again here, right before play, so a
  // title that passed on the shelf cannot play on a map that has since gone
  // missing or gone stale.
  const preparedRoute = concernsPackagedLibrary(data);
  const preparedRouteAccepted = preparedRoute && packagedLibrary.acceptsRoute(data, route.params.guarded);
  const rejectedPreparedRoute = preparedRoute && !preparedRouteAccepted;
  const guardedParams = rejectedPreparedRoute ? undefined : route.params.guarded;
  const continuousEnding = continuousEndingForRoute(data, guardedParams);
  const bundledIdentity = {
    id: data.id,
    uri: data.uri,
    sha256: guardedParams?.sha256,
  };
  const benignDemo = isBundledBenignStory(bundledIdentity);
  const extraCoverAsset = personalCoverAsset({
    id: guardedParams?.titleId ?? data.id, sha256: guardedParams?.sha256,
    renditionSha256: guardedParams?.renditionSha256,
    durationMs: guardedParams?.durationMs,
    renditionStartOffsetMs: guardedParams?.renditionStartOffsetMs,
  });
  const ambientDocument = preparedRouteAccepted
    ? bakedAmbientForRendition(extraCoverAsset?.renditionSha256, guardedParams?.settings?.preset) : null;
  const predecessor = ambientCoverPredecessor(ambientDocument, extraCoverAsset, guardedParams?.settings);
  const currentCovers = usePersonalCovers(preparedRouteAccepted ? extraCoverAsset : undefined);
  const predecessorCovers = usePersonalCovers(predecessor.asset);
  const predecessorStatus = predecessor.status;
  const predecessorKey = predecessor.asset?.renditionSha256;
  const extraCovers = React.useMemo(() => combineAmbientCovers(currentCovers, predecessorCovers, predecessor),
    // Stable records keep the guard from restarting verification on each playback tick.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [currentCovers.status, currentCovers.record, predecessorCovers.status, predecessorCovers.record,
      predecessorStatus, predecessorKey]);
  const guard = useFlashGuard({
    additionalCovers: preparedRouteAccepted ? extraCovers.record?.additions : undefined,
    personalCoversStatus: preparedRouteAccepted
      ? extraCoverAsset ? extraCovers.status : 'blocked'
      : 'ready',
    announceCards: false,
    mediaRef: videoRef,
    mapTexts: guardedParams?.maps,
    mapUrls: guardedParams?.mapUrls,
    expectedSha256: guardedParams?.sha256 ?? '',
    publicKeyBase64: preparedRouteAccepted ? packagedLibrary.publicKeyForRoute(data, guardedParams) ?? '' : bundledTitlePublicKey(
      bundledIdentity,
      OFFLINE_PUBLIC_KEY_BASE64,
    ),
    cardCopy: benignDemo ? benignStoryCard : undefined,
    settings: guardedParams?.settings,
    durationMs: guardedParams?.durationMs,
    // How far the rendition about to play sits from the source the map
    // describes. The bundled Harbor demo plays its pre-covered rendition,
    // whose verification.json records an offset of 0 for every preset, so
    // nothing is passed for it.
    renditionStartOffsetMs: guardedParams?.renditionStartOffsetMs,
    titleId: guardedParams?.titleId ?? data.id,
    titleName: data.title,
    ready: isVideoInitialized && Boolean(guardedParams),
    // One line in the parent area per cover this player put on. The guard
    // fires this once per interval it actually covered; everything added here
    // is what the guard has no way of knowing: whose sitting it was and which
    // preset the schedule was built under.
    onHide: (entry) => {
      // Practice holds are disclosed demonstrations, not family exposure history.
      if (benignDemo) {
        return;
      }
      recordHide(entry, {
        profileId: guardedParams?.profileId,
        profileName: guardedParams?.profileName,
        preset: guardedParams?.settings?.preset,
      });
    },
  });
  const memory = usePlaybackMemory({identity: recovery?.identity, initial: recovery?.start,
    media: videoRef, initialized: isVideoInitialized, verified: guard.status === 'verified',
    enabled: !isVideoError && !showBuffering && !recoveryPending && !leaving.current,
    ended: isVideoEnded});
  const recoveryCurrent = useRef(false);
  recoveryCurrent.current = guard.status === 'verified' && surfaceReady && !leaving.current && !isVideoError;
  useEffect(() => {
    const media = videoRef.current;
    if (!recovery?.start || recoveryStarted.current || !media || !isVideoInitialized ||
        !surfaceReady || !recoveryCoverMounted || guard.status !== 'verified') return;
    recoveryStarted.current = true;
    recoveryAttempt.current = recoverPlayback({media, positionMs: recovery.start.positionMs,
      paused: recovery.start.paused,
      current: () => recoveryCurrent.current && videoRef.current === media && !leaving.current,
      presentCover: async () => { /* The opaque view's onLayout has already fired. */ },
      seek: position => guard.requestSeek('recovery', position),
      phase: next => {
        if (leaving.current) return;
        setRecoveryPhase(next);
        trace('playback', `recovery ${next}`);
        if (next === 'failed') setVideoError(true);
      }});
    // Each keyed player instance owns exactly one explicit recovery attempt.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isVideoInitialized, surfaceReady, recoveryCoverMounted, guard.status]);
  useEffect(() => () => { recoveryAttempt.current?.cancel(); }, []);
  useEffect(() => {
    if (recoveryPending && guard.status === 'blocked') {
      recoveryAttempt.current?.cancel(); setVideoError(true);
    }
  }, [recoveryPending, guard.status]);
  // The courtesy sound. useChimeCue decides whether a chime is owed and
  // refuses to raise one that no cover follows, so everything this call does is
  // hand it the numbers the guard already reports and a way to make a noise.
  // chimeSound swallows every audio failure, so a machine with no audio path
  // plays nothing and the title is unaffected.
  useChimeCue({
    intervals: guard.intervals,
    mediaTimeMs: guard.mediaTimeMs,
    covered: guard.covered,
    verified: guard.status === 'verified',
    enabled: guardedParams?.chimeEnabled !== false && !recoveryPending,
    playChime,
    titleId: guardedParams?.titleId ?? data.id,
  });

  // Three answers, and only three: the guard is running, a measurement
  // harness is running, or the picture stays hidden. playerAccess.ts says why
  // this is decided here rather than trusted to whoever navigated.
  const access = playbackAccess({
    guarded: guardedParams,
    coverTest: rejectedPreparedRoute ? 'off' : coverTest,
  });
  const guarding = access === 'guarded';
  const lineage = preparedRouteAccepted && guardedParams?.settings
    ? packagedLibrary.titles(guardedParams.settings).find(title => title.id === data.id)
    : undefined;
  const playbackEvidence = lineage && guardedParams?.settings
    ? packagedLibrary.evidenceFor(lineage, guardedParams.settings) : null;
  const evidenceTrace = playbackEvidence ? JSON.stringify(playbackEvidence) : null;
  React.useEffect(() => {
    if (guarding && guard.status === 'verified' && evidenceTrace) {
      trace('prepared-playback', evidenceTrace);
    }
  }, [guarding, guard.status, evidenceTrace]);

  const homeOpening = (recovery?.start ? recoveryPending : route.params.showHomeOpening === true) && guarding && !isVideoError && guard.status !== 'blocked';
  const openingFrameReady = useOpeningFrame({ media: videoRef, enabled: homeOpening && !returningHome,
    verified: guard.status === 'verified' && !recoveryPending, surfaceReady, frameGeneration, onTimeout: () => setVideoError(true) });
  const showOpeningShell = Boolean(homeOpening && !openingFrameReady || returningHome && route.params.showHomeOpening);
  // The measurement harness and the guard never run at once: a run is a
  // measurement, kid mode is the product.
  let covered = cover.covered;
  let card = NO_CARD;
  if (guarding) {
    covered = guard.covered;
    card = guard.card;
  } else if (mustStayHidden(access)) {
    covered = true;
    card = rejectedPreparedRoute
      ? {
          ...UNGUARDED_CARD,
          detail: 'This video cannot be opened. Go back to the library.',
          announcement: 'This video is unavailable. Go back to the library.',
        }
      : UNGUARDED_CARD;
  }
  // A failed player has no advancing timeline. Keep its picture hidden and
  // remove the stale countdown/Skip control above the recovery screen.
  if (isVideoError || recoveryPending) {
    covered = true;
    card = NO_CARD;
  }
  const slowPlayback = usePlaybackProgress(videoRef, isVideoInitialized && !showOpeningShell &&
    !paused && !showBuffering && !isVideoEnded && !isVideoError && !returningHome &&
    (!guarding || guard.status === 'verified'));
  const retryAvailable = Boolean(!showOpeningShell && slowPlayback && !isVideoError &&
    !retryBlocked && recovery && memory.last.current);
  const calmCoverFallback = guarding && guard.status === 'verified' && card.kind === 'covering';
  const sceneBridge = preparedRouteAccepted && extraCoverAsset &&
    guard.scheduledCover && !paused && !showBuffering && !isVideoEnded &&
    !isVideoError && !returningHome && !showOpeningShell
    && !recoveryPending ? resolveSceneBridge(sceneBridgesForAsset(extraCoverAsset), extraCoverAsset,
        guard.baseIntervals, guard.mediaTimeMs)
    : undefined;
  const bakedAmbientVisible = mayShowBakedAmbient(
    ambientDocument, extraCoverAsset,
    guardedParams?.settings?.preset, playbackEvidence?.maps ?? [], guard.baseIntervals,
    guard.mediaTimeMs, { acceptedPreparedRoute: preparedRouteAccepted, verified: guard.status === 'verified',
      scheduledCover: guard.scheduledCover, buffering: showBuffering || slowPlayback,
      paused, opening: showOpeningShell || recoveryPending, returning: returningHome, ended: isVideoEnded, error: isVideoError,
      personalCoversReady: extraCovers.status === 'ready', personalCoverCount: extraCovers.record?.additions.length ?? -1 });
  card = playbackCard(card, { paused, covered, buffering: showBuffering, slow: slowPlayback,
    ended: isVideoEnded, practice: benignDemo, oceanVisible: bakedAmbientVisible });
  usePlaybackCardAnnouncement(showOpeningShell ? NO_CARD : card, paused);
  const coverPresentation = bakedAmbientVisible ? 'baked-ambient' : !covered ? 'clear' : guard.coverImageUri ? 'signed-still' : calmCoverFallback ? 'message' : 'plain';
  useEffect(() => { trace('playback', `cover-surface ${coverPresentation}`); }, [coverPresentation]);
  // Debug-build breadcrumbs (CALM_TRACE, see trace.ts) so one native run can
  // separate the phases from the device log alone: the first picture, each
  // cover and each wait with its media time, then Back and teardown. They
  // fire on state changes only, never per tick, and carry no personal data.
  const traceMediaMs = useRef(0);
  traceMediaMs.current = guard.mediaTimeMs;
  useEffect(() => {
    if (openingFrameReady) trace('playback', `picture-shown media=${Math.round(traceMediaMs.current)}`);
  }, [openingFrameReady]);
  useEffect(() => {
    trace('playback', `cover ${covered ? 'on' : 'off'} media=${Math.round(traceMediaMs.current)}`);
  }, [covered]);
  useEffect(() => {
    if (isVideoInitialized) trace('playback', `waiting ${showBuffering ? 'on' : 'off'} media=${Math.round(traceMediaMs.current)}`);
  }, [showBuffering, isVideoInitialized]);
  useEffect(() => {
    trace('playback', `slow ${slowPlayback ? 'on' : 'off'} media=${Math.round(traceMediaMs.current)}`);
  }, [slowPlayback]);
  // The app records its own layer, because Vega gives it no way to read its
  // pixels back. tools/ui_flashmap.mjs runs flashmap over what this records.
  useUiCapture(
    React.useMemo(
      () => playerFrame(covered, card.kind, benignDemo),
      [covered, card.kind, benignDemo],
    ),
    'player',
  );
  const keplerAppStateManager: IKeplerAppStateManager =
    useKeplerAppStateManager();
  const componentInstance: IComponentInstance =
    keplerAppStateManager.getComponentInstance();

  // Alexa and the remote's transport commands arrive through Vega Media
  // Controls. In kid mode they go to SafeMediaControlHandler, which sends
  // every one of them through the same seek function the on-screen controls
  // use, so a spoken "skip forward" cannot land inside a flagged part with the
  // picture showing.
  const transportReady = useRef(false);
  transportReady.current = !recoveryPending && !isVideoError;
  const mediaControlHandler = React.useMemo(
    () =>
      guarding
        ? new SafeMediaControlHandler({
            engine: guard.seekEngine,
            getCurrentMs: () => (videoRef.current?.currentTime ?? 0) * 1000,
            getPaused: () => videoRef.current?.paused,
            canControl: () => !leaving.current && transportReady.current,
            onBlockedPause: () => { recoveryAttempt.current?.cancel(); if (!leaving.current) setVideoError(true); },
          })
        : undefined,
    [guarding, guard.seekEngine],
  );

  const handlerRef = useRef<VideoHandler | null>(null);
  if (!handlerRef.current) handlerRef.current = new VideoHandler(
    videoRef,
    player,
    data,
    setIsVideoInitialized,
    setVideoEnded,
    setVideoError,
    setVideoPlayElapsedTimeM,
    setShowBuffering,
    mediaControlHandler,
  );
  const videoHandler = handlerRef.current;
  videoHandler.mediaControlHandler = mediaControlHandler;

  useEffect(() => {
    setupEventListeners();
    if (rejectedPreparedRoute) {
      setShowBuffering(false);
    } else {
      console.log(
        '[PlayerScreen.tsx] - Initialize media player: componentInstance',
        componentInstance,
      );
      console.log(
        '[PlayerScreen.tsx] - Video Handler invoke preBufferVideo',
        videoHandler.data,
      );
      videoHandler.preBufferVideo(componentInstance);
    }
    const changeSubscription = addKeplerAppStateListenerCallback(
      'change',
      handleAppStateChange,
    );
    return () => {
      changeSubscription.remove();
      removeEventListeners();
      // Restore focus when leaving player screen
      if (route.params.focusId) {
        const focusKey = `player_return_${route.params.focusId}`;
        focusManager.restoreFocus(focusKey);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (isVideoError) {
      setShowBuffering(false);
    }
  }, [isVideoError]);

  /**
   * Function to report the video player screen exit.
   */
  const reportVideoExit = () => {
    if (!isContentPersonalizationEnabled()) {
      return;
    }

    try {
      console.info(
        '[PlayerScreen.tsx] - reportVideoExit - k_content_per: Creating playbackEvent object on exit',
      );
      const playbackEvent = getMockPlaybackEventForVideo(
        videoRef,
        videoRef.current!.currentSrc,
        PlaybackState.EXIT,
      );
      ContentPersonalizationServer.reportNewPlaybackEvent(playbackEvent);
      console.info(
        `[PlayerScreen.tsx] - reportVideoexit - k_content_per: Exit : Reporting new playback event :${JSON.stringify(
          playbackEvent,
        )}`,
      );
    } catch (e) {
      console.error(
        `[PlayerScreen.tsx] - reportVideoexit - k_content_per: ${e}`,
      );
    }
  };

  const releaseNativePlayer = (): Promise<boolean> => {
    if (!videoRef.current) {
      // Invalidate pending initialization even before a decoder exists.
      videoHandler.destroyVideoElements();
      return Promise.resolve(true);
    }
    return videoHandler.destroyVideoElementsConfirmed();
  };

  useEffect(() => {
    return () => {
      memory.close();
      mounted.current = false;
      leaving.current = true;
      retryGeneration.current += 1;
      recoveryAttempt.current?.cancel();
      surfaceGeneration.current += 1;
      /**
       * When the player is unmounted we check if the instance was destroyed correctly,
       * if not, it is destroyed (commonly used with integrations like EPG).
       */
      surfaceHandle.current = null;
      captionViewHandle.current = null;
      releaseNativePlayer();
      videoRef.current = null;

      if (exitTimer.current !== null) {
        clearTimeout(exitTimer.current);
      }

      if (bifFrameImagesRef) {
        bifFrameImagesRef.current?.clearCache();
        bifFrameImagesRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const leavePlayer = useCallback(() => {
    if (leaving.current) {
      return true;
    }
    memory.capture();
    memory.close();
    leaving.current = true;
    recoveryAttempt.current?.cancel();
    surfaceGeneration.current += 1;
    retryGeneration.current += 1;
    trace('playback', 'back');
    if (route.params.showHomeOpening) setReturningHome(true);

    if (videoRef.current) reportVideoExit();

    surfaceHandle.current = null;
    captionViewHandle.current = null;
    const release = releaseNativePlayer();
    videoRef.current = null;
    let returned = false;
    const returnOnce = () => {
      if (returned || !mounted.current) return;
      returned = true;
      if (exitTimer.current !== null) clearTimeout(exitTimer.current);
      navigation.goBack();
    };
    // Back may leave for a static screen while native teardown finishes. The
    // process-wide creation barrier still forbids any replacement decoder.
    exitTimer.current = setTimeout(returnOnce, BACK_NAVIGATION_DELAY);
    release.then(confirmed => {
      trace('playback', confirmed ? 'teardown ok' : 'teardown unconfirmed');
      if (confirmed) returnOnce();
    });
    return true;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Optional short previews end on stationary artwork until explicit Back.
  // Legacy diagnostic/demo routes retain their existing teardown behavior.
  useEffect(() => {
    if (isVideoEnded) {
      memory.close();
      trace('playback', 'ended');
      if (!route.params.ambientPreview && !continuousEnding) {
        leavePlayer();
      } else {
        // Release native transport focus as well as the visible surface. A
        // finished preview must not restart audio beneath the still scene.
        surfaceGeneration.current += 1;
        if (videoRef.current) reportVideoExit();
        releaseNativePlayer();
        videoRef.current = null;
        surfaceHandle.current = null;
        captionViewHandle.current = null;
      }
    }
    // The handler owns the stable media refs for this mounted route.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isVideoEnded, leavePlayer, route.params.ambientPreview, continuousEnding]);

  const navigateBack = useCallback(() => {
    if (captionStatus.current) {
      captionStatus.current = false;
      return true;
    }
    return leavePlayer();
  }, [leavePlayer]);

  const handleAppStateChange = useCallback(
    (nextAppState: KeplerAppStateChangeData): void => {
      // A line for every change, and one for what the player did about it,
      // so a device log shows each state the app passed through. console.log,
      // which the Release build strips.
      console.log(
        `[PlayerScreen.tsx] - handleAppStateChange - KeplerAppStateChange to ${String(
          nextAppState,
        )}`,
      );
      if (nextAppState === BACKGROUND_STATE) {
        setShowBuffering(false);
        if (coverTest !== 'off') {
          // A measurement run stays on this screen. The virtual device
          // backgrounds an app that nobody is touching, and leaving the
          // screen would tear the player down mid-run. The cover is already
          // on: useCoverHarness hides the picture as soon as the playhead
          // becomes uncertain, which includes going to the background.
          console.log(
            '[PlayerScreen.tsx] - handleAppStateChange - background, a measurement run stays on the player',
          );
          return;
        }
        console.log(
          '[PlayerScreen.tsx] - handleAppStateChange - background, leaving the player',
        );
        leavePlayer();
      }
    },
    [leavePlayer, coverTest],
  );

  const backHandlerSubscription = useRef<{ remove: () => void } | null>(null);

  const setupEventListeners = useCallback(() => {
    if (Platform.isTV) {
      backHandlerSubscription.current = BackHandler.addEventListener(
        'hardwareBackPress',
        navigateBack,
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [Platform.isTV]);

  const removeEventListeners = useCallback(() => {
    if (Platform.isTV) {
      backHandlerSubscription.current?.remove();
      backHandlerSubscription.current = null;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [Platform.isTV]);

  const reportVideoPlaying = useCallback(() => {
    if (!isContentPersonalizationEnabled()) {
      return;
    }
    try {
      const playbackEvent = getMockPlaybackEventForVideo(
        videoRef,
        videoRef.current!.currentSrc,
        PlaybackState.PLAYING,
      );
      console.info(
        `[PlayerScreen.tsx] - reportVideoPlaying -  k_content_per: Reported playback event : ${JSON.stringify(
          playbackEvent,
        )}`,
      );
      ContentPersonalizationServer.reportNewPlaybackEvent(playbackEvent);
    } catch (e) {
      console.error(
        `[PlayerScreen.tsx] - reportVideoPlaying -  k_content_per: ${e}`,
      );
    }
  }, [videoRef]);

  useEffect(() => {
    if (videoPlayElapsedTimeM === 0) {
      return;
    }
    console.info(
      '[PlayerScreen.tsx] - reportVideoPlaying - k_content_per: Reporting playback event for Continued PLAYING',
    );

    reportVideoPlaying();
  }, [reportVideoPlaying, videoPlayElapsedTimeM]);

  const playVideo = useCallback(async () => {
    try {
      // Hide buffer view and Play the video if allowed...
      await videoRef?.current?.play();
      setShowBuffering(false);
      console.debug(
        '[PlayerScreen.tsx] - playVideo -  Video playing successfully',
      );
      console.info(
        '[PlayerScreen.tsx] - playVideo - k_content_per: Reporting new playback event',
      );
      reportVideoPlaying();
    } catch (error) {
      console.error(
        '[PlayerScreen.tsx] - playVideo - Error occurred while playing video {}',
        error,
      );
      leavePlayer();
    }
  }, [videoRef, leavePlayer, reportVideoPlaying]);

  const setSurface = useCallback(async () => {
    const handle = surfaceHandle.current;
    const media = videoRef.current;
    const generation = surfaceGeneration.current;
    if (!handle || !media || leaving.current) return;
    media.setSurfaceHandle(handle);
    const current = () => !leaving.current && videoRef.current === media &&
      surfaceHandle.current === handle && surfaceGeneration.current === generation;
    try {
      if (data?.bifUrl) {
        const frames = await getBifFrameImageSource(data.bifUrl);
        if (!current()) { frames?.clearCache(); return; }
        bifFrameImagesRef.current?.clearCache();
        bifFrameImagesRef.current = frames;
      }
      if (current() && !recovery?.start) playVideo();
    } catch { if (current()) setVideoError(true); }
  }, [data.bifUrl, playVideo, recovery?.start]);

  const onSurfaceViewCreated = useCallback((handle: string): void => {
    if (leaving.current || surfaceHandle.current === handle) return;
    surfaceGeneration.current += 1;
    surfaceHandle.current = handle;
    setFrameGeneration(surfaceGeneration.current);
    setSurfaceReady(true);
    trace('playback', 'surface-ready');
    setSurface();
  }, [setSurface]);

  const onSurfaceViewDestroyed = useCallback((handle: string): void => {
    if (surfaceHandle.current !== handle) return;
    surfaceGeneration.current += 1;
    surfaceHandle.current = null;
    setSurfaceReady(false);
    setFrameGeneration(surfaceGeneration.current);
    recoveryCurrent.current = false;
    recoveryAttempt.current?.cancel();
    if (recovery?.start) {
      memory.close(); transportReady.current = false;
      // A completed recovery controller has detached; surface loss must still
      // stop its audio before presenting the error/retry screen.
      try { videoRef.current?.pause(); } catch { /* Keep the failed picture covered. */ }
      setVideoError(true);
    }
    try { videoRef.current?.clearSurfaceHandle(handle); } catch { setVideoError(true); }
    trace('playback', 'surface-lost');
    // The owning player's refs remain stable for this callback's lifetime.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recovery?.start]);

  const onCaptionViewCreated = useCallback((captionsHandle: string): void => {
    console.info(
      '[PlayerScreen.tsx] - onCaptionViewCreated - Creating video captions',
    );
    captionViewHandle.current = captionsHandle;
    setCaptionViewHandle();
  }, []);

  const setCaptionViewHandle = () => {
    console.info(
      '[PlayerScreen.tsx] - setCaptionViewHandle - setting captionViewHandle on video',
    );
    if (videoRef.current !== null && captionViewHandle.current !== null) {
      (videoRef.current as VideoPlayer).setCaptionViewHandle(
        captionViewHandle.current,
      );
    }
  };
  const onCaptionViewDestroyed = (captionsHandle: string): void => {
    console.log(
      `[PlayerScreen.tsx] - onCaptionViewDestroyed - Destroying captionsHandle=${captionsHandle}`,
    );
    if (videoRef.current !== null) {
      (videoRef.current as VideoPlayer).clearCaptionViewHandle(captionsHandle);
    }
    captionViewHandle.current = null;
  };

  const retryPlayback = () => {
    const checkpoint = memory.last.current;
    if (!recovery || !checkpoint || leaving.current || retryBlocked || guard.status !== 'verified') return;
    const currentRelease = retryRelease.current;
    if (currentRelease) {
      if (!currentRelease.confirmed) return;
      // A second explicit activation is required after confirmed release.
      leaving.current = true; retryGeneration.current += 1;
      videoRef.current = null; surfaceHandle.current = null; captionViewHandle.current = null;
      recovery.retry(checkpoint);
      return;
    }
    memory.close(); transportReady.current = false;
    recoveryAttempt.current?.cancel(); surfaceGeneration.current += 1;
    const generation = ++retryGeneration.current;
    retryRelease.current = {generation, confirmed: false};
    setVideoError(true); setRetryClosing(true);
    trace('playback', 'retry closing');
    videoHandler.destroyVideoElementsConfirmed().then(confirmed => {
      if (leaving.current || retryGeneration.current !== generation) return;
      setRetryClosing(false);
      if (!confirmed) {setRetryBlocked(true); trace('playback', 'retry release refused'); return;}
      retryRelease.current!.confirmed = true;
      trace('playback', 'retry release confirmed');
    });
  };

  // TEST BUILD ONLY. No route, guard, destroy, retry or recovery implementation is replaced.
  const probeEligible = () => Boolean(continuousEnding && preparedRouteAccepted &&
    recovery && memory.last.current && guard.status === 'verified' &&
    !leaving.current && !returningHome && !recoveryPending && !showOpeningShell &&
    !showBuffering && !isVideoError && !isVideoEnded && surfaceReady &&
    videoRef.current && !videoRef.current.paused && videoRef.current.seeking === false &&
    videoRef.current.readyState >= 2 && videoRef.current.currentTime >= 10 &&
    memory.last.current.positionMs >= 8000);
  const probeEligibility = useRef(probeEligible); probeEligibility.current = probeEligible;
  useEffect(() => {
    const media = videoRef.current;
    if (!isVideoInitialized || !media) return;
    const refresh = () => setProbeReady(probeEligibility.current());
    media.addEventListener('timeupdate', refresh);
    media.addEventListener('play', refresh);
    media.addEventListener('pause', refresh);
    return () => {
      media.removeEventListener('timeupdate', refresh);
      media.removeEventListener('play', refresh);
      media.removeEventListener('pause', refresh);
    };
  }, [isVideoInitialized, videoRef]);
  const injectProbeFailure = () => {
    const media = videoRef.current;
    if (!media) return;
    nativeRetryProbe.trigger(probeEligible(), () => media.pause(), () => {
      trace('playback', 'TEST ONLY synthetic failure; real decoder retained for production Retry');
      setVideoError(true); setProbeUsed(true);
    });
  };

  if (isVideoEnded && continuousEnding && guard.status === 'verified') {
    return <AmbientScene title={data.title} artwork="coastal" endingPicture={continuousEnding} ended onBack={leavePlayer} testID="continuous-ended-still" />;
  }
  if (isVideoEnded && route.params.ambientPreview && ['coastal', 'forest', 'sea-otters'].includes(data.calmMenuArt ?? '')) {
    return <AmbientScene title={data.title} artwork={data.calmMenuArt as AmbientArtwork} ended onBack={leavePlayer} testID="preview-ended-still" />;
  }

  return (
    <CoastalAppearance.Provider value={false}>
    <SafeAreaView style={styles.playerContainer} testID="safe-area-view">
      <View
        style={[
          styles.surfaceContainer,
          {
            width: deviceWidth,
            height: deviceHeight,
          },
        ]}
        testID="touchable-opacity">
        {isVideoInitialized && (
          <>
            <KeplerVideoSurfaceView
              style={styles.videoSurface}
              onSurfaceViewCreated={onSurfaceViewCreated}
              onSurfaceViewDestroyed={onSurfaceViewDestroyed}
              testID="kepler-video-surface-view"
            />
            {/*
              The cover sits between the video surface (zIndex 0) and the
              captions view (zIndex 2), which is what keeps captions readable
              over a hidden picture.
            */}
            <CoverLayer
              visible={covered && !bakedAmbientVisible}
              calmFallback={calmCoverFallback}
              sceneBridge={sceneBridge}
              imageUri={access === 'guarded' ? guard.coverImageUri : undefined}
              imageSource={access === 'guarded' ? bundledStillFor(guard.coverImageUri) : undefined}
              referencePatch={route.params.referencePatch}
              screenWidth={deviceWidth}
              screenHeight={deviceHeight}
            />
            {/* Native captions need a retained RN host to stack above the image cover. */}
            <View testID="calm-captions-layer" style={styles.captions} pointerEvents="none" collapsable={false}>
              <KeplerCaptionsView
                onCaptionViewCreated={onCaptionViewCreated}
                onCaptionViewDestroyed={onCaptionViewDestroyed}
                style={StyleSheet.absoluteFill}
                show={captionID !== CAPTION_DISABLE_ID}
                testID="kepler-captions-view"
              />
            </View>
          </>
        )}

        {/* Opening, return and errors own their feedback. Unmounting cancels
            pending loading announcements; ordinary stalls keep the status mounted
            long enough to avoid blinking, without dimming the verified picture. */}
        {!showOpeningShell && !isVideoError && !isVideoEnded && !returningHome && !paused && !(guarding && guard.status === 'blocked') && (
          <BufferingWindow key={slowPlayback ? 'slow' : 'waiting'} presentation="overlay" visible={showBuffering || slowPlayback}
            statusText={['checking', 'countdown', 'covering'].includes(card.kind) ? null : slowPlayback ? 'Playback slow' : undefined} />
        )}
        {/*
          The card sits above the cover, so it stays readable while the picture
          is hidden, and keeps its own accessible status and Skip action.
        */}
        {!showOpeningShell && <CalmCard
          card={card}
          stableLayout={card.kind === 'countdown' || card.kind === 'covering'}
          manualAnnouncements
          onSkip={guard.skipTo}
          skipAccessibilityLabel={
            benignDemo ? 'Skip the demo pause' : undefined
          }
        />}
        {/*
          The practice label, on a plate in the top left corner: a row of its
          own above the card, and nowhere near the captions.
        */}
        {benignDemo && !showOpeningShell && (
          <CornerPlate label={BENIGN_STORY_LABEL} testID="benign-demo" />
        )}
        {showVideoPlayerUI && !showOpeningShell && (
          <VideoPlayerUI
            key={isVideoInitialized ? 'ready' : 'loading'}
            videoRef={videoRef}
            navigateBack={navigateBack}
            title={route.params.data.title}
            // During a countdown or a cover the scene card already says it is
            // paused and what Play and Skip do; the corner banner would say it
            // a second time, on screen and to a screen reader.
            paused={paused && card.kind !== 'countdown' && card.kind !== 'covering'}
            setCaptionStatus={setCaptionStatus}
            setSelectedCaptionInVideoPlayer={setSelectedCaptionInVideoPlayer}
            bifFrameImagesRef={bifFrameImagesRef}
            videoData={data}
            // Skip and Retry own OK while visible. The seekbar must not
            // reclaim focus when its controls appear behind either action.
            skipOwnsSelect={cardOffersSkip(card) || retryAvailable}
            selectedCaptionId={captionID}
            sceneIntervals={guarding && guard.status === 'verified' ? guard.intervals : undefined}
            requestSeek={
              guarding
                ? (source, targetMs) => {
                    guard.requestSeek(source, targetMs).catch(() => {
                      // requestSeek covers before it moves, so a rejected seek
                      // leaves the picture hidden. Nothing more to do here.
                    });
                  }
                : undefined
            }
          />
        )}
        {recoveryPending && <View testID="recovery-picture-barrier" pointerEvents="none"
          onLayout={() => setRecoveryCoverMounted(true)} style={styles.recoveryCover} />}
        {retryAvailable &&
          <View style={styles.recoveryAction}><CalmButton label="Try again" hasTVPreferredFocus sound={false} testID="slow-playback-retry" onPress={retryPlayback} /></View>}
        {showOpeningShell && <PlayerOpening title={data.title} menuArt={data.calmMenuArt} returning={returningHome} checking={guard.status !== 'verified'} motionEnabled={route.params.interfaceMotionEnabled === true} onBack={leavePlayer} />}
        {isVideoError && !returningHome && <ErrorView navigateBack={leavePlayer}
          onRetry={!retryBlocked && !retryClosing && recovery && memory.last.current && guard.status === 'verified' ? retryPlayback : undefined}
          recoveryBlocked={retryBlocked} closing={retryClosing} />}
        <View testID="native-retry-probe" style={{position: 'absolute', top: 36, right: 96, zIndex: 100, backgroundColor: '#193F3E', padding: 16}}>
          <Text style={{color: '#FFF8E8', fontSize: 24}}>TEST BUILD: synthetic failure</Text>
          {!probeUsed && probeReady && probeEligible() ? <CalmButton label="Simulate failure" sound={false}
            testID="native-retry-probe-trigger" onPress={injectProbeFailure} /> : null}
        </View>
      </View>
    </SafeAreaView>
    </CoastalAppearance.Provider>
  );
};

const arePlayerPropsEqual = (
  prevProps: PlayerProps,
  nextProps: PlayerProps,
) => {
  return isEqual(prevProps, nextProps);
};
const RecoverablePlayerScreen = (props: AppStackScreenProps<Screens.PLAYER_SCREEN>) => {
  const {data, guarded, ambientPreview, coverTest} = props.route.params;
  let identity;
  try {
    if (!ambientPreview && (!coverTest || coverTest === 'off') && guarded?.profileId && packagedLibrary.acceptsRoute(data, guarded)) {
      identity = validateCheckpointIdentity({profileId: guarded.profileId, titleId: data.id, uri: data.uri,
        sourceSha256: guarded.sha256, renditionSha256: guarded.renditionSha256,
        durationMs: guarded.durationMs, startOffsetMs: guarded.renditionStartOffsetMs ?? 0});
    }
  } catch { /* Optional recovery cannot grant access or block the ordinary guard path. */ }
  if (!identity) return <PlayerScreen {...props} />;
  return <RecoverablePlayback key={checkpointIdentityKey(identity)} identity={identity}
    title={data.title} menuArt={data.calmMenuArt} onBack={() => {
      if (props.route.params.focusId) focusManager.restoreFocus(`player_return_${props.route.params.focusId}`);
      props.navigation.goBack();
    }}>
    {(recovery, generation) => <PlayerScreen key={generation} {...props} recovery={recovery} />}
  </RecoverablePlayback>;
};
export default React.memo(RecoverablePlayerScreen, arePlayerPropsEqual);

export const styles = StyleSheet.create({
  recoveryCover: {...StyleSheet.absoluteFillObject, backgroundColor: CALM_COLORS.COVER, zIndex: 4},
  recoveryAction: {position: 'absolute', right: scale(96), top: scale(160), zIndex: 5},
  // Where captions are drawn: the renderer stacks cue lines upward from this
  // view's bottom edge, so the bottom of the picture is theirs. The card and
  // the practice plate keep clear of this band. The compact scene control
  // sits below it; tenFoot.test.tsx checks both layouts against captions.
  captions: {
    width: '100%',
    height: '100%',
    left: 0,
    bottom: scale(240),
    position: 'absolute',
    backgroundColor: 'transparent',
    flexDirection: 'column',
    alignItems: 'center',
    zIndex: 2,
  },
  playerContainer: { backgroundColor: CALM_COLORS.BACKGROUND, height: '100%' },
  surfaceContainer: { backgroundColor: COLORS.BLACK, alignItems: 'stretch' },

  videoSurface: { zIndex: 0 },
});
