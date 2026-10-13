import { fireEvent, render, screen } from '@testing-library/react-native';
import React from 'react';
import { ReactTestInstance } from 'react-test-renderer';
import CalmButton from '../../src/calmframes/CalmButton';
import HouseholdStorageScreen from '../../src/calmframes/HouseholdStorageScreen';
import StatusNotice from '../../src/calmframes/StatusNotice';

/** Group only announcement text, so native readers can focus each action. */
function expectIndependentAction(action: ReactTestInstance) {
  let ancestor = action.parent;
  while (ancestor) {
    if (typeof ancestor.type === 'string') {
      expect(ancestor.props.accessible).not.toBe(true);
    }
    ancestor = ancestor.parent;
  }
}

describe('notice actions and announcements', () => {
  it('keeps storage retry outside the grouped failure announcement', () => {
    const onRetry = jest.fn();
    render(<HouseholdStorageScreen failed onRetry={onRetry} />);
    const retry = screen.getByRole('button', { name: 'Try again' });
    expectIndependentAction(retry);
    fireEvent.press(retry);
    expect(onRetry).toHaveBeenCalledTimes(1);
    const message = screen.getByLabelText(
      "Your settings couldn't be opened or saved. Your library stays closed until your settings and PIN are available. Try again.",
    );
    expect(message.props.accessibilityLiveRegion).toBe('polite');
    expect(message.props.accessible).toBe(true);
  });

  it('keeps both confirmation actions separate from the announcement', () => {
    const keep = jest.fn();
    const remove = jest.fn();
    render(
      <StatusNotice notice={{ title: 'Remove Sam?', detail: 'Their settings and history will be removed.', tone: 'blocked' }}>
        <CalmButton label="Keep Sam" onPress={keep} />
        <CalmButton label="Remove Sam" onPress={remove} />
      </StatusNotice>,
    );
    const keepAction = screen.getByRole('button', { name: 'Keep Sam' });
    const removeAction = screen.getByRole('button', { name: 'Remove Sam' });
    expectIndependentAction(keepAction);
    expectIndependentAction(removeAction);
    fireEvent.press(keepAction);
    fireEvent.press(removeAction);
    expect(keep).toHaveBeenCalledTimes(1);
    expect(remove).toHaveBeenCalledTimes(1);
  });
});
