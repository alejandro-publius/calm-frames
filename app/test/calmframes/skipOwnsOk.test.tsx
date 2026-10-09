/**
 * While a countdown card is up, OK belongs to its Skip button.
 *
 * The card puts D-pad focus on Skip the moment a countdown appears, so OK is a
 * press on Skip. The sample's player chrome also hears that key: with its
 * controls hidden it reads OK as play or pause, and any key brings the
 * controls up. Either one, at the moment a child is choosing to skip, pauses
 * the title under the card or drops the controls over it.
 *
 * The real VideoPlayerUI and the real useMediaControls run here, so the
 * controls appear and time out the way they do on the device. Only the remote
 * is faked: useTVEventHandler is a recorder in jest.setup.ts, and a key press
 * is a call to the last handler it recorded.
 *
 * Seen to fail, Oct 9 2026, three ways. With the countdown check taken out of
 * VideoPlayerUI's key handler, the first and third tests went red with pause
 * called once instead of never. With only the controls half taken out, the
 * same two went red with the controls back on screen. With skipOwnsSelect left
 * out of areVideoPlayerUIPropsEqual, the memo kept the first render's handler
 * and both rerender tests went red.
 */

import { useTVEventHandler } from '@amazon-devices/react-native-kepler';
import { VideoPlayer } from '@amazon-devices/react-native-w3cmedia';
import { act, render, screen } from '@testing-library/react-native';
import React from 'react';
import { Platform } from 'react-native';
import { DPADEventType, EVENT_KEY_DOWN } from '../../src/constants';
import { FrameImageSource } from '../../src/services/bif/FrameImageSource';
import { TitleData } from '../../src/types/TitleData';
import { DISMISS_CONTROLS_DELAY } from '../../src/utils/videoPlayerValues';
import VideoPlayerUI from '../../src/w3cmedia/mediacontrols/VideoPlayerUI';

jest.mock('../../src/config/AppConfig', () => ({
  isRunningOnAutomotive: jest.fn(() => false),
  isContentPersonalizationEnabled: jest.fn(() => false),
}));

const data = {
  id: 'title',
  title: 'A title',
  uri: 'https://example.invalid/title.mp4',
  format: 'MP4',
  categories: [],
  channelID: '',
  posterUrl: '',
  description: '',
  mediaType: 'video',
  mediaSourceType: 'url',
  uhd: false,
  secure: false,
  rentAmount: '',
} as unknown as TitleData;

function makeVideo() {
  return {
    paused: false,
    ended: false,
    currentTime: 2,
    duration: 60,
    currentSrc: data.uri,
    play: jest.fn(),
    pause: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    textTracks: Object.assign([], { getTrackById: () => null }),
  };
}

type Video = ReturnType<typeof makeVideo>;

function player(video: Video, skipOwnsSelect?: boolean) {
  return (
    <VideoPlayerUI
      videoRef={{ current: video as unknown as VideoPlayer }}
      navigateBack={jest.fn()}
      title={data.title}
      setCaptionStatus={jest.fn()}
      setSelectedCaptionInVideoPlayer={jest.fn()}
      bifFrameImagesRef={{ current: null as FrameImageSource | null }}
      videoData={data}
      skipOwnsSelect={skipOwnsSelect}
    />
  );
}

/** The handler the most recent render gave the remote. */
function pressRemote(eventType: DPADEventType) {
  const calls = (useTVEventHandler as jest.Mock).mock.calls;
  const handler = calls[calls.length - 1][0];
  act(() => {
    handler({ eventType, eventKeyAction: EVENT_KEY_DOWN });
  });
}

const controlsShowing = () => screen.queryByTestId('video-player-header') !== null;

/** Render, then let the controls time out, the state a title plays in. */
function renderWithControlsHidden(element: React.ReactElement) {
  const result = render(element);
  expect(controlsShowing()).toBe(true);
  act(() => {
    jest.advanceTimersByTime(DISMISS_CONTROLS_DELAY);
  });
  expect(controlsShowing()).toBe(false);
  return result;
}

describe('OK while a countdown card is up', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.spyOn(Platform, 'isTV', 'get').mockReturnValue(true);
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  it('presses Skip and nothing else: no pause, no controls', () => {
    const video = makeVideo();
    renderWithControlsHidden(player(video, true));

    pressRemote(DPADEventType.SELECT);

    expect(video.pause).not.toHaveBeenCalled();
    expect(video.play).not.toHaveBeenCalled();
    expect(controlsShowing()).toBe(false);
  });

  it('still pauses and shows the controls when no card is offering Skip', () => {
    // The same press with no countdown up, so the test above is measuring the
    // countdown and not a harness that cannot see a pause.
    const video = makeVideo();
    renderWithControlsHidden(player(video, false));

    pressRemote(DPADEventType.SELECT);

    expect(video.pause).toHaveBeenCalledTimes(1);
    expect(controlsShowing()).toBe(true);
  });

  it('takes OK over as soon as a countdown arrives on a player already on screen', () => {
    // The player is memoised. If the memo did not compare skipOwnsSelect,
    // this rerender would keep the first render's key handler and OK would
    // still pause the title under the card.
    const video = makeVideo();
    const { rerender } = renderWithControlsHidden(player(video, false));

    rerender(player(video, true));
    pressRemote(DPADEventType.SELECT);

    expect(video.pause).not.toHaveBeenCalled();
    expect(controlsShowing()).toBe(false);
  });

  it('hands OK back once the countdown has gone', () => {
    const video = makeVideo();
    const { rerender } = renderWithControlsHidden(player(video, true));

    rerender(player(video, false));
    pressRemote(DPADEventType.SELECT);

    expect(video.pause).toHaveBeenCalledTimes(1);
  });

  it('leaves the other keys alone during a countdown', () => {
    // Only OK belongs to Skip. Moving off the card is still allowed, and the
    // sample shows its controls for that the way it always has.
    const video = makeVideo();
    renderWithControlsHidden(player(video, true));

    pressRemote(DPADEventType.DOWN);

    expect(controlsShowing()).toBe(true);
    expect(video.pause).not.toHaveBeenCalled();
  });
});
