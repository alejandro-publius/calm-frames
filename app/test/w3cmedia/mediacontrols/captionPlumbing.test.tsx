/**
 * The caption track PlayerScreen turned on reaches the caption menu.
 *
 * PlayerScreen turns a title's captions on once the player is ready, which is
 * after VideoPlayerUI has already rendered. VideoPlayerUI is memoised, so the
 * new id only gets through if its comparator looks at it. ControlBarMenu is a
 * stand in here so the props VideoPlayerUI hands it can be read directly.
 *
 * Seen to fail, Oct 9 2026: with selectedCaptionId left out of
 * areVideoPlayerUIPropsEqual, the rerender test still read the Off id.
 */

import { VideoPlayer } from '@amazon-devices/react-native-w3cmedia';
import { render, screen } from '@testing-library/react-native';
import React from 'react';
import { CAPTION_DISABLE_ID } from '../../../src/constants';
import { FrameImageSource } from '../../../src/services/bif/FrameImageSource';
import { TitleData } from '../../../src/types/TitleData';
import VideoPlayerUI from '../../../src/w3cmedia/mediacontrols/VideoPlayerUI';

jest.mock('../../../src/w3cmedia/mediacontrols/ControlBarMenu', () => 'ControlBarMenu');
jest.mock('../../../src/config/AppConfig', () => ({
  isRunningOnAutomotive: jest.fn(() => false),
  isContentPersonalizationEnabled: jest.fn(() => false),
}));

const data = { id: 'title', title: 'A title', uri: 'https://example.invalid/a.mp4' } as unknown as TitleData;
const video = {
  paused: false,
  currentTime: 0,
  duration: 60,
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  textTracks: Object.assign([], { getTrackById: () => null }),
} as unknown as VideoPlayer;

function player(selectedCaptionId?: string) {
  return (
    <VideoPlayerUI
      videoRef={{ current: video }}
      navigateBack={jest.fn()}
      title={data.title}
      setCaptionStatus={jest.fn()}
      setSelectedCaptionInVideoPlayer={jest.fn()}
      bifFrameImagesRef={{ current: null as FrameImageSource | null }}
      videoData={data}
      selectedCaptionId={selectedCaptionId}
    />
  );
}

const menuProps = () => {
  const found = screen.UNSAFE_root.findAll(
    (node) => (node.type as unknown) === 'ControlBarMenu',
  );
  expect(found).toHaveLength(1);
  return found[0].props as { selectedCaptionId?: string };
};

describe('the selected caption id on its way to the menu', () => {
  it('hands the menu the id the player chose', () => {
    render(player('n-1'));
    expect(menuProps().selectedCaptionId).toBe('n-1');
  });

  it('gets through the memo when the player turns captions on after the first render', () => {
    const { rerender } = render(player(CAPTION_DISABLE_ID));
    expect(menuProps().selectedCaptionId).toBe(CAPTION_DISABLE_ID);
    rerender(player('n-1'));
    expect(menuProps().selectedCaptionId).toBe('n-1');
  });
});
