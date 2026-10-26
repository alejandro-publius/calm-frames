import {
  ContentPersonalizationServer,
  IPlaybackEvent,
  PlaybackState,
} from '@amazon-devices/kepler-content-personalization';
import LinearGradient from '@amazon-devices/react-linear-gradient';
import {
  HWEvent,
  useTVEventHandler,
} from '@amazon-devices/react-native-kepler';
import { VideoPlayer } from '@amazon-devices/react-native-w3cmedia';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Platform, StyleSheet, Text, View } from 'react-native';
import { CALM_COLORS, CALM_SURFACE, CALM_SPACE, CALM_TEXT, scale } from '../../calmframes/calmStyles';
import { trace } from '../../calmframes/trace';
import { announceForAccessibility } from '../../calmframes/announce';
import { CARD_ANNOUNCEMENT_SETTLE_MS } from '../../calmframes/usePlaybackPresentation';
import { CoverInterval } from '../../calmframes/coverSchedule';
import { SeekSource } from '../../calmframes/seekSafety';
import Seekbar from '../../components/Seekbar';
import {
  isContentPersonalizationEnabled,
  isRunningOnAutomotive,
} from '../../config/AppConfig';
import { DPADEventType, EVENT_KEY_DOWN } from '../../constants';
import { getMockPlaybackEventForVideo } from '../../personalization/mock/ContentPersonalizationMocks';
import { FrameImageSource } from '../../services/bif/FrameImageSource';
import { COLORS } from '../../styles/Colors';
import { TitleData } from '../../types/TitleData';
import { areComponentPropsEqual } from '../../utils/lodashHelper';
import ControlBar from './ControlBar';
import ControlBarMenu from './ControlBarMenu';
import PlaybackControls from './PlaybackControls';
import { useMediaControls } from './types/useMediaControls';
import Header from './VideoPlayerHeader';

interface VideoPlayerUIProps {
  videoRef: React.MutableRefObject<VideoPlayer | null>;
  navigateBack: () => void;
  title: string;
  setCaptionStatus: (status: boolean) => void;
  setSelectedCaptionInVideoPlayer: (id: string) => void;
  bifFrameImagesRef: React.MutableRefObject<FrameImageSource | null>;
  videoData: TitleData;
  /**
   * Calm Frames: the one safe seek function. Given it, the seek bar and the
   * transport buttons ask the guard to move the playhead instead of writing
   * currentTime themselves.
   */
  requestSeek?: (source: SeekSource, targetMs: number) => void;
  /**
   * Calm Frames: true while a countdown card's Skip button is on screen.
   *
   * Skip takes D-pad focus the moment a countdown appears, so OK is a press
   * on Skip. The sample also reads OK as play or pause, and any key as a
   * reason to bring its controls up. Either one then would pause the title
   * under the card, or drop the controls over it, just as the child chooses
   * to skip.
   */
  skipOwnsSelect?: boolean;
  /**
   * Calm Frames: the caption track PlayerScreen has showing. A title that
   * ships captions starts with them on, so the caption menu has to open on
   * that track rather than on Off.
   */
  selectedCaptionId?: string;
  paused?: boolean;
  sceneIntervals?: CoverInterval[];
}
export const areVideoPlayerUIPropsEqual = (
  prevProps: VideoPlayerUIProps,
  nextProps: VideoPlayerUIProps,
) => {
  // The key handler reads skipOwnsSelect and the caption menu needs
  // selectedCaptionId, so a change to either has to render.
  return (
    areComponentPropsEqual(prevProps.title, nextProps.title) &&
    prevProps.skipOwnsSelect === nextProps.skipOwnsSelect &&
    prevProps.selectedCaptionId === nextProps.selectedCaptionId &&
    prevProps.paused === nextProps.paused &&
    areComponentPropsEqual(prevProps.sceneIntervals, nextProps.sceneIntervals)
  );
};

export const VideoPlayerUI = React.memo(
  ({
    navigateBack,
    title,
    videoRef,
    setCaptionStatus,
    setSelectedCaptionInVideoPlayer,
    bifFrameImagesRef,
    videoData,
    requestSeek,
    skipOwnsSelect = false,
    selectedCaptionId,
    paused = false,
    sceneIntervals,
  }: VideoPlayerUIProps) => {
    useEffect(() => { trace('playback', paused ? 'paused' : 'playing'); }, [paused]);
    const [captionMenuVisibility, setCaptionMenuVisibility] =
      useState<boolean>(false);

    const setSelectedCaptionInMenuBar = (id: string) => {
      setSelectedCaptionInVideoPlayer(id);
    };

    const [playerControlType, setPlayerControlType] = useState<string>('');
    const [isCaptionButtonFocused, setCaptionButtonFocused] = useState(false);
    const [showMediaControls, setShowMediaControls] = useState(true);
    const played = useRef(false);
    const [pauseNotice, setPauseNotice] = useState('');
    useEffect(() => {
      if (!paused) {
        // Opening/restored paused media is not a new user pause.
        played.current = videoRef.current?.paused === false && !videoRef.current?.ended;
        setPauseNotice('');
        return;
      }
      if (!played.current) return;
      const message = 'Paused. Press Play to continue.';
      setPauseNotice(message);
      // A live-region mutation can be lost alongside native control focus.
      // Speak once for this playback-to-pause transition, independently of
      // controls visibility. Resume/unmount cancels superseded speech.
      const timer = setTimeout(() => {
        announceForAccessibility(message, { force: true, queue: false });
      }, CARD_ANNOUNCEMENT_SETTLE_MS);
      return () => clearTimeout(timer);
    }, [paused, videoRef]);
    useEffect(() => { trace('playback', `controls ${showMediaControls ? 'shown' : 'hidden'}`); }, [showMediaControls]);
    const { handleShowControls, handleShowControlsOnKeyEvent, cancelTimer } =
      useMediaControls(showMediaControls, setShowMediaControls);

    useEffect(() => {
      handleShowControls();
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
      // Hide and show controls on caption menu toggel actions
      if (captionMenuVisibility) {
        cancelTimer();
      } else {
        handleShowControlsOnKeyEvent();
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [captionMenuVisibility]);

    const playPauseVideo = useCallback(() => {
      const isVideoPaused = videoRef.current?.paused;
      if (videoRef.current) {
        isVideoPaused ? videoRef.current.play() : videoRef.current.pause();
      }
    }, [videoRef]);

    useTVEventHandler((evt: HWEvent) => {
      if (!Platform.isTV) {
        return;
      }

      if (evt && evt.eventKeyAction === EVENT_KEY_DOWN) {
        let playbackEvent: IPlaybackEvent | undefined;
        // OK on a countdown card is a press on Skip, so the sample neither
        // brings its controls up for it nor reads it as play or pause.
        const okIsSkip =
          skipOwnsSelect && evt.eventType === DPADEventType.SELECT;
        setPlayerControlType(evt.eventType);

        if (!captionMenuVisibility && !okIsSkip) {
          showMediaControls
            ? handleShowControlsOnKeyEvent()
            : handleShowControls();
        }

        if (videoRef.current) {
          try {
            switch (evt.eventType) {
              case DPADEventType.PLAY:
              case DPADEventType.SKIPFORWARD:
              case DPADEventType.SKIPBACKWARD:
                console.info(`k_content_per: VideoPlayerUI : ${evt.eventType}`);
                playbackEvent = getMockPlaybackEventForVideo(
                  videoRef,
                  videoRef.current!.currentSrc,
                  PlaybackState.PLAYING,
                );
                break;

              case DPADEventType.PAUSE:
                console.info(
                  '[VideoPlayer.tsx] -DPADEventType.PAUSE -  k_content_per: VideoPlayerUI : pause',
                );
                playbackEvent = getMockPlaybackEventForVideo(
                  videoRef,
                  videoRef.current!.currentSrc,
                  PlaybackState.PAUSED,
                );
                break;

              case DPADEventType.PLAYPAUSE: {
                console.info('k_content_per: VideoPlayerUI : playpause');
                const isVideoPaused = videoRef.current.paused;

                playbackEvent = getMockPlaybackEventForVideo(
                  videoRef,
                  videoRef.current!.currentSrc,
                  isVideoPaused ? PlaybackState.PLAYING : PlaybackState.PAUSED,
                );
                break;
              }

              case DPADEventType.BACK: {
                console.info('[VideoPlayerUI.tsx]: VideoPlayerUI : back');
                if (captionMenuVisibility) {
                  setCaptionMenuVisibility(false);
                }
                setCaptionStatus(captionMenuVisibility);
                setCaptionButtonFocused(captionMenuVisibility);
                break;
              }

              case DPADEventType.SELECT: {
                console.info('k_content_per: VideoPlayerUI : select');
                if (okIsSkip) {
                  console.log(
                    '[VideoPlayerUI.tsx] - select - OK is a press on Skip, the countdown card has focus',
                  );
                  break;
                }
                // pause video
                if (!showMediaControls) {
                  playPauseVideo();
                }
                break;
              }
            }
          } catch (e) {
            console.error(`k_content_per: ${e}`);
          }
        }
        if (playbackEvent) {
          if (isContentPersonalizationEnabled()) {
            console.log(
              `k_content_per: useTvEventHandler: Reporting new playback event : ${JSON.stringify(
                playbackEvent,
              )}`,
            );
            ContentPersonalizationServer.reportNewPlaybackEvent(playbackEvent);
          }
        }
      }
    });

    const toggleCaption = useCallback(() => {
      setCaptionMenuVisibility(!captionMenuVisibility);
    }, [captionMenuVisibility]);

    const seekBarRef = useRef<any>(null);

    const setCaptionVisibility = (captionVisibility: boolean) => {
      setCaptionMenuVisibility(captionVisibility);
      seekBarRef?.current?.requestTVFocus();
    };

    return (
      <View style={styles.uiContainer} testID="video-player-ui-view">
        <View testID="player-pause-announcement" accessible accessibilityRole="text"
          accessibilityLiveRegion="none" accessibilityLabel={pauseNotice}
          style={pauseNotice ? styles.paused : styles.emptyPause}>
          {pauseNotice ? <Text testID="player-paused" style={styles.pausedText}>{pauseNotice}</Text> : null}
        </View>
        {paused && !showMediaControls && !pauseNotice && (
          // A saved paused position still needs visible guidance. It is not a
          // new pause announcement and does not change the retained live node.
          <View testID="player-paused" accessible accessibilityRole="text" accessibilityLiveRegion="none" style={styles.paused}>
            <Text style={styles.pausedText}>Paused. Press Play to continue.</Text>
          </View>
        )}
        {showMediaControls && (
          <LinearGradient
            colors={[
              COLORS.SEMI_TRANSPARENT,
              COLORS.TRANSPARENT,
              COLORS.SEMI_TRANSPARENT,
            ]}
            style={styles.ui}>
            <Header navigateBack={navigateBack} title={title} />

            {isRunningOnAutomotive() && (
              <PlaybackControls videoRef={videoRef} requestSeek={requestSeek} />
            )}

            <Seekbar
              hasTVPreferredFocus={!skipOwnsSelect}
              seekBarRef={seekBarRef}
              videoRef={videoRef}
              bifFrameImagesRef={bifFrameImagesRef}
              videoData={videoData}
              handleShowControlsOnKeyEvent={handleShowControlsOnKeyEvent}
              requestSeek={requestSeek}
              sceneIntervals={sceneIntervals}
            />
            <ControlBar
              videoRef={videoRef}
              captions={toggleCaption}
              captionMenuVisibility={captionMenuVisibility}
              playerControlType={playerControlType}
              isCaptionButtonFocused={isCaptionButtonFocused}
            />
            <ControlBarMenu
              captionMenuVisibility={captionMenuVisibility}
              videoRef={videoRef}
              setSelectedCaptionInMenuBar={setSelectedCaptionInMenuBar}
              setCaptionMenuVisibility={setCaptionVisibility}
              selectedCaptionId={selectedCaptionId}
            />
          </LinearGradient>
        )}
      </View>
    );
  },
  areVideoPlayerUIPropsEqual,
);

const styles = StyleSheet.create({
  paused: {
    zIndex: 1,
    position: 'absolute', top: scale(CALM_SPACE.SAFE_Y + 88), right: scale(CALM_SPACE.SAFE_X),
    backgroundColor: CALM_COLORS.SURFACE, padding: scale(16), borderRadius: scale(CALM_SURFACE.STATUS_RADIUS),
  },
  emptyPause: { position: 'absolute', width: 0, height: 0, overflow: 'hidden' },
  pausedText: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT },
  ui: {
    height: '100%',
    width: '100%',
    justifyContent: 'space-between',
  },
  uiContainer: {
    position: 'absolute',
    zIndex: 5,
    height: '100%',
    width: '100%',
  },
});

export default VideoPlayerUI;
