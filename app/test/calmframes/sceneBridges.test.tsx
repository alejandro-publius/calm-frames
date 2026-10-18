import { createHash } from 'crypto';
import React from 'react';
import { render, screen } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import CoverLayer from '../../src/calmframes/CoverLayer';
import {
  loadSceneBridges, resolveSceneBridge, sceneBridgeTextError,
  validateSceneBridgeDocument, SceneBridgeDocument,
} from '../../src/calmframes/sceneBridges';

const asset = { titleId: 'test-card', renditionStartOffsetMs: 0, sourceSha256: 'a'.repeat(64), renditionSha256: 'b'.repeat(64), durationMs: 20000 };
const entry = { startMs: 2000, endMs: 10000, text: 'Test fixture: a card displays the number one.' };
const draft = () => ({ version: 1, ...asset, authorConfirmed: true, testFixture: true, entries: [{ ...entry }] });
const digest = (raw: string) => createHash('sha512').update(raw).digest('hex');
const load = (value: unknown = draft()) => { const raw = JSON.stringify(value); return loadSceneBridges(raw, digest(raw)); };
const bases = [{ startMs: 2000, endMs: 10000 }];

describe('creator scene bridge integrity and bounded text', () => {
  it('accepts reviewed bytes and labels synthetic demonstrations honestly', () => {
    const document = load();
    expect(document).not.toBeNull();
    expect(resolveSceneBridge(document, asset, bases, 2000)).toEqual({ text: entry.text, label: 'Scene bridge test' });
    expect(resolveSceneBridge(load({ ...draft(), testFixture: false }), asset, bases, 2000)?.label).toBe('Creator note');
  });
  it('freezes checked records and never trusts a route-shaped document', () => {
    const document = load()!;
    expect(Object.isFrozen(document)).toBe(true);
    expect(Object.isFrozen(document.entries)).toBe(true);
    expect(Object.isFrozen(document.entries[0])).toBe(true);
    expect(resolveSceneBridge(draft() as SceneBridgeDocument, asset, bases, 5000)).toBeUndefined();
  });
  it('rejects tampering, unknown checksum, oversized input and duplicate keys', () => {
    const raw = JSON.stringify(draft());
    expect(loadSceneBridges(raw.replace('number one', 'number two'), digest(raw))).toBeNull();
    expect(loadSceneBridges(raw, '')).toBeNull();
    const large = raw + ' '.repeat(16384);
    expect(loadSceneBridges(large, digest(large))).toBeNull();
    const duplicate = raw.replace('"version":1', '"version":1,"version":1');
    expect(loadSceneBridges(duplicate, digest(duplicate))).toBeNull();
    expect(loadSceneBridges('{', digest('{'))).toBeNull();
  });
  it.each(['titleId', 'renditionStartOffsetMs', 'sourceSha256', 'renditionSha256', 'durationMs'] as const)('does not reuse %s revisions', key => {
    const changed = { ...asset, [key]: key === 'durationMs' ? 21000 : key === 'renditionStartOffsetMs' ? 1 : 'c'.repeat(64) };
    expect(resolveSceneBridge(load(), changed, bases, 5000)).toBeUndefined();
  });
  it('requires exactly the same immutable base interval, not a personal or wider span', () => {
    const document = load();
    expect(resolveSceneBridge(document, asset, [], 5000)).toBeUndefined();
    expect(resolveSceneBridge(document, asset, [{ startMs: 1000, endMs: 11000 }], 5000)).toBeUndefined();
    expect(resolveSceneBridge(document, asset, [{ startMs: 2000, endMs: 9999 }], 5000)).toBeUndefined();
    expect(resolveSceneBridge(document, asset, bases, 1999)).toBeUndefined();
    expect(resolveSceneBridge(document, asset, bases, 10000)).toBeUndefined();
    expect(resolveSceneBridge(document, asset, bases, Infinity)).toBeUndefined();
    expect(resolveSceneBridge(undefined, asset, bases, 5000)).toBeUndefined();
  });
  it.each([
    { authorConfirmed: false }, { testFixture: 'yes' }, { sourceSha256: 'wrong' },
    { titleId: '' }, { renditionStartOffsetMs: NaN }, { renditionStartOffsetMs: 20001 },
    { entries: [{ ...entry, endMs: 6000 }] }, { entries: [{ ...entry, endMs: 22000 }] },
    { entries: [{ ...entry, startMs: -1 }] }, { entries: [{ ...entry, startMs: Infinity }] },
    { entries: [{ ...entry, text: 'a'.repeat(121) }] }, { entries: [{ ...entry, text: ' line ' }] },
    { entries: [{ ...entry, text: 'two\nlines' }] }, { entries: [{ ...entry, text: '<b>text</b>' }] },
    { entries: [{ ...entry, text: 'hidden\u202etext' }] },
    { entries: [{ ...entry, text: Array(21).fill('word').join(' ') }] },
    { entries: [entry, entry] }, { extra: 'not allowed' },
  ])('falls back for malformed editor data %j', change => {
    expect(load({ ...draft(), ...change })).toBeNull();
  });
  it('preserves fractional timeline identity and exact cover boundaries', () => {
    const fractional = { ...asset, durationMs: 37641.756, renditionStartOffsetMs: 12.25 };
    const interval = { startMs: 2000.25, endMs: 10000.75 };
    const document = load({ ...draft(), ...fractional, entries: [{ ...entry, ...interval }] });
    expect(resolveSceneBridge(document, fractional, [interval], 5000)?.text).toBe(entry.text);
    expect(resolveSceneBridge(document, { ...fractional, durationMs: 37642 }, [interval], 5000)).toBeUndefined();
  });
  it('enforces a reading budget as well as the absolute word limit', () => {
    expect(sceneBridgeTextError('One two three four five six seven eight.', 6000)).toBeNull();
    expect(sceneBridgeTextError('One two three four five six seven eight nine.', 6000)).not.toBeNull();
    expect(validateSceneBridgeDocument({ ...draft(), entries: [] })).toBeNull();
    expect(load({ ...draft(), entries: Array(33).fill(entry) })).toBeNull();
  });
});

describe('scene bridges remain opaque presentation', () => {
  const sceneBridge = { text: entry.text, label: 'Scene bridge test' as const };
  it('keeps coverage, layering and controls unchanged while displaying a static note', () => {
    const view = render(<CoverLayer visible calmFallback sceneBridge={sceneBridge} />);
    const cover = screen.getByTestId('calm-frames-cover');
    expect(StyleSheet.flatten(cover.props.style)).toMatchObject({ opacity: 1, zIndex: 1, backgroundColor: '#22303B' });
    expect(cover.props.pointerEvents).toBe('none');
    expect(screen.getByText(entry.text)).toBeTruthy();
    expect(screen.getByText('Scene bridge test')).toBeTruthy();
    expect(screen.getByText('You can wait or choose Skip.')).toBeTruthy();
    expect(screen.queryAllByRole('button')).toHaveLength(0);
    view.rerender(<CoverLayer visible={false} calmFallback sceneBridge={sceneBridge} />);
    expect(screen.queryByText(entry.text)).toBeNull();
  });
  it('never overlays text on startup, dim, signed still or measurement cover', () => {
    const view = render(<CoverLayer visible sceneBridge={sceneBridge} />);
    expect(screen.queryByText(entry.text)).toBeNull();
    view.rerender(<CoverLayer visible calmFallback mode="dim" sceneBridge={sceneBridge} />);
    expect(screen.queryByText(entry.text)).toBeNull();
    view.rerender(<CoverLayer visible calmFallback imageUri="verified-fixture" sceneBridge={sceneBridge} />);
    expect(screen.queryByText(entry.text)).toBeNull();
    view.rerender(<CoverLayer visible calmFallback referencePatch={{ x: 0, y: 0, width: 10, height: 10 }} sceneBridge={sceneBridge} />);
    expect(screen.queryByText(entry.text)).toBeNull();
  });
});
