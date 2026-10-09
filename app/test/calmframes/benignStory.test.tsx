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
    ).toContain('practice holds, no flashing');
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
      expect(practice.announcement).toMatch(/practice/i);
    }
    const refused = cardAt([], 0, { rejection: 'bad-signature' });
    expect(benignStoryCard(refused)).toBe(refused);
  });
});
