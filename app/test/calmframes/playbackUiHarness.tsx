/** Actual player UI; only native media, SDK widgets and guard inputs are simulated. */
import React from 'react';
import { act, render } from '@testing-library/react-native';
import { useTVEventHandler } from '@amazon-devices/react-native-kepler';
import { benignStoryCard, benignStoryTitle } from '../../src/calmframes/benignStory';
import { Card, cardAt, NO_CARD } from '../../src/calmframes/cards';
import PlayerScreen from '../../src/screens/PlayerScreen';

jest.mock('../../src/services/bif/bifService', () => ({ getBifFrameImageSource: jest.fn(async () => null) }));
jest.mock('../../src/config/AppConfig', () => ({ isRunningOnAutomotive: () => false, isContentPersonalizationEnabled: () => false }));
jest.mock('../../src/calmframes/useFlashGuard', () => ({ useFlashGuard: () => mockGuard }));
jest.mock('../../src/calmframes/useChimeCue', () => ({ useChimeCue: () => undefined }));
jest.mock('../../src/calmframes/useCoverHarness', () => ({ useCoverHarness: () => ({ covered: false }) }));
jest.mock('@amazon-devices/react-native-vector-icons/MaterialIcons', () => {
  const ReactActual = jest.requireActual('react');
  return (props: unknown) => ReactActual.createElement('PreviewMaterialIcon', props);
});
jest.mock('@amazon-devices/react-native-kepler', () => {
  const ReactActual = jest.requireActual('react');
  const RN = jest.requireActual('react-native');
  return {
    useTVEventHandler: jest.fn(),
    BackHandler: { addEventListener: () => ({ remove() {} }) },
    TVFocusGuideView: ({ children, ...props }: any) => ReactActual.createElement(RN.View, props, children),
    useKeplerAppStateManager: () => ({ getComponentInstance: () => ({}), addAppStateListener: () => ({ remove() {} }) }),
  };
});
jest.mock('@amazon-devices/react-native-w3cmedia', () => {
  const ReactActual = jest.requireActual('react');
  return {
    VideoPlayer: jest.fn(),
    KeplerMediaControlHandler: class {},
    KeplerVideoSurfaceView: (props: unknown) => ReactActual.createElement('PreviewVideoSurface', props),
    KeplerCaptionsView: (props: unknown) => ReactActual.createElement('PreviewNativeCaptions', props),
  };
});
jest.mock('@amazon-devices/kepler-ui-components', () => {
  const ReactActual = jest.requireActual('react');
  const RN = jest.requireActual('react-native');
  return {
    Typography: ({ children, ...props }: any) => ReactActual.createElement(RN.Text, props, children),
    SeekBar: ReactActual.forwardRef((props: unknown, ref: any) => {
      ReactActual.useImperativeHandle(ref, () => ({ requestTVFocus: mockSeekFocus }));
      return ReactActual.createElement('PreviewNativeSeekBar', props);
    }),
  };
});
jest.mock('../../src/utils/VideoHandler', () => ({
  VideoHandler: class {
    video: any;
    data: unknown;
    initialized: (value: boolean) => void;
    buffering: (value: boolean) => void;
    constructor(video: any, _player: unknown, data: unknown,
      initialized: (value: boolean) => void, _ended: unknown,
      error: (value: boolean) => void, _elapsed: unknown,
      buffering: (value: boolean) => void) {
      this.video = video; this.data = data; this.initialized = initialized;
      this.buffering = buffering; mockError = error;
    }
    preBufferVideo() { this.video.current = mockMedia; this.initialized(true); this.buffering(false); }
    destroyVideoElements() {}
  },
}));

export const mockSeekFocus = jest.fn();
export let mockError: (value: boolean) => void;
export let mockMedia: ReturnType<typeof makeMedia>;
export let mockGuard: any;
export function makeMedia() {
  const listeners: Record<string, Set<() => void>> = {};
  const tracks: any = [{ id: 'english', label: 'English practice captions', language: 'en', kind: 'subtitles', mode: 'showing' }];
  tracks.getTrackById = (id: string) => tracks.find((t: any) => t.id === id);
  return {
    currentTime: 6, duration: 20, currentSrc: 'fixture', paused: false, ended: false, textTracks: tracks,
    addEventListener: (type: string, fn: () => void) => { (listeners[type] ??= new Set()).add(fn); },
    removeEventListener: (type: string, fn: () => void) => listeners[type]?.delete(fn),
    fire: (type: string) => { for (const fn of listeners[type] ?? []) fn(); },
    pause() { this.paused = true; this.fire('pause'); },
    async play() { this.paused = false; this.fire('play'); },
    clearSurfaceHandle() {}, clearCaptionViewHandle() {}, setSurfaceHandle() {}, setCaptionViewHandle() {},
    listeners,
  };
}
export const interval = { startMs: 5000, endMs: 9000, causes: ['general'] };
export function startPlayer(kind: 'none' | 'covering' | 'countdown' = 'none'): ReturnType<typeof render> & { goBack: jest.Mock } {
  mockMedia = makeMedia();
  mockMedia.currentTime = kind === 'countdown' ? 3 : 6;
  const raw = kind === 'none' ? NO_CARD : cardAt([interval] as never, mockMedia.currentTime * 1000);
  mockGuard = { card: benignStoryCard(raw as Card), covered: kind === 'covering', status: 'verified',
    intervals: [], mediaTimeMs: mockMedia.currentTime * 1000, skipTo: jest.fn(), requestSeek: jest.fn(async () => undefined), seekEngine: {} };
  const title = benignStoryTitle();
  if (kind === 'covering') mockGuard.coverImageUri = JSON.parse(title.maps!.wcag!).scene_holds.holds[0].image_data_uri;
  const goBack = jest.fn();
  const data = { ...title, title: 'Harbor', format: 'MP4', categories: [], channelID: '', posterUrl: '', description: '', mediaType: 'video', mediaSourceType: 'url', uhd: false, secure: false, rentAmount: '' };
  const view = render(<PlayerScreen navigation={{ goBack } as never} route={{ params: { data, guarded: { sha256: title.sha256, maps: title.maps } } } as never} />);
  return { ...view, goBack };
}
export function remote(eventType: string) {
  const calls = (useTVEventHandler as jest.Mock).mock.calls;
  // The actual mounted UI callback is the last registered callback.
  act(() => calls[calls.length - 1][0]({ eventKeyAction: 0, eventType }));
}
