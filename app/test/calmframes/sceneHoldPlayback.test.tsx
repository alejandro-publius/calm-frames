import { act, fireEvent, render, screen } from '@testing-library/react-native';
import React from 'react';
import { Image, StyleSheet, Text } from 'react-native';
import CoverLayer from '../../src/calmframes/CoverLayer';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { MediaElementLike } from '../../src/calmframes/useCoverHarness';
import { useFlashGuard } from '../../src/calmframes/useFlashGuard';
import {
  jpegEnvelope,
  SCENE_KEY,
  SCENE_NOW,
  SCENE_SHA,
  sceneMap,
  signSceneMap,
} from './sceneHoldFixtures';

function makeMedia() {
  const listeners: Record<string, Set<() => void>> = {};
  return {
    currentTime: 0,
    playbackRate: 1,
    addEventListener(name: string, listener: () => void) {
      (listeners[name] ??= new Set()).add(listener);
    },
    removeEventListener(name: string, listener: () => void) {
      listeners[name]?.delete(listener);
    },
    fire(name: string) {
      for (const listener of listeners[name] ?? []) {
        listener();
      }
    },
  };
}

const nowMs = () => SCENE_NOW;
const defaultMap = signSceneMap(sceneMap());
function Guarded({
  media,
  mapText = defaultMap,
  titleId = 'scenes',
  foreground = true,
  ready = true,
  offset = 0,
  strict = false,
}: {
  media: MediaElementLike;
  mapText?: string | null;
  titleId?: string;
  foreground?: boolean;
  ready?: boolean;
  offset?: number;
  strict?: boolean;
}) {
  const ref = React.useRef<MediaElementLike | null>(media);
  const guard = useFlashGuard({
    mediaRef: ref,
    expectedSha256: SCENE_SHA,
    publicKeyBase64: SCENE_KEY,
    mapTexts: { wcag: mapText, broadcast: mapText },
    nowMs,
    titleId,
    foreground,
    ready,
    renditionStartOffsetMs: offset,
    settings: strict
      ? { ...DEFAULT_SETTINGS, preset: 'extra-cautious' }
      : DEFAULT_SETTINGS,
    durationMs: 30000,
  });
  return (
    <>
      <Text testID="status">{guard.status}</Text>
      <Text testID="covered">{guard.covered ? 'covered' : 'clear'}</Text>
      <Text testID="uri">{guard.coverImageUri ?? 'black'}</Text>
      <Text
        testID="seek-first"
        onPress={() => guard.requestSeek('seek-bar', 5000)}>
        Seek to first hold
      </Text>
      <CoverLayer
        visible={guard.covered}
        mode={guard.coverMode}
        imageUri={guard.coverImageUri}
      />
    </>
  );
}

const read = (id: string) => screen.getByTestId(id).props.children;
async function settle() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}
function at(
  media: ReturnType<typeof makeMedia>,
  seconds: number,
  event = 'playing',
) {
  act(() => {
    media.currentTime = seconds;
    media.fire(event);
    jest.advanceTimersByTime(50);
  });
}

describe('scene hold playback', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });
  afterEach(() => {
    jest.useRealTimers();
  });

  it('shows the right authenticated still only during its scheduled interval', async () => {
    const media = makeMedia();
    render(<Guarded media={media} />);
    await settle();
    at(media, 1);
    expect(read('covered')).toBe('clear');
    expect(read('uri')).toBe('black');
    at(media, 5);
    expect(read('covered')).toBe('covered');
    expect(read('uri')).toBe(jpegEnvelope());
    expect(screen.getByTestId('calm-frames-cover-still').props.source.uri).toBe(
      jpegEnvelope(),
    );
    at(media, 10);
    expect(read('covered')).toBe('clear');
    expect(screen.queryByTestId('calm-frames-cover-still')).toBeNull();
    at(media, 15);
    expect(read('uri')).toBe(jpegEnvelope(1, 1, 1));
  });

  it.each(['waiting', 'stalled', 'pause', 'seeking', 'error'])(
    'removes the still on %s even when the scheduled cover was already on',
    async (event) => {
      const media = makeMedia();
      render(<Guarded media={media} />);
      await settle();
      at(media, 5);
      expect(read('uri')).toBe(jpegEnvelope());
      act(() => media.fire(event));
      expect(read('covered')).toBe('covered');
      expect(read('uri')).toBe('black');
      expect(screen.queryByTestId('calm-frames-cover-still')).toBeNull();
      expect(screen.getByTestId('calm-frames-cover')).toBeTruthy();
      at(media, 5, 'timeupdate');
      expect(read('uri')).toBe('black');
      at(media, 5, 'seeked');
      expect(read('covered')).toBe('covered');
      expect(read('uri')).toBe('black');
      at(media, 10);
      expect(read('covered')).toBe('clear');
      at(media, 15);
      expect(read('uri')).toBe(jpegEnvelope(1, 1, 1));
    },
  );

  it('latches black through repeated waiting and playing batched in one render', async () => {
    const media = makeMedia();
    render(<Guarded media={media} />);
    await settle();
    at(media, 5);
    expect(read('uri')).toBe(jpegEnvelope());
    for (let repeat = 0; repeat < 4; repeat += 1) {
      act(() => {
        media.fire('waiting');
        media.fire('playing');
        jest.advanceTimersByTime(50);
      });
      expect(read('covered')).toBe('covered');
      expect(read('uri')).toBe('black');
      expect(screen.queryByTestId('calm-frames-cover-still')).toBeNull();
    }
    at(media, 10);
    expect(read('covered')).toBe('clear');
    at(media, 5);
    expect(read('uri')).toBe('black');
    at(media, 15);
    expect(read('uri')).toBe(jpegEnvelope(1, 1, 1));
  });

  it('latches both interrupted and seek-target intervals through batched seeking and seeked', async () => {
    const media = makeMedia();
    render(<Guarded media={media} />);
    await settle();
    at(media, 1);
    act(() => {
      media.currentTime = 5;
      media.fire('seeking');
      media.fire('seeked');
      jest.advanceTimersByTime(50);
    });
    expect(read('covered')).toBe('covered');
    expect(read('uri')).toBe('black');
    at(media, 10);
    at(media, 15);
    expect(read('uri')).toBe(jpegEnvelope(1, 1, 1));
    act(() => {
      media.currentTime = 5;
      media.fire('seeking');
      media.fire('seeked');
      jest.advanceTimersByTime(50);
    });
    expect(read('uri')).toBe('black');
    at(media, 20);
    at(media, 15);
    expect(read('covered')).toBe('covered');
    expect(read('uri')).toBe('black');
  });

  it('latches a seek target before the seek funnel moves time without media events', async () => {
    const media = makeMedia();
    render(<Guarded media={media} />);
    await settle();
    at(media, 1);
    fireEvent.press(screen.getByTestId('seek-first'));
    expect(media.currentTime).toBe(5);
    at(media, 5, 'seeked');
    expect(read('covered')).toBe('covered');
    expect(read('uri')).toBe('black');
    at(media, 10);
    at(media, 5);
    expect(read('uri')).toBe('black');
  });

  it('retains the committed title latch after an abandoned suspended title render', async () => {
    const media = makeMedia();
    const pending = new Promise<void>(() => {});
    function Suspender({ block }: { block: boolean }) {
      if (block) {
        throw pending;
      }
      return null;
    }
    function Scenario({ titleId, block }: { titleId: string; block: boolean }) {
      return (
        <React.Suspense fallback={<Text testID="pending-title">Pending</Text>}>
          <Guarded media={media} titleId={titleId} />
          <Suspender block={block} />
        </React.Suspense>
      );
    }
    const view = render(<Scenario titleId="original" block={false} />);
    await settle();
    at(media, 5);
    expect(read('uri')).toBe(jpegEnvelope());
    act(() => {
      media.fire('waiting');
      media.fire('playing');
      jest.advanceTimersByTime(50);
    });
    expect(read('uri')).toBe('black');
    view.rerender(<Scenario titleId="never-shown" block />);
    expect(screen.getByTestId('pending-title')).toBeTruthy();
    view.rerender(<Scenario titleId="original" block={false} />);
    await settle();
    expect(read('uri')).toBe('black');
    at(media, 5);
    expect(read('uri')).toBe('black');
  });

  it('clears the previous latch only for a committed and verified title replacement', async () => {
    const media = makeMedia();
    const view = render(<Guarded media={media} titleId="original" />);
    await settle();
    at(media, 5);
    act(() => {
      media.fire('waiting');
      media.fire('playing');
      jest.advanceTimersByTime(50);
    });
    expect(read('uri')).toBe('black');
    view.rerender(<Guarded media={media} titleId="replacement" />);
    await settle();
    at(media, 5);
    expect(read('status')).toBe('verified');
    expect(read('uri')).toBe(jpegEnvelope());
  });

  it('keeps black while backgrounded or unready', async () => {
    const media = makeMedia();
    const view = render(<Guarded media={media} />);
    await settle();
    at(media, 5);
    view.rerender(<Guarded media={media} foreground={false} />);
    expect(read('covered')).toBe('covered');
    expect(read('uri')).toBe('black');
    view.rerender(<Guarded media={media} ready={false} />);
    expect(read('covered')).toBe('covered');
    expect(read('uri')).toBe('black');
    view.rerender(<Guarded media={media} />);
    at(media, 5);
    expect(read('uri')).toBe('black');
    at(media, 15);
    expect(read('uri')).toBe(jpegEnvelope(1, 1, 1));
  });

  it('fails closed on a replacement map in the same title and drops its old still', async () => {
    const media = makeMedia();
    const view = render(<Guarded media={media} />);
    await settle();
    at(media, 5);
    const tampered = defaultMap.replace(jpegEnvelope(), jpegEnvelope(1, 1, 2));
    view.rerender(<Guarded media={media} mapText={tampered} />);
    expect(read('covered')).toBe('covered');
    expect(read('uri')).toBe('black');
    await settle();
    expect(read('status')).toBe('blocked');
    expect(screen.queryByTestId('calm-frames-cover-still')).toBeNull();
  });

  it('drops old stills across a title transition and refreshes signed replacements', async () => {
    const media = makeMedia();
    const view = render(<Guarded media={media} />);
    await settle();
    at(media, 5);
    view.rerender(<Guarded media={media} titleId="next" mapText={null} />);
    expect(read('uri')).toBe('black');
    await settle();
    expect(read('status')).toBe('blocked');
    const changed = sceneMap();
    changed.scene_holds.holds[0].image_data_uri = jpegEnvelope(1, 1, 2);
    view.rerender(
      <Guarded media={media} titleId="next" mapText={signSceneMap(changed)} />,
    );
    await settle();
    at(media, 5);
    expect(read('uri')).toBe(jpegEnvelope(1, 1, 2));
  });

  it('uses the same rendition offset and keeps black for wider strict schedules', async () => {
    const media = makeMedia();
    const view = render(<Guarded media={media} offset={100} />);
    await settle();
    at(media, 4.45);
    expect(read('covered')).toBe('covered');
    expect(read('uri')).toBe(jpegEnvelope());
    view.rerender(<Guarded media={media} strict />);
    await settle();
    at(media, 5);
    expect(read('covered')).toBe('covered');
    expect(read('uri')).toBe('black');
  });

  it('prefetches only authenticated images and treats preload failure as optional', async () => {
    const prefetch = jest
      .spyOn(Image, 'prefetch')
      .mockRejectedValue(new Error('unsupported'));
    const media = makeMedia();
    const view = render(<Guarded media={media} mapText={null} />);
    await settle();
    expect(prefetch).not.toHaveBeenCalled();
    view.rerender(<Guarded media={media} />);
    await settle();
    expect(prefetch).toHaveBeenCalledWith(jpegEnvelope());
    at(media, 5);
    expect(read('covered')).toBe('covered');
    prefetch.mockRestore();
  });
});

describe('scene still rendering', () => {
  it('keeps a fully opaque black backing on load, error and source changes', () => {
    const view = render(
      <CoverLayer visible mode="dim" imageUri={jpegEnvelope()} />,
    );
    const backing = () =>
      StyleSheet.flatten(screen.getByTestId('calm-frames-cover').props.style);
    expect(backing()).toMatchObject({ backgroundColor: '#000000', opacity: 1 });
    const first = screen.getByTestId('calm-frames-cover-still');
    const lateFailure = first.props.onError;
    expect(first.props.fadeDuration).toBe(0);
    // Keep source aspect while the opaque backing fills any letterbox bars.
    expect(first.props.resizeMode).toBe('contain');
    fireEvent(first, 'error');
    expect(screen.queryByTestId('calm-frames-cover-still')).toBeNull();
    expect(backing()).toMatchObject({ backgroundColor: '#000000', opacity: 1 });
    view.rerender(
      <CoverLayer visible mode="dim" imageUri={jpegEnvelope(1, 1, 1)} />,
    );
    expect(screen.getByTestId('calm-frames-cover-still').props.source.uri).toBe(
      jpegEnvelope(1, 1, 1),
    );
    // A late failure callback for the old native image cannot black the new one.
    act(() => lateFailure());
    expect(screen.getByTestId('calm-frames-cover-still').props.source.uri).toBe(
      jpegEnvelope(1, 1, 1),
    );
    expect(backing()).toMatchObject({ backgroundColor: '#000000', opacity: 1 });
  });

  it('never paints a still in the reference-patch harness', () => {
    render(
      <CoverLayer
        visible
        imageUri={jpegEnvelope()}
        screenWidth={1920}
        screenHeight={1080}
        referencePatch={{ x: 48, y: 48, width: 96, height: 96 }}
      />,
    );
    expect(screen.queryByTestId('calm-frames-cover-still')).toBeNull();
    expect(screen.getByTestId('calm-frames-cover-top')).toBeTruthy();
  });
});
