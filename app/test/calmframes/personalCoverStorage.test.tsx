import React from 'react';
import { Text } from 'react-native';
import { act, render, screen } from '@testing-library/react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { PersonalCoverAsset } from '../../src/calmframes/personalCovers';
import { usePersonalCovers } from '../../src/calmframes/personalCoverStorage';

const asset: PersonalCoverAsset = { titleId: 'prepared', sourceSha256: 'a'.repeat(64),
  renditionSha256: 'b'.repeat(64), durationMs: 10000, renditionStartOffsetMs: 0 };
function Reader({ identity }: { identity: PersonalCoverAsset }) {
  const value = usePersonalCovers(identity);
  return <Text testID="loaded">{JSON.stringify(value)}</Text>;
}
const read = () => JSON.parse(screen.getByTestId('loaded').props.children);

it('never exposes an old revision while a new identity loads or its stale read resolves', async () => {
  const resolves: Array<(text: string | null) => void> = [];
  const getter = jest.spyOn(AsyncStorage, 'getItem').mockImplementation(() =>
    new Promise((resolve) => { resolves.push(resolve); }));
  const view = render(<Reader identity={asset} />);
  expect(read().status).toBe('loading');
  const revision = { ...asset, renditionSha256: 'c'.repeat(64) };
  view.rerender(<Reader identity={revision} />);
  await act(async () => {
    resolves[0](JSON.stringify({ version: 1, asset, additions: [{ startMs: 0, endMs: 1000 }] }));
  });
  expect(read().status).toBe('loading');
  await act(async () => { resolves[1](null); });
  expect(read()).toMatchObject({ status: 'ready', record: { asset: revision, additions: [] } });
  getter.mockRestore();
});

it('treats read rejection as blocked instead of empty preferences', async () => {
  const getter = jest.spyOn(AsyncStorage, 'getItem').mockRejectedValue(new Error('unreadable'));
  render(<Reader identity={asset} />);
  await act(async () => { await Promise.resolve(); });
  expect(read()).toEqual({ status: 'blocked' });
  getter.mockRestore();
});
