import React from 'react';
import { act, fireEvent, render, screen } from '@testing-library/react-native';
import PersonalCoversScreen from '../../src/calmframes/PersonalCoversScreen';
import { PersonalCoverAsset } from '../../src/calmframes/personalCovers';
jest.mock('@react-native-async-storage/async-storage', () => ({}));
const asset: PersonalCoverAsset = { titleId: 'prepared', sourceSha256: 'a'.repeat(64),
  renditionSha256: 'b'.repeat(64), durationMs: 10000, renditionStartOffsetMs: 0 };
async function settle() { await act(async () => { await Promise.resolve(); }); }

it('lets a parent use remote buttons to add, review and remove exact times', async () => {
  let saved: string | null = null;
  const storage = { getItem: async () => saved, setItem: jest.fn(async (_key, text) => { saved = text; }) };
  const onBack = jest.fn();
  render(<PersonalCoversScreen asset={asset} title="Prepared test" storage={storage} onBack={onBack} />);
  await settle();
  fireEvent.press(screen.getByTestId('extra-start-more'));
  fireEvent.press(screen.getByTestId('extra-end-more'));
  fireEvent.press(screen.getByTestId('extra-add'));
  await settle();
  expect(JSON.parse(saved!).additions).toEqual([{ startMs: 1000, endMs: 6000 }]);
  expect(screen.getByTestId('extra-remove-0')).toBeTruthy();
  fireEvent.press(screen.getByTestId('extra-remove-0'));
  await settle();
  expect(JSON.parse(saved!).additions).toEqual([]);
  expect(screen.getByTestId('extra-add').props.hasTVPreferredFocus).toBe(true);
  expect(screen.getByTestId('extra-back').props.hasTVPreferredFocus).toBe(false);
  fireEvent.press(screen.getByTestId('extra-back'));
  expect(onBack).toHaveBeenCalledTimes(1);
});

it('blocks invalid draft times and does not report a failed save as saved', async () => {
  const storage = { getItem: async () => null, setItem: jest.fn(async () => { throw new Error('full'); }) };
  render(<PersonalCoversScreen asset={asset} title="Prepared test" storage={storage} onBack={() => {}} />);
  await settle();
  for (let i = 0; i < 5; i++) fireEvent.press(screen.getByTestId('extra-start-more'));
  fireEvent.press(screen.getByTestId('extra-add'));
  expect(storage.setItem).not.toHaveBeenCalled();
  fireEvent.press(screen.getByTestId('extra-start-less'));
  fireEvent.press(screen.getByTestId('extra-add'));
  await settle();
  expect(screen.getByTestId('extra-error').props.children).toContain('not saved');
  expect(screen.queryByTestId('extra-remove-0')).toBeNull();
});

it('does not replace a corrupt record with empty defaults and permits read retry', async () => {
  const storage = { getItem: jest.fn().mockResolvedValueOnce('{').mockResolvedValueOnce(null), setItem: jest.fn() };
  render(<PersonalCoversScreen asset={asset} title="Prepared test" storage={storage} onBack={() => {}} />);
  await settle();
  expect(screen.queryByTestId('extra-add')).toBeNull();
  expect(storage.setItem).not.toHaveBeenCalled();
  fireEvent.press(screen.getByTestId('extra-retry'));
  await settle();
  expect(screen.getByTestId('extra-add').props.hasTVPreferredFocus).toBe(true);
});
