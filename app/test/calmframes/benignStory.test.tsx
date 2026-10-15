import { fireEvent, render, screen } from '@testing-library/react-native';
import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import React from 'react';
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(async () => null),
  setItem: jest.fn(async () => undefined),
}));
import {
  benignStoryCard,
  benignStorySettings,
  benignStoryTitle,
  bundledTitlePublicKey,
  isBundledBenignStory,
} from '../../src/calmframes/benignStory';
import {
  BENIGN_STORY_MAPS,
  BENIGN_STORY_PUBLIC_KEY,
  BENIGN_STORY_RENDITION_SHA256,
  BENIGN_STORY_SHA256,
} from '../../src/calmframes/benignStoryData';
import { cardAt } from '../../src/calmframes/cards';
import { buildCoverIntervals } from '../../src/calmframes/coverSchedule';
import { verifyFlashMap } from '../../src/calmframes/flashMap';
import {
  DEFAULT_SETTINGS,
  PRESET_NAMES,
  coverOptionsFor,
} from '../../src/calmframes/household';
import { sceneHoldForInterval } from '../../src/calmframes/sceneHolds';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { checkTitle } from '../../src/calmframes/titleStatus';
import { titleDataFor } from '../../src/screens/KidModeScreen';

const assets = path.join(__dirname, '../../assets/raw/benign-story');
const nowMs = Date.parse(JSON.parse(BENIGN_STORY_MAPS.wcag).created_utc) + 1000;
const digest = (file: string) =>
  crypto
    .createHash('sha256')
    .update(fs.readFileSync(path.join(assets, file)))
    .digest('hex');

describe('the packaged benign story', () => {
  it('binds the actual original and pre-covered picture to the verified production receipt', () => {
    const evidence = JSON.parse(
      fs.readFileSync(path.join(assets, 'verification.json'), 'utf8'),
    );
    expect(digest('harbor.mp4')).toBe(BENIGN_STORY_SHA256);
    expect(digest('harbor.precovered.mp4')).toBe(BENIGN_STORY_RENDITION_SHA256);
    expect(evidence.source_sha256).toBe(BENIGN_STORY_SHA256);
    expect(evidence.playback_sha256).toBe(BENIGN_STORY_RENDITION_SHA256);
    expect(evidence.production_pipeline_passed).toBe(true);
    expect(evidence.physical_tv_validated).toBe(false);
    for (const [file, hash] of Object.entries(evidence.assets_sha256)) {
      expect(digest(file)).toBe(hash);
    }
    for (const preset of ['wcag', 'broadcast', 'extra-cautious']) {
      for (const name of [
        'map_signature',
        'scene_assets',
        'safe_rendition_clean',
        'cover_model_clean',
        'hls_rendition_clean',
        'scene_hls_drawn',
      ]) {
        expect(evidence.checks).toContainEqual(
          expect.objectContaining({ name: `${name}:${preset}`, passed: true }),
        );
      }
      const measured = JSON.parse(
        fs.readFileSync(
          path.join(assets, `measured-source.${preset}.json`),
          'utf8',
        ),
      );
      expect(measured.segments).toEqual([]);
      expect(measured.summary.pass).toBe(true);
      expect(BENIGN_STORY_MAPS[preset]).toBe(
        fs.readFileSync(path.join(assets, `harbor.${preset}.json`), 'utf8'),
      );
      expect(
        JSON.parse(BENIGN_STORY_MAPS[preset]).demonstration.synthetic_intervals,
      ).toBe(true);
    }
  });

  it.each(PRESET_NAMES)(
    'remains checked in %s at the strictest selectable room, with stills spanning every hold',
    (preset) => {
      const settings = {
        ...DEFAULT_SETTINGS,
        preset,
        tvDiagonalIn: 85,
        seatDistanceIn: 48,
      };
      const title = benignStoryTitle();
      const checked = checkTitle(title, {
        settings,
        publicKeyBase64: BENIGN_STORY_PUBLIC_KEY,
        nowMs,
      });
      expect(checked.status).toBe('verified');
      const intervals = buildCoverIntervals(checked.segments, {
        ...coverOptionsFor(settings),
        durationMs: title.durationMs,
      });
      expect(intervals).toHaveLength(2);
      const verdict = verifyFlashMap(title.maps?.wcag, {
        publicKeyBase64: BENIGN_STORY_PUBLIC_KEY,
        expectedSha256: title.sha256,
        nowMs,
      });
      expect(verdict.ok).toBe(true);
      if (!verdict.ok) throw new Error(verdict.reason);
      for (const interval of intervals) {
        const hold = sceneHoldForInterval(
          verdict.map.sceneHolds ?? [],
          interval,
        );
        expect(hold?.imageDataUri).toMatch(/^data:image\/jpeg;base64,/);
        expect(hold?.frameMs).toBeLessThan(interval.startMs);
      }
    },
  );

  it.each(['id', 'uri', 'sha256'] as const)(
    'does not grant the demo key if %s changes',
    (field) => {
      const title = { ...benignStoryTitle(), [field]: 'untrusted' };
      expect(isBundledBenignStory(title)).toBe(false);
      expect(bundledTitlePublicKey(title, 'existing-key')).toBe('existing-key');
    },
  );

  it('hands the player the verified pre-covered asset and external captions', () => {
    const checked = checkTitle(benignStoryTitle(), {
      settings: benignStorySettings(benignStoryTitle(), DEFAULT_SETTINGS),
      publicKeyBase64: BENIGN_STORY_PUBLIC_KEY,
      nowMs,
    });
    const data = titleDataFor(checked);
    expect(data.uri).toMatch(/harbor\.precovered\.mp4$/);
    expect(data.textTrack?.[0]).toMatchObject({
      language: 'en',
      mimeType: 'text/vtt',
      uri: expect.stringMatching(/harbor\.vtt$/),
    });
    const onPlay = jest.fn();
    render(<TitleDetailsScreen entry={checked} onPlay={onPlay} />);
    expect(
      JSON.stringify(
        screen.getByTestId('title-details-demo-label').props.children,
      ),
    ).toContain('practice holds');
    fireEvent.press(screen.getByTestId('title-details-play'));
    expect(
      screen.getByTestId('title-details-summary').props.children,
    ).toContain('8 seconds');
    expect(screen.getByTestId('title-details-plan-preset').props.children).toBe(
      'Extra cautious',
    );
    expect(onPlay).toHaveBeenCalledWith(checked);
  });

  it('labels practice copy while preserving timing, seek destinations and refusals', () => {
    const interval = {
      startMs: 5000,
      endMs: 9000,
      reason: 'general' as const,
      sources: [],
    };
    for (const time of [1000, 6000, 9500]) {
      const original = cardAt([interval], time);
      const practice = benignStoryCard(original);
      expect(practice).toMatchObject({
        kind: original.kind,
        interval: original.interval,
      });
      expect(practice.skipToMs).toBe(original.skipToMs);
      expect(practice.secondsLeft).toBe(original.secondsLeft);
      expect(practice.announcement).toMatch(/practice/i);
    }
    const refused = cardAt([], 0, { rejection: 'bad-signature' });
    expect(benignStoryCard(refused)).toBe(refused);
  });
});

/**
 * The practice cards, word for word, on the real Harbor schedule.
 *
 * The video storyboard quotes these cards as the app draws them, so the words
 * are pinned here exactly, at moments taken from the packaged map and the fixed
 * Extra cautious plan rather than from a made-up interval.
 *
 * Seen to fail with the Oct 2 countdown wording put back in benignStoryCard:
 *
 *     -   "detail": "In 4 seconds. Press Skip to jump past it.",
 *     +   "detail": "No flashing. The gentle tone and captions continue.",
 *     -   "title": "Practice hold coming up",
 *     +   "title": "A practice hold is coming",
 */
describe('the Harbor practice cards', () => {
  const title = benignStoryTitle();
  const settings = benignStorySettings(title, DEFAULT_SETTINGS);
  const checked = checkTitle(title, {
    settings,
    publicKeyBase64: BENIGN_STORY_PUBLIC_KEY,
    nowMs,
  });
  const intervals = buildCoverIntervals(checked.segments, {
    ...coverOptionsFor(settings),
    durationMs: title.durationMs,
  });
  const practiceAt = (timeMs: number) =>
    benignStoryCard(cardAt(intervals, timeMs));

  it('runs on the schedule the storyboard was written against', () => {
    expect(checked.status).toBe('verified');
    expect(intervals.map(({ startMs, endMs }) => [startMs, endMs])).toEqual([
      [5000, 9000],
      [12000, 16000],
    ]);
  });

  it('counts down in the real pattern, with the live seconds', () => {
    expect(practiceAt(1000)).toMatchObject({
      kind: 'countdown',
      title: 'Practice hold coming up',
      detail: 'In 4 seconds. Press Skip to jump past it.',
      announcement:
        'Practice hold coming up in 4 seconds. Press Skip to jump past it.',
    });
    // The second hold's countdown starts while the first one's after card
    // would still be up, and the countdown wins, as it does on a real title.
    expect(practiceAt(11_500)).toMatchObject({
      kind: 'countdown',
      detail: 'In 1 second. Press Skip to jump past it.',
    });
  });

  it('says what is held while it is held', () => {
    expect(practiceAt(7000)).toMatchObject({
      kind: 'covering',
      title: 'Holding a calm scene',
      detail: 'A practice hold. Sound and captions keep playing.',
      announcement:
        'Holding a calm scene for practice. Sound and captions keep playing.',
    });
  });

  it('says how long it held, and that nothing flashed', () => {
    expect(practiceAt(16_500)).toMatchObject({
      kind: 'after',
      title: 'Held 4 seconds for practice',
      detail: 'A practice hold. Nothing flashed, and sound and captions kept playing.',
      announcement:
        'Held 4 seconds for practice. A practice hold. Nothing flashed, and sound and captions kept playing.',
    });
  });

  /**
   * Seen to fail with the countdown branch taken out of benignStoryCard, so
   * the real "Flashing part coming up" card came through:
   *
   *     Expected: "0 ms countdown: false"
   *     Received: "0 ms countdown: true"
   */
  it('never says a practice hold hid flashing, at any moment of the story', () => {
    const claimsAFinding = /\bhid\b|hiding|flashing part|of flashing/i;
    for (let timeMs = 0; timeMs <= title.durationMs!; timeMs += 250) {
      const card = practiceAt(timeMs);
      if (card.kind === 'none') {
        continue;
      }
      const words = `${card.title} ${card.detail ?? ''} ${card.announcement}`;
      expect(`${timeMs} ms ${card.kind}: ${claimsAFinding.test(words)}`).toBe(
        `${timeMs} ms ${card.kind}: false`,
      );
      expect(card.announcement).toMatch(/practice/i);
    }
  });

  /**
   * The real cards are the pattern. If one of them changes how it words the
   * seconds, the practice card has to follow, so the two are held together
   * here, at the rounding edges and the singular.
   *
   * Seen to fail with the singular dropped from secondsPhrase:
   *
   *     Expected: "Held 1 second for practice"
   *     Received: "Held 1 seconds for practice"
   */
  it('words the seconds exactly as the real cards do', () => {
    const interval = (startMs: number, endMs: number) => ({
      startMs,
      endMs,
      reason: 'general' as const,
      sources: [],
    });
    for (const lengthMs of [400, 1000, 1499, 1500, 2600, 4000, 61_000]) {
      const held = interval(10_000, 10_000 + lengthMs);
      const real = cardAt([held], held.endMs + 100);
      expect(real.kind).toBe('after');
      const phrase = /^Held the picture for (.+)$/.exec(real.title)?.[1];
      expect(phrase).toBeDefined();
      expect(benignStoryCard(real).title).toBe(`Held ${phrase} for practice`);
    }
    for (const timeMs of [5000, 5900, 6000, 9000, 9001]) {
      const real = cardAt([interval(10_000, 12_000)], timeMs);
      expect(real.kind).toBe('countdown');
      expect(benignStoryCard(real).detail).toBe(real.detail);
    }
  });

  it('keeps the after card honest when it has no interval to measure', () => {
    const bare = benignStoryCard({ kind: 'after', title: '', announcement: '' });
    expect(bare.title).toBe('Held a calm scene for practice');
    expect(bare.announcement).toMatch(/practice/i);
  });
});
