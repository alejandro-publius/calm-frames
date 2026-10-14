import {
  ContentPersonalizationServer,
  PlaybackState,
} from '@amazon-devices/kepler-content-personalization';
import {
  BackHandler,
  HWEvent,
  IComponentInstance,
  IKeplerAppStateManager,
  KeplerAppStateChangeData,
  KeplerAppStateEvent,
  useKeplerAppStateManager,
  useTVEventHandler,
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
  useWindowDimensions,
  View,
} from 'react-native';
import CalmCard from '../calmframes/CalmCard';
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
import { pausedCard, usePlaybackPaused } from '../calmframes/usePlaybackPresentation';
import { useFlashGuard } from '../calmframes/useFlashGuard';
import BufferingWindow from '../components/BufferingWindow';
import {
  AppStackParamList,
  AppStackScreenProps,
  Screens,
} from '../components/navigation/types';
import { isContentPersonalizationEnabled } from '../config/AppConfig';
import { CAPTION_DISABLE_ID, EVENT_KEY_DOWN } from '../constants';
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

const PlayerScreen = ({
  navigation,
  route,
}: AppStackScreenProps<Screens.PLAYER_SCREEN>) => {
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
  const [surfaceReady, setSurfaceReady] = React.useState(false);
  const [returningHome, setReturningHome] = React.useState(false);
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
  const timer = useRef<null | ReturnType<typeof setTimeout> | number>(null);
  const exitTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const leaving = useRef(false);

  const videoRef = useRef<VideoPlayer | null>(null);
  const player = useRef<ShakaPlayer | null>(null);
  const bifFrameImagesRef = useRef<FrameImageSource | null>(null);

  const TIME_TO_GO_BACK_IF_VIDEO_ENDS = 2300;
  const BACK_NAVIGATION_DELAY = 700;
  const showVideoPlayerUI = !isVideoError;
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
    const shown = showDefaultCaptions(
      videoRef.current?.textTracks as TextTrackListLike | undefined,
      data.textTrack,
      data.id,
    );
    if (shown !== CAPTION_DISABLE_ID) {
      console.log(
        `[PlayerScreen.tsx] - captions - on by default, track ${shown}`,
      );
      setCaptionID(shown);
    }
  }, [isVideoInitialized, data.textTrack, data.id]);

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
  const bundledIdentity = {
    id: data.id,
    uri: data.uri,
    sha256: guardedParams?.sha256,
  };
  const benignDemo = isBundledBenignStory(bundledIdentity);
  const guard = useFlashGuard({
    mediaRef: videoRef,
    mapTexts: guardedParams?.maps,
    mapUrls: guardedParams?.mapUrls,
    expectedSha256: guardedParams?.sha256 ?? '',
    publicKeyBase64: preparedRouteAccepted ? packagedLibrary.publicKeyBase64 : bundledTitlePublicKey(
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
    enabled: guardedParams?.chimeEnabled !== false,
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
  const homeOpening = route.params.showHomeOpening === true && guarding && !isVideoError && guard.status !== 'blocked';
  const openingFrameReady = useOpeningFrame({ media: videoRef, enabled: homeOpening && !returningHome,
    verified: guard.status === 'verified', surfaceReady, onTimeout: () => setVideoError(true) });
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
          detail: 'This title cannot be opened. Return to the library.',
          announcement: 'This title is unavailable. Return to the library.',
        }
      : UNGUARDED_CARD;
  }
  // A failed player has no advancing timeline. Keep its picture hidden and
  // remove the stale countdown/Skip control above the recovery screen.
  if (isVideoError) {
    covered = true;
    card = NO_CARD;
  }
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
  const mediaControlHandler = React.useMemo(
    () =>
      guarding
        ? new SafeMediaControlHandler({
            engine: guard.seekEngine,
            getCurrentMs: () => (videoRef.current?.currentTime ?? 0) * 1000,
          })
        : undefined,
    [guarding, guard.seekEngine],
  );

  const videoHandler = new VideoHandler(
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

  useTVEventHandler((evt: HWEvent) => {
    if (!Platform.isTV) {
      return;
    }
    if (evt && evt.eventKeyAction === EVENT_KEY_DOWN) {
      if (isVideoEnded) {
        clearTimeout(Number(timer.current));
        setVideoEnded(false);
      }
    }
  });

  useEffect(() => {
    if (!isVideoEnded) {
      return;
    }
    timer.current = setTimeout(() => {
      leavePlayer();
    }, TIME_TO_GO_BACK_IF_VIDEO_ENDS);

    return () => clearTimeout(Number(timer.current));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isVideoEnded]);

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
      clearTimeout(Number(timer.current));
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

  useEffect(() => {
    return () => {
      /**
       * When the player is unmounted we check if the instance was destroyed correctly,
       * if not, it is destroyed (commonly used with integrations like EPG).
       */
      if (videoRef?.current) {
        surfaceHandle.current = null;
        captionViewHandle.current = null;
        videoRef.current?.clearSurfaceHandle('');
        videoRef?.current?.clearCaptionViewHandle('');
        videoHandler.destroyVideoElements();
        videoRef.current = null;
        clearTimeout(Number(timer.current));
      }

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
    leaving.current = true;
    if (route.params.showHomeOpening) setReturningHome(true);

    reportVideoExit();

    surfaceHandle.current = null;
    captionViewHandle.current = null;
    videoRef?.current?.clearSurfaceHandle('');
    videoRef?.current?.clearCaptionViewHandle('');
    videoHandler.destroyVideoElements();
    videoRef.current = null;
    clearTimeout(Number(timer.current));

    //Approx delay added to destroy media instance
    exitTimer.current = setTimeout(() => navigation.goBack(), BACK_NAVIGATION_DELAY);
    return true;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
    if (surfaceHandle.current) {
      videoRef.current?.setSurfaceHandle(surfaceHandle.current);

      //Get bif file if apply
      if (data?.bifUrl) {
        bifFrameImagesRef.current = await getBifFrameImageSource(data.bifUrl);
      }

      // Play video once surface has created and set to media reference
      playVideo();
    }
  }, [data.bifUrl, playVideo]);

  const onSurfaceViewCreated = useCallback(
    (_surfaceHandle: string): void => {
      console.info(
        '[PlayerScreen.tsx] - onSurfaceViewCreated - Creating video surface',
      );
      surfaceHandle.current = _surfaceHandle;
      setSurfaceReady(true);
      setSurface();
    },
    [setSurface],
  );

  const onSurfaceViewDestroyed = useCallback((_surfaceHandle: string): void => {
    // Clear surface on screen unmount
    videoRef.current?.clearSurfaceHandle(_surfaceHandle);
  }, []);

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

  return (
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
              visible={covered}
              imageUri={access === 'guarded' ? guard.coverImageUri : undefined}
              referencePatch={route.params.referencePatch}
              screenWidth={deviceWidth}
              screenHeight={deviceHeight}
            />
            {/* Native captions need a retained RN host to stack above the image cover. */}
            <View style={styles.captions} pointerEvents="none" collapsable={false}>
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

        {showBuffering && (
          <BufferingWindow backgroundColor={COLORS.SEMI_TRANSPARENT} />
        )}
        {/*
          The card sits above the cover, so it stays readable while the picture
          is hidden, and it is the only thing on screen that speaks.
        */}
        {!showOpeningShell && <CalmCard
          card={pausedCard(card, paused)}
          onSkip={guard.skipTo}
          skipAccessibilityLabel={
            benignDemo ? 'Skip the practice hold' : undefined
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
            paused={paused}
            setCaptionStatus={setCaptionStatus}
            setSelectedCaptionInVideoPlayer={setSelectedCaptionInVideoPlayer}
            bifFrameImagesRef={bifFrameImagesRef}
            videoData={data}
            // The card's Skip button has focus during a countdown, so OK is
            // Skip's and the sample must not pause or show its controls.
            skipOwnsSelect={cardOffersSkip(card)}
            selectedCaptionId={captionID}
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
        {showOpeningShell && <PlayerOpening title={data.title} returning={returningHome} onBack={leavePlayer} />}
        {isVideoError && !returningHome && <ErrorView navigateBack={leavePlayer} />}
      </View>
    </SafeAreaView>
  );
};

const arePlayerPropsEqual = (
  prevProps: PlayerProps,
  nextProps: PlayerProps,
) => {
  return isEqual(prevProps, nextProps);
};
export default React.memo(PlayerScreen, arePlayerPropsEqual);

export const styles = StyleSheet.create({
  // Where captions are drawn: the renderer stacks cue lines upward from this
  // view's bottom edge, so the bottom of the picture is theirs. The card and
  // the practice plate keep to the top (PLAYER_LAYOUT in calmStyles.ts), and
  // tenFoot.test.tsx fails if either reaches down into the captions.
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
  playerContainer: { backgroundColor: COLORS.GRAY, height: '100%' },
  surfaceContainer: { backgroundColor: COLORS.BLACK, alignItems: 'stretch' },

  videoSurface: { zIndex: 0 },
});
