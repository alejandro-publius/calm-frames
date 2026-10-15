/**
 * The player refusing to play something unchecked.
 *
 * The player screen came from the Vega sample, where anything in the catalog
 * plays on request, and five screens in this app still navigate to it that
 * way. Calm Frames cannot work like that, and the fix cannot be a promise
 * about call sites: it has to be the player itself.
 *
 * What is faked here and what is not. The sample's own video plumbing is
 * replaced: VideoHandler, which talks to Shaka, and VideoPlayerUI, which is
 * the sample's transport chrome. Everything this test is about is real: the
 * access decision, the cover and the card.
 *
 * Seen to fail: take the unguarded branch out of PlayerScreen and the first
 * test here reports a missing cover and a card that is not there.
 */

import { act, render, screen } from '@testing-library/react-native';
import React from 'react';
// babel-jest hoists the jest.mock calls below above this import, so the player
// is loaded with the stand ins already in place.
import PlayerScreen from '../../src/screens/PlayerScreen';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { packagedLibrary } from '../../src/calmframes/packagedLibrary';
import { focusManager } from '../../src/utils/FocusManager';

const mockPreBuffer = jest.fn();
let mockVideoError: (error: boolean) => void;

jest.mock('../../src/w3cmedia/mediacontrols/VideoPlayerUI', () => 'VideoPlayerUI');
jest.mock('../../src/services/bif/bifService', () => ({
  getBifFrameImageSource: jest.fn(async () => null),
}));

/**
 * A stand in for the sample's video plumbing.
 *
 * It does one thing the real one does: says the video is initialized, which is
 * what puts the surface, the cover and the captions on screen. Without that
 * the player renders a buffering window and nothing else, and the state this
 * test is about never appears.
 */
jest.mock('../../src/utils/VideoHandler', () => ({
  VideoHandler: class {
    data: unknown;
    private readonly setInitialized: (value: boolean) => void;

    constructor(
      _videoRef: unknown,
      _player: unknown,
      data: unknown,
      setIsVideoInitialized: (value: boolean) => void,
      _setEnded: unknown,
      setError: (value: boolean) => void,
    ) {
      this.data = data;
      this.setInitialized = setIsVideoInitialized;
      mockVideoError = setError;
    }

    preBufferVideo() {
      mockPreBuffer();
      this.setInitialized(true);
    }

    destroyVideoElements() {}
  },
}));

const data = {
  id: 'sample',
  title: 'Something from the sample catalog',
  uri: 'https://example.invalid/sample.mp4',
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
};

function renderPlayer(params: Record<string, unknown>) {
  return render(
    <PlayerScreen
      navigation={{ goBack: jest.fn() } as never}
      route={{ params: { data, ...params } } as never}
    />,
  );
}

describe('the player with nothing to check', () => {
  beforeEach(() => mockPreBuffer.mockClear());

  it('rejects substituted prepared media before initializing the player, even with a harness flag', () => {
    const title = packagedLibrary.titles(DEFAULT_SETTINGS)[0];
    renderPlayer({ data: { ...data, id: title.id, uri: 'https://example.invalid/substituted.mp4' },
      guarded: { sha256: title.sha256, maps: title.maps, settings: DEFAULT_SETTINGS },
      coverTest: 'layering' });
    expect(mockPreBuffer).not.toHaveBeenCalled();
    expect(screen.queryByTestId('kepler-video-surface-view')).toBeNull();
    expect(screen.getByTestId('calm-card-title').props.children).toBe('This video is unavailable');
  });
  it('restores registered focus after a rejected prepared route', () => {
    const restore = jest.spyOn(focusManager, 'restoreFocus');
    const title = packagedLibrary.titles(DEFAULT_SETTINGS)[0];
    const { unmount } = renderPlayer({
      data: { ...data, id: title.id, uri: 'https://example.invalid/substituted.mp4' },
      guarded: { sha256: title.sha256, maps: title.maps, settings: DEFAULT_SETTINGS },
      focusId: title.id,
    });
    unmount();
    expect(restore).toHaveBeenCalledWith(`player_return_${title.id}`);
    restore.mockRestore();
  });

  it('keeps the picture hidden and says why', () => {
    renderPlayer({});
    expect(screen.getByTestId('calm-frames-cover')).toBeTruthy();
    expect(screen.getByTestId('calm-card-title').props.children).toBe(
      'This video is unavailable',
    );
    expect(screen.getByTestId('calm-card-detail').props.children).toMatch(
      /picture stays hidden/,
    );
  });

  it('is not fooled by guarded parameters that carry no map', () => {
    renderPlayer({ guarded: { sha256: 'a'.repeat(64) } });
    expect(screen.getByTestId('calm-frames-cover')).toBeTruthy();
    expect(screen.getByTestId('calm-card-title').props.children).toBe(
      'This video is unavailable',
    );
  });

  it('removes the stale guard card and keeps the cover on playback failure', () => {
    // Native Harbor failed with the countdown card still above the error.
    renderPlayer({});
    expect(screen.getByTestId('calm-card-title')).toBeTruthy();
    act(() => mockVideoError(true));
    expect(screen.queryByTestId('calm-card-title')).toBeNull();
    expect(screen.getByTestId('error-boundary-label')).toBeTruthy();
    expect(screen.getByTestId('calm-frames-cover')).toBeTruthy();
  });

  it('leaves a measurement run alone', () => {
    // A harness run plays a marker clip at a camera with nobody watching, and
    // the cover harness is in charge of the picture. Forcing the cover on here
    // would break every timing run.
    renderPlayer({ coverTest: 'layering', toggleEveryMs: 1_000 });
    expect(screen.queryByTestId('calm-card-title')).toBeNull();
  });
});
