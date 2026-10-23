/** Copy into app/test/calmframes for an explicit preview export only. */
import { fireEvent, render as renderBase } from '@testing-library/react-native';
import fs from 'fs';
import path from 'path';
import React from 'react';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { checkedShelf } from './shelfFixtures';
import { unavailableVariants } from './unavailableFixtures';

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined),
}));
jest.mock('../../src/utils/pixelUtils', () => {
  const height = 1080; // Export at the actual target scale, not a resized screenshot.
  return { ...jest.requireActual('../../src/utils/pixelUtils'),
    scaleUxToDp: (value: number) => Math.round(value * height / 1080) };
});

test('export unavailable variants at the target layout size', () => {
  const stage = 'after';
  const height = 1080;
  const base = checkedShelf().find(entry => entry.title.title === 'Harbor story (prepared locally)');
  expect(base?.status).toBe('verified');
  if (!base) throw new Error('Checked Harbor fixture is required');
  const cases = unavailableVariants(base);
  cases.push(['long-title', { ...cases[4][1], title: { ...base.title,
    title: 'A quiet journey along the coast at sunset' } }]);
  const out = path.resolve(__dirname, '../../build/unavailable-preview', stage, String(height));
  fs.mkdirSync(out, { recursive: true });
  for (const [name, entry] of cases) {
    const view = render(<TitleDetailsScreen entry={entry} onPlay={() => {}} onBack={() => {}} />);
    fireEvent(view.getByTestId('title-details-back'), 'focus');
    fs.writeFileSync(path.join(out, `${name}.json`), JSON.stringify(view.toJSON(), null, 2));
    view.unmount();
  }
});

import { CalmControlAppearance } from '../../src/calmframes/CalmControlSurface';
const render = (ui: React.ReactElement) => renderBase(ui, { wrapper: ({ children }: { children: React.ReactNode }) => <CalmControlAppearance.Provider value>{children}</CalmControlAppearance.Provider> });
