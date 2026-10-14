import '@testing-library/jest-native/extend-expect';
import { fireEvent, render } from '@testing-library/react-native';
import React from 'react';
import { COASTAL_COLORS as CALM_COLORS } from '../../src/calmframes/calmStyles';
import { noticeForTitle } from '../../src/calmframes/copy';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { checkedShelf } from './shelfFixtures';
import { unavailableVariants } from './unavailableFixtures';

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined),
}));

const base = checkedShelf().find(entry => entry.title.title === 'Harbor story (prepared locally)')!;

describe('unavailable title details', () => {
  it.each(unavailableVariants(base))('%s preserves its reason and offers only a focused way back', (_name, entry) => {
    const onPlay = jest.fn();
    const onBack = jest.fn();
    const view = render(<TitleDetailsScreen entry={entry} onPlay={onPlay} onBack={onBack} saving interfaceMotionEnabled />);
    expect(view.queryByTestId('title-details-play')).toBeNull();
    expect(view.queryByTestId('title-details-artwork')).toBeNull();
    expect(view.queryByTestId('title-details-hero-motion')).toBeNull();
    expect(view.queryByTestId('title-details-strip')).toBeNull();
    expect(view.queryByTestId('title-details-plan')).toBeNull();
    expect(view.queryByTestId('title-details-show-info')).toBeNull();
    expect(view.getAllByRole('button')).toHaveLength(1);
    const back = view.getByTestId('title-details-back');
    expect(back.props.hasTVPreferredFocus).toBe(true);
    expect(back.props.accessibilityLabel).toBe('Back to library');
    expect(back.props.accessibilityState).toEqual({ disabled: false });
    fireEvent(back, 'focus');
    expect(back).toHaveStyle({ borderColor: CALM_COLORS.FOCUS_RING });
    expect(view.getByTestId('title-details-back-label')).toHaveStyle({ textDecorationLine: 'underline' });
    fireEvent.press(back);
    expect(onBack).toHaveBeenCalledTimes(1);
    expect(onPlay).not.toHaveBeenCalled();
    const notice = noticeForTitle(entry)!;
    const label = view.getByTestId('title-details-notice-announcement').props.accessibilityLabel;
    const expected = notice.detail.startsWith(`${notice.title}. `)
      ? notice.detail : `${notice.title}. ${notice.detail}`;
    expect(label).toBe(expected);
    expect(label.match(/picture stays hidden/gi)).toHaveLength(1);
    expect(view.getByTestId('title-details-notice-announcement').props.accessibilityLiveRegion).toBe('polite');
  });

  it('removes playback when a previously verified title becomes unavailable', () => {
    const onPlay = jest.fn();
    const view = render(<TitleDetailsScreen entry={base} onPlay={onPlay} onBack={jest.fn()} />);
    expect(view.getByTestId('title-details-play')).toBeTruthy();
    view.rerender(<TitleDetailsScreen entry={unavailableVariants(base)[0][1]} onPlay={onPlay} onBack={jest.fn()} />);
    expect(view.queryByTestId('title-details-play')).toBeNull();
    fireEvent.press(view.getByTestId('title-details-back'));
    expect(onPlay).not.toHaveBeenCalled();
  });
});
