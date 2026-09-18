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
import { beacon } from '../calmframes/timingLog';
import CalmCard from '../calmframes/CalmCard';
import CoverLayer from '../calmframes/CoverLayer';
import { buildCoverIntervals } from '../calmframes/coverSchedule';
import { OFFLINE_PUBLIC_KEY_BASE64 } from '../calmframes/offlineTitle';
import { SafeMediaControlHandler } from '../calmframes/SafeMediaControlHandler';
import { NO_CARD } from '../calmframes/cards';
import { useCoverHarness } from '../calmframes/useCoverHarness';
import { useFlashGuard } from '../calmframes/useFlashGuard';
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
  const surfaceHandle = useRef<string | null>(null);
  const captionViewHandle = useRef<string | null>(null);

  const captionStatus = useRef<boolean | null>(null);
  const setCaptionStatus = (status: boolean) => {
    captionStatus.current = status;
  };
  const [captionID, setCaptionID] = React.useState<string>(CAPTION_DISABLE_ID);
  const setSelectedCaptionInVideoPlayer = (id: string) => {
    setCaptionID(id);
  };
  const [isVideoEnded, setVideoEnded] = React.useState<boolean>(false);
  const [isVideoError, setVideoError] = React.useState<boolean>(false);
  const [videoPlayElapsedTimeM, setVideoPlayElapsedTimeM] =
    React.useState<number>(0);
  const timer = useRef<null | ReturnType<typeof setTimeout> | number>(null);

  const videoRef = useRef<VideoPlayer | null>(null);
  const player = useRef<ShakaPlayer | null>(null);
  const bifFrameImagesRef = useRef<FrameImageSource | null>(null);

  const TIME_TO_GO_BACK_IF_VIDEO_ENDS = 2300;
  const BACK_NAVIGATION_DELAY = 700;
  const showVideoPlayerUI = !isVideoError;

  React.useEffect(() => {
    beacon('PlayerScreen.mount', { coverTest, uri: route.params.data?.uri });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  React.useEffect(() => {
    beacon('PlayerScreen.videoInitialized', { isVideoInitialized });
  }, [isVideoInitialized]);

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
  const guardedParams = route.params.guarded;
  const guard = useFlashGuard({
    mediaRef: videoRef,
    mapTexts: guardedParams?.maps,
    mapUrls: guardedParams?.mapUrls,
    expectedSha256: guardedParams?.sha256 ?? '',
    publicKeyBase64: OFFLINE_PUBLIC_KEY_BASE64,
    settings: guardedParams?.settings,
    durationMs: guardedParams?.durationMs,
    titleId: guardedParams?.titleId ?? data.id,
    titleName: data.title,
    ready: isVideoInitialized && Boolean(guardedParams),
  });
  const guarding = Boolean(guardedParams);
  // The measurement harness and the guard never run at once: a run is a
  // measurement, kid mode is the product.
  const covered = guarding ? guard.covered : cover.covered;
  const card = guarding ? guard.card : NO_CARD;
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
      navigateBack();
    }, TIME_TO_GO_BACK_IF_VIDEO_ENDS);

    return () => clearTimeout(Number(timer.current));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isVideoEnded]);

  useEffect(() => {
    console.log(
      '[PlayerScreen.tsx] - Initialize media player: componentInstance',
      componentInstance,
    );
    console.log(
      '[PlayerScreen.tsx] - Video Handler invoke preBufferVideo',
      videoHandler.data,
    );
    videoHandler.preBufferVideo(componentInstance);
    setupEventListeners();
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

      if (bifFrameImagesRef) {
        bifFrameImagesRef.current?.clearCache();
        bifFrameImagesRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const navigateBack = useCallback(() => {
    if (captionStatus.current) {
      captionStatus.current = false;
      return true;
    }

    reportVideoExit();

    surfaceHandle.current = null;
    captionViewHandle.current = null;
    videoRef?.current?.clearSurfaceHandle('');
    videoRef?.current?.clearCaptionViewHandle('');
    videoHandler.destroyVideoElements();
    videoRef.current = null;
    clearTimeout(Number(timer.current));

    //Approx delay added to destroy media instance
    setTimeout(() => navigation.goBack(), BACK_NAVIGATION_DELAY);
    return true;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleAppStateChange = useCallback(
    (nextAppState: KeplerAppStateChangeData): void => {
      console.log(
        '[PlayerScreen.tsx] - handleAppStateChange - k_content_per: handleAppStateChange',
      );
      if (nextAppState === BACKGROUND_STATE) {
        setShowBuffering(false);
        if (coverTest !== 'off') {
          // A measurement run stays on this screen. The virtual device
          // backgrounds an app that nobody is touching, and leaving the
          // screen would tear the player down mid-run. The cover is already
          // on: useCoverHarness hides the picture as soon as the playhead
          // becomes uncertain, which includes going to the background.
          return;
        }
        navigateBack();
      }
    },
    [navigateBack, coverTest],
  );

  const backHandlerSubscription = useRef<{ remove: () => void } | null>(null);

  const setupEventListeners = useCallback(() => {
    if (Platform.isTV) {
      backHandlerSubscription.current = BackHandler.addEventListener('hardwareBackPress', navigateBack);
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
      navigateBack();
    }
  }, [videoRef, navigateBack, reportVideoPlaying]);

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
              referencePatch={route.params.referencePatch}
              screenWidth={deviceWidth}
              screenHeight={deviceHeight}
            />
            <KeplerCaptionsView
              onCaptionViewCreated={onCaptionViewCreated}
              onCaptionViewDestroyed={onCaptionViewDestroyed}
              style={styles.captions}
              show={captionID !== CAPTION_DISABLE_ID}
              testID="kepler-captions-view"
            />
          </>
        )}

        {showBuffering && (
          <BufferingWindow backgroundColor={COLORS.SEMI_TRANSPARENT} />
        )}
        {/*
          The card sits above the cover, so it stays readable while the picture
          is hidden, and it is the only thing on screen that speaks.
        */}
        <CalmCard card={card} onSkip={guard.skipTo} />
        {showVideoPlayerUI && (
          <VideoPlayerUI
            videoRef={videoRef}
            navigateBack={navigateBack}
            title={route.params.data.title}
            setCaptionStatus={setCaptionStatus}
            setSelectedCaptionInVideoPlayer={setSelectedCaptionInVideoPlayer}
            bifFrameImagesRef={bifFrameImagesRef}
            videoData={data}
            requestSeek={
              guarding
                ? (source, targetMs) => {
                    void guard.requestSeek(source, targetMs);
                  }
                : undefined
            }
          />
        )}
        {isVideoError && <ErrorView navigateBack={navigateBack} />}
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
  captions: {
    width: '100%',
    height: '100%',
    left: 0,
    bottom: 120,
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
