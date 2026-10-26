/** Native target wiring, not a simulation of the platform's spatial engine. */
import React from 'react';
import { act, fireEvent, render } from '@testing-library/react-native';
const RN = require('react-native');
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import { checkedShelf } from './shelfFixtures';

afterEach(() => jest.restoreAllMocks());

test('each selected card has an explicit round trip through Watch independent of card position', () => {
  const tags = new Map<string, number>();
  const tag = (id: string) => { if (!tags.has(id)) tags.set(id, tags.size + 1); return tags.get(id)!; };
  jest.spyOn(RN, 'findNodeHandle').mockImplementation((node: any) => (node?.testID ?? node?.props?.testID) ? tag(node.testID ?? node.props.testID) : null);
  const view = render(<KidHomeScreen titles={checkedShelf()} onOpen={jest.fn()} onPlay={jest.fn()} />, {
    createNodeMock: (element: any) => ({ testID: element.props.testID }),
  });
  const cards = view.getAllByTestId(/^kid-home-poster-/).filter(node => node.props.accessibilityRole === 'button');
  expect(cards.length).toBeGreaterThan(1);
  for (const card of cards) {
    fireEvent(card, 'focus');
    const id = card.props.testID;
    const watch = view.getByTestId('kid-home-watch');
    const details = view.getByTestId('kid-home-more-info');
    expect(view.getByTestId(id).props.nextFocusDown).toBe(tag('kid-home-watch'));
    expect(watch.props.nextFocusUp).toBe(tag(id));
    expect(details.props.nextFocusUp).toBe(tag(id));
    // Follow the native target supplied to Watch instead of choosing by distance.
    fireEvent(card, 'blur');
    fireEvent(watch, 'focus');
    const destination = cards.find(candidate => tag(candidate.props.testID) === view.getByTestId('kid-home-watch').props.nextFocusUp)!;
    expect(destination.props.testID).toBe(id);
    act(() => fireEvent(destination, 'focus'));
    expect(view.getByTestId(id).props.accessibilityState.selected).toBe(true);
  }
});
