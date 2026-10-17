// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { VideoPlayer } from '@amazon-devices/react-native-w3cmedia';
import React from 'react';
import { TitleData } from '../../src/types/TitleData';
import { VideoHandler } from '../../src/utils/VideoHandler';

jest.mock('react', () => ({
  ...jest.requireActual('react'),
  useCallback: (fn) => fn,
}));

jest.mock('@amazon-devices/react-native-w3cmedia');

jest.mock('../../src/utils/AppOverrideMediaControlHandler', () => ({
  AppOverrideMediaControlHandler: jest.fn(),
}));

describe('VideoHandler', () => {
  const createVideoHandler = () => {
    const mockVideoRef: React.MutableRefObject<VideoPlayer | null> = {
      current: null,
    };
    const mockPlayer: React.MutableRefObject<any | null> = { current: null };
    const mockSetIsVideoInitialized = jest.fn();
    const mockSetIsVideoEnded = jest.fn();
    const mockSetIsVideoError = jest.fn();
    const mockSetVideoPlayElapsedTimeM = jest.fn();
    const mockSetShowBuffering = jest.fn();

    // Mock data
    const mockData: TitleData = {
      id: '169313',
      title: 'Beautiful Whale Tail Uvita Costa Rica',
      description: 'Beautiful Whale Tail Uvita Costa Rica',
      duration: 86,
      thumbnail:
        'http://le2.cdn01.net/videos/0000169/0169313/thumbs/0169313__007f.jpg',
      posterUrl:
        'http://le2.cdn01.net/videos/0000169/0169313/thumbs/0169313__007f.jpg',
      uri: `boat-sailing.mp4`,
      thumbnailUrl: `boat-sailing-hd/`,
      categories: ['Costa Rica Islands'],
      channelID: '13454',
      mediaType: 'video',
      mediaSourceType: 'url',
      format: 'MP4',
      secure: false,
      uhd: false,
      rentAmount: '100',
    } as TitleData;

    return {
      mockVideoRef,
      mockPlayer,
      mockData,
      mockSetIsVideoInitialized,
      mockSetIsVideoEnded,
      mockSetIsVideoError,
      mockSetVideoPlayElapsedTimeM,
      mockSetShowBuffering,
      videoHandler: new VideoHandler(
        mockVideoRef,
        mockPlayer,
        mockData as any,
        mockSetIsVideoInitialized,
        mockSetIsVideoEnded,
        mockSetIsVideoError,
        mockSetVideoPlayElapsedTimeM,
        mockSetShowBuffering,
      ),
    };
  };

  it.each([
    ['file:///pkg/assets/raw/benign-story/harbor.vtt', '/pkg/assets/raw/benign-story/harbor.vtt'],
    ['https://example.invalid/captions.vtt', 'https://example.invalid/captions.vtt'],
  ])('passes the native subtitle source for %s', (uri, expected) => {
    // Native filesrc treated file:///pkg/... as a literal filename and
    // aborted Harbor playback. Keep remote URLs unchanged.
    const { mockVideoRef, videoHandler } = createVideoHandler();
    const addTextTrack = jest.fn();
    mockVideoRef.current = { addTextTrack, textTracks: [] } as unknown as VideoPlayer;
    videoHandler.data.textTrack = [{ uri, label: 'English', language: 'en', mimeType: 'text/vtt' }];
    videoHandler.loadSubtitles();
    expect(addTextTrack).toHaveBeenCalledWith('subtitles', 'English', 'en', expected, 'text/vtt');
  });

  it('does not dismiss waiting on a repeated MP4 clock value or a seek jump', () => {
    const { mockVideoRef, videoHandler, mockSetShowBuffering } = createVideoHandler();
    const media = { currentTime: 6, paused: false, seeking: false };
    mockVideoRef.current = media as unknown as VideoPlayer;
    videoHandler.onWaiting();
    mockSetShowBuffering.mockClear();
    videoHandler.onTimeUpdate();
    expect(mockSetShowBuffering).not.toHaveBeenCalled();
    media.seeking = true; media.currentTime = 15;
    videoHandler.onTimeUpdate();
    expect(mockSetShowBuffering).not.toHaveBeenCalled();
    media.seeking = false; media.currentTime = 15.1;
    videoHandler.onTimeUpdate();
    expect(mockSetShowBuffering).toHaveBeenCalledWith(false);
    videoHandler.onWaiting(); mockSetShowBuffering.mockClear();
    media.paused = true; media.currentTime = 15.2;
    videoHandler.onTimeUpdate();
    expect(mockSetShowBuffering).not.toHaveBeenCalled();
  });

  describe('preBufferVideo', () => {
    it('opens a packaged video using its native path without changing catalog identity', () => {
      const { videoHandler } = createVideoHandler();
      const uri = 'file:///pkg/assets/raw/benign-story/harbor.precovered.mp4';
      videoHandler.data.uri = uri;
      const video = { src: '', autoplay: false, pause: jest.fn(), load: jest.fn() };
      videoHandler.loadStaticMediaPlayer(video);
      expect(video.src).toBe('/pkg/assets/raw/benign-story/harbor.precovered.mp4');
      expect(videoHandler.data.uri).toBe(uri);
      expect(video.load).toHaveBeenCalled();
    });

    it('should initialize video player and setup event listeners', async () => {
      const { mockVideoRef, videoHandler } = createVideoHandler();

      videoHandler.setupEventListeners = jest.fn();
      videoHandler.loadVideoElements = jest.fn();
      videoHandler.destroyVideoElements = jest.fn().mockResolvedValue(true);

      const mockInitialize = jest.fn().mockResolvedValue(undefined);
      mockVideoRef.current = {
        initialize: mockInitialize,
        setMediaControlFocus: jest.fn(),
      } as unknown as VideoPlayer;

      await videoHandler.preBufferVideo();

      expect(videoHandler.destroyVideoElements).toBeCalled();
      expect(mockInitialize).toHaveBeenCalled();
      expect(videoHandler.setupEventListeners).toBeCalled();
      expect(videoHandler.loadVideoElements).toBeCalled();
      expect(global.gmedia).toBe(mockVideoRef.current);
      expect(mockVideoRef.current.autoplay).toBe(false);
      expect(mockVideoRef.current).not.toBeNull();
    });
  });

  it('settles quietly when leaving while media control focus is pending', async () => {
    const { mockVideoRef, videoHandler } = createVideoHandler();
    let resolveFocus!: () => void;
    const focus = new Promise<void>((resolve) => { resolveFocus = resolve; });
    const initialize = jest.fn().mockResolvedValue(undefined);
    const setMediaControlFocus = jest.fn(() => focus);
    videoHandler.destroyVideoElements = jest.fn().mockResolvedValue(true);
    mockVideoRef.current = { initialize, setMediaControlFocus } as unknown as VideoPlayer;
    const pending = videoHandler.preBufferVideo({} as never);
    await Promise.resolve();
    expect(setMediaControlFocus).toHaveBeenCalled();
    mockVideoRef.current = null;
    resolveFocus();
    await expect(pending).resolves.toBeUndefined();
    expect(initialize).not.toHaveBeenCalled();
  });

  it('does not attach listeners or load after leaving during initialization', async () => {
    const { mockVideoRef, videoHandler } = createVideoHandler();
    let resolveInitialize!: () => void;
    const initialized = new Promise<void>((resolve) => { resolveInitialize = resolve; });
    videoHandler.destroyVideoElements = jest.fn().mockResolvedValue(true);
    videoHandler.setupEventListeners = jest.fn();
    videoHandler.loadVideoElements = jest.fn();
    mockVideoRef.current = { initialize: jest.fn(() => initialized) } as unknown as VideoPlayer;
    await videoHandler.preBufferVideo();
    mockVideoRef.current = null;
    resolveInitialize();
    await new Promise(process.nextTick);
    expect(videoHandler.setupEventListeners).not.toHaveBeenCalled();
    expect(videoHandler.loadVideoElements).not.toHaveBeenCalled();
  });

  it.each(['initialize', 'load'] as const)(
    'reports a %s failure immediately for the current player',
    async (failure) => {
      const { mockVideoRef, mockSetIsVideoError, videoHandler } = createVideoHandler();
      videoHandler.destroyVideoElements = jest.fn().mockReturnValue(true);
      videoHandler.setupEventListeners = jest.fn();
      videoHandler.loadVideoElements = jest.fn(() => {
        if (failure === 'load') { throw new Error('Asset unavailable'); }
      });
      mockVideoRef.current = {
        initialize: jest.fn(() => failure === 'initialize'
          ? Promise.reject(new Error('Native initialization failed'))
          : Promise.resolve()),
      } as unknown as VideoPlayer;

      await videoHandler.preBufferVideo();
      await new Promise(process.nextTick);

      expect(mockSetIsVideoError).toHaveBeenCalledTimes(1);
      expect(mockSetIsVideoError).toHaveBeenCalledWith(true);
    },
  );

  it('ignores an initialization failure after leaving playback', async () => {
    const { mockVideoRef, mockSetIsVideoError, videoHandler } = createVideoHandler();
    let rejectInitialize!: (reason: Error) => void;
    const initialized = new Promise<void>((_resolve, reject) => { rejectInitialize = reject; });
    videoHandler.destroyVideoElements = jest.fn().mockReturnValue(true);
    mockVideoRef.current = { initialize: jest.fn(() => initialized) } as unknown as VideoPlayer;
    await videoHandler.preBufferVideo();
    mockVideoRef.current = null;
    rejectInitialize(new Error('Initialization completed after Back'));
    await new Promise(process.nextTick);
    expect(mockSetIsVideoError).not.toHaveBeenCalled();
  });

  describe('destroyMediaPlayerSync', () => {
    it.each(['timeout', 'failure'])('does not report completed teardown after native %s', (status) => {
      const { mockVideoRef, videoHandler } = createVideoHandler();
      const native = { pause: jest.fn(), deinitializeSync: jest.fn(() => status) };
      mockVideoRef.current = native as unknown as VideoPlayer;
      videoHandler.removeEventListeners = jest.fn();
      expect(videoHandler.destroyVideoElements()).toBe(false);
      expect(native.deinitializeSync).toHaveBeenCalledWith(1500);
      expect(mockVideoRef.current).toBe(native);
    });

    it('does not report completed teardown when native deinitialization throws', () => {
      const { mockVideoRef, videoHandler } = createVideoHandler();
      mockVideoRef.current = { pause: jest.fn(), deinitializeSync: () => { throw Error('native failure'); } } as unknown as VideoPlayer;
      videoHandler.removeEventListeners = jest.fn();
      expect(videoHandler.destroyVideoElements()).toBe(false);
    });

    it('should successfully destroy media player for MP4 content', () => {
      const { mockVideoRef, videoHandler } = createVideoHandler();

      const mockPause = jest.fn();
      const mockDeinitializeSync = jest.fn().mockReturnValue('success');

      mockVideoRef.current = {
        pause: mockPause,
        deinitializeSync: mockDeinitializeSync,
      } as unknown as VideoPlayer;

      videoHandler.removeEventListeners = jest.fn();

      (global as any).gmedia = mockVideoRef.current;

      const result = videoHandler.destroyMediaPlayerSync();

      expect(mockPause).toHaveBeenCalled();
      expect(videoHandler.removeEventListeners).toHaveBeenCalled();
      expect(mockDeinitializeSync).toHaveBeenCalledWith(1500);
      expect(mockVideoRef.current).toBeNull();
      expect(global.gmedia).toBeNull();
      expect(result).toBe(true);
    });

    it('should handle adaptive media player destruction', () => {
      const { mockVideoRef, mockPlayer, videoHandler } = createVideoHandler();

      videoHandler.selectedFileType = 'HLS';

      const mockPause = jest.fn();
      const mockDeinitializeSync = jest.fn().mockReturnValue('success');
      const mockUnload = jest.fn();

      mockVideoRef.current = {
        pause: mockPause,
        deinitializeSync: mockDeinitializeSync,
      } as unknown as VideoPlayer;

      mockPlayer.current = {
        unload: mockUnload,
      };

      videoHandler.removeEventListeners = jest.fn();

      const result = videoHandler.destroyMediaPlayerSync();

      expect(mockPause).toHaveBeenCalled();
      expect(videoHandler.removeEventListeners).toHaveBeenCalled();
      expect(mockUnload).toHaveBeenCalled();
      expect(mockPlayer.current).toBeNull();
      expect(mockDeinitializeSync).toHaveBeenCalledWith(1500);
      expect(result).toBe(true);
    });
  });
});
