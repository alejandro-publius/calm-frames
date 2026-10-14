/**
 * The first Watch of a session, between the details page and the player.
 *
 * PlayerScreen is a React.lazy route. Metro's import() is the async function
 * asyncRequire in metro-runtime/src/modules/asyncRequire.js: it returns a
 * pending promise even when the module is already in the bundle. metroImport
 * below behaves the same way, so the first render suspends here exactly as it
 * does on the device. Jest's own dynamic import cannot run in this project.
 */
import { act, fireEvent, render } from '@testing-library/react-native';
import React from 'react';
import { StyleSheet, Text } from 'react-native';
import { playerRouteFallback } from '../../src/components/navigation/playerRouteFallback';
import { COLORS } from '../../src/styles/Colors';
import { WithSuspense } from '../../src/utils/WithSuspense';

const Player = () => <Text testID="player-ready">player</Text>;
const metroImport = async () => ({ default: Player });

function route(params: Record<string, unknown>) {
  const navigation = { goBack: jest.fn() };
  return {
    navigation,
    props: { navigation, route: { params: { data: { title: 'Harbor' }, ...params } } },
  };
}

async function settle() {
  await act(async () => {
    await Promise.resolve();
  });
}

test('before: the default fallback puts the opaque black loading screen between the pages', async () => {
  const Route = WithSuspense(React.lazy(metroImport));
  const { props } = route({ showHomeOpening: true });
  const view = render(<Route {...props} />);
  const fallback = view.getByTestId('buffering-view');
  expect(StyleSheet.flatten(fallback.props.style).backgroundColor).toBe(COLORS.BLACK);
  expect(view.queryByTestId('player-ready')).toBeNull();
  await settle();
  expect(view.getByTestId('player-ready')).toBeTruthy();
});

test('after: a harbor-opening route shows the same opening scene while the player loads', async () => {
  const Route = WithSuspense(React.lazy(metroImport), playerRouteFallback);
  const { props } = route({ showHomeOpening: true });
  const view = render(<Route {...props} />);
  expect(view.queryByTestId('buffering-view')).toBeNull();
  expect(view.getByTestId('player-home-opening')).toBeTruthy();
  expect(view.getByText('Harbor')).toBeTruthy();
  // Announced once, by the player's own opening, not twice.
  expect(view.getByText('Opening your story...').props.accessibilityLiveRegion).toBe('none');
  expect(view.getByTestId('player-opening-back')).toBeTruthy();
  await settle();
  expect(view.getByTestId('player-ready')).toBeTruthy();
  expect(view.queryByTestId('player-home-opening')).toBeNull();
  expect(view.queryByTestId('buffering-view')).toBeNull();
});

test('Back while the player loads leaves the route once', () => {
  const Route = WithSuspense(React.lazy(metroImport), playerRouteFallback);
  const { navigation, props } = route({ showHomeOpening: true });
  const view = render(<Route {...props} />);
  fireEvent.press(view.getByTestId('player-opening-back'));
  expect(navigation.goBack).toHaveBeenCalledTimes(1);
});

test('a route that does not open on the harbor keeps the default fallback', async () => {
  const Route = WithSuspense(React.lazy(metroImport), playerRouteFallback);
  const { props } = route({});
  const view = render(<Route {...props} />);
  expect(view.getByTestId('buffering-view')).toBeTruthy();
  expect(view.queryByTestId('player-home-opening')).toBeNull();
  await settle();
  expect(view.getByTestId('player-ready')).toBeTruthy();
});

test('a fixed fallback still works as before', () => {
  const Route = WithSuspense(React.lazy(metroImport), <Text testID="fixed">fixed</Text>);
  const view = render(<Route />);
  expect(view.getByTestId('fixed')).toBeTruthy();
});
