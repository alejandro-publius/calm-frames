/**
 * Renaming a kid in the parent area.
 *
 * Add a kid named the new kid Kid, or Kid 2, and the screen said in a comment
 * that there was no keyboard to rename them with. Now there is one: letter
 * keys for the remote, the name being typed above them, Save and Cancel
 * below. These tests press those keys the way a remote would and check what
 * the screen says and what it saves.
 *
 * Three things are being protected.
 *
 * - The save is the route's answer, not the press. The editor closes on a
 *   true from `onRenameProfile` and on nothing else. A false keeps the draft
 *   on screen with Try again and Cancel, and a second press while the first
 *   is in flight saves nothing twice.
 * - What is saved is one kid's name and nothing else: the same id, the same
 *   settings, the same active kid, the same floor, everybody else untouched.
 * - What is refused is refused in words: a blank, a name another chip already
 *   carries, the household's own label, a seventeenth character.
 *
 * Seen to fail, each by breaking the thing on purpose and putting it back:
 *
 * - `saveName` closing the editor before the promise answered turned "closes
 *   only once the write has committed" red: `expect(received).toBeTruthy()`
 *   on `parent-area-name` while the write was still pending.
 * - the pending guard removed turned the same test red at
 *   `expect(onRenameProfile).toHaveBeenCalledTimes(1)`, Received: 2.
 * - `nameProblem` without the lower casing turned "refuses a name another
 *   chip carries" red: `robin` reached the adapter.
 */
import React from 'react';
import { act, fireEvent, render, screen } from '@testing-library/react-native';
import { BackHandler, TouchableOpacity } from 'react-native';
import ParentAreaScreen from '../../src/calmframes/ParentAreaScreen';
import {
  CANCEL_NAME_LABEL,
  EDIT_NAME_LABEL,
  NAME_EMPTY_HINT,
  NAME_SAVE_FAILED,
  NAME_SAVING,
  SAVE_NAME_LABEL,
  TRY_NAME_AGAIN_LABEL,
} from '../../src/calmframes/copy';
import { emptyHideLog } from '../../src/calmframes/hideLog';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { emptyPinGate, setPin } from '../../src/calmframes/parentGate';
import {
  addProfile,
  Family,
  MAX_PROFILE_NAME,
  newFamily,
} from '../../src/calmframes/profiles';

const gate = setPin(emptyPinGate(), '1357', 'seed', 4);
const twoKids: Family = addProfile(newFamily(DEFAULT_SETTINGS, 'Robin'), 'Sam');

type Props = React.ComponentProps<typeof ParentAreaScreen>;

/** The parent area, unlocked, for a household with Robin and Sam in it. */
function renderArea(overrides: Partial<Props> = {}) {
  const onFamilyChange = jest.fn();
  const onRenameProfile = jest.fn(async (_family: Family) => true);
  const props: Props = {
    gate,
    onGateChange: jest.fn(),
    settings: DEFAULT_SETTINGS,
    onSettingsChange: jest.fn(),
    log: emptyHideLog(),
    family: twoKids,
    onFamilyChange,
    onRenameProfile,
    titles: [],
    nowMs: () => 0,
    onBack: jest.fn(),
    ...overrides,
  };
  const view = render(<ParentAreaScreen {...props} />);
  for (const digit of '1357') {
    fireEvent.press(screen.getByTestId(`parent-area-key-${digit}`));
  }
  return { view, props, onFamilyChange, onRenameProfile };
}

const press = (testID: string) => fireEvent.press(screen.getByTestId(testID));
const key = (id: string) => `parent-area-name-key-${id}`;
/** Press the keys for these characters, a space for a space. */
const type = (text: string) => {
  for (const character of text) {
    press(key(character === ' ' ? 'space' : character.toLowerCase()));
  }
};
const erase = (count: number) => {
  for (let index = 0; index < count; index += 1) {
    press(key('delete'));
  }
};
const draft = () => screen.getByTestId('parent-area-name-draft').props.children;
const count = () => screen.getByTestId('parent-area-name-count').props.children;
const problem = () => screen.queryByTestId('parent-area-name-problem')?.props.children ?? null;
const keyLabel = (id: string) => screen.getByTestId(`${key(id)}-label`).props.children;
const editorOpen = () => screen.queryByTestId('parent-area-name') !== null;

/** Open the editor on Sam, the second kid. */
function openSam() {
  press('parent-area-profiles-profile-2');
  press('parent-area-rename-profile');
}

const flush = () => act(async () => { await Promise.resolve(); });

describe('Edit name', () => {
  it('is offered for a kid, including the only kid, and never for Everyone', () => {
    const { view } = renderArea();
    // The household is chosen first, and the household has no name to edit.
    expect(screen.queryByTestId('parent-area-rename-profile')).toBeNull();
    press('parent-area-profiles-profile-2');
    expect(screen.getByTestId('parent-area-rename-profile').props.accessibilityLabel).toBe(
      EDIT_NAME_LABEL,
    );
    press('parent-area-profiles-everyone');
    expect(screen.queryByTestId('parent-area-rename-profile')).toBeNull();
    view.unmount();

    // The last kid cannot be removed, and can still be renamed.
    renderArea({ family: newFamily(DEFAULT_SETTINGS, 'Robin') });
    press('parent-area-profiles-profile-1');
    expect(screen.queryByTestId('parent-area-remove-profile')).toBeNull();
    expect(screen.getByTestId('parent-area-rename-profile')).toBeTruthy();
  });

  it('is not offered when the route cannot say whether a save committed', () => {
    renderArea({ onRenameProfile: undefined });
    press('parent-area-profiles-profile-2');
    expect(screen.getByTestId('parent-area-add-profile')).toBeTruthy();
    expect(screen.queryByTestId('parent-area-rename-profile')).toBeNull();
  });

  it('puts the keys where the picker was, with the current name and focus on the first key', () => {
    renderArea();
    openSam();
    expect(editorOpen()).toBe(true);
    expect(screen.getByTestId('parent-area-name-title').props.children).toBe('New name for Sam');
    expect(draft()).toBe('Sam');
    expect(count()).toBe(`3 of ${MAX_PROFILE_NAME} characters`);
    expect(screen.getByTestId(key('a')).props.hasTVPreferredFocus).toBe(true);
    expect(screen.getByTestId('parent-area-back-top').props.hasTVPreferredFocus).toBe(false);
    // One thing at a time: nothing else in the group can move under the draft.
    expect(screen.queryByTestId('parent-area-profiles')).toBeNull();
    expect(screen.queryByTestId('parent-area-add-profile')).toBeNull();
    expect(screen.queryByTestId('parent-area-remove-profile')).toBeNull();
    // The rest of the page is still there.
    expect(screen.getByTestId('parent-area-preset-wcag')).toBeTruthy();
    expect(screen.getByTestId('parent-area-name-save').props.accessibilityLabel).toBe(
      SAVE_NAME_LABEL,
    );
    expect(screen.getByTestId('parent-area-name-cancel').props.accessibilityLabel).toBe(
      CANCEL_NAME_LABEL,
    );
  });
});

describe('typing a name with the remote', () => {
  it('capitalises each word, and Shift turns the next letter the other way once', () => {
    renderArea();
    openSam();
    erase(3);
    expect(draft()).toBe(NAME_EMPTY_HINT);
    expect(count()).toBe(`0 of ${MAX_PROFILE_NAME} characters`);
    // The keys show the case they will type: a capital to start.
    expect(keyLabel('a')).toBe('A');
    type('ro');
    expect(draft()).toBe('Ro');
    expect(keyLabel('a')).toBe('a');

    press(key('shift'));
    expect(keyLabel('a')).toBe('A');
    expect(screen.getByTestId(key('shift')).props.accessibilityState.selected).toBe(true);
    type('b');
    expect(draft()).toBe('RoB');
    // One shot. The rule is back for the letter after.
    expect(keyLabel('a')).toBe('a');
    expect(screen.getByTestId(key('shift')).props.accessibilityState.selected).toBe(false);

    erase(1);
    type(' j');
    expect(draft()).toBe('Ro J');
    expect(keyLabel('a')).toBe('a');
  });

  it('allows one space between words and none at the start', () => {
    renderArea();
    openSam();
    erase(3);
    press(key('space'));
    expect(draft()).toBe(NAME_EMPTY_HINT);
    type('jo');
    press(key('space'));
    press(key('space'));
    expect(draft()).toBe('Jo ');
    expect(count()).toBe(`3 of ${MAX_PROFILE_NAME} characters`);
  });

  it('stops at the longest name the picker can draw, and says so', () => {
    renderArea();
    openSam();
    erase(3);
    type('abcdefghijklmnop');
    expect(draft()).toBe('Abcdefghijklmnop');
    expect(count()).toBe(`${MAX_PROFILE_NAME} of ${MAX_PROFILE_NAME} characters`);
    expect(problem()).toBeNull();
    type('q');
    expect(draft()).toBe('Abcdefghijklmnop');
    expect(problem()).toBe(`A name can be up to ${MAX_PROFILE_NAME} characters.`);
    press(key('space'));
    expect(draft()).toBe('Abcdefghijklmnop');
    // Delete makes room, and the words about the limit go away with it.
    erase(1);
    expect(draft()).toBe('Abcdefghijklmno');
    expect(problem()).toBeNull();
  });
});

describe('what Save refuses', () => {
  it('refuses a blank in words and saves nothing', () => {
    const { onRenameProfile, onFamilyChange } = renderArea();
    openSam();
    erase(3);
    press('parent-area-name-save');
    expect(problem()).toBe('Type a name before saving.');
    expect(editorOpen()).toBe(true);
    expect(onRenameProfile).not.toHaveBeenCalled();
    expect(onFamilyChange).not.toHaveBeenCalled();
  });

  it('refuses a name another chip carries, in any case, and the household label', async () => {
    const { onRenameProfile } = renderArea();
    openSam();
    erase(3);
    type('robin');
    press('parent-area-name-save');
    expect(problem()).toBe('Robin is already in this household. Choose a different name.');
    expect(onRenameProfile).not.toHaveBeenCalled();

    // Robin and robin are two chips nobody can tell apart from a sofa.
    erase(5);
    press(key('shift'));
    type('robin');
    expect(draft()).toBe('robin');
    press('parent-area-name-save');
    expect(problem()).toBe('robin is already in this household. Choose a different name.');
    expect(onRenameProfile).not.toHaveBeenCalled();

    erase(5);
    type('everyone');
    press('parent-area-name-save');
    expect(problem()).toBe('Everyone is already in this household. Choose a different name.');
    expect(onRenameProfile).not.toHaveBeenCalled();

    // The next key takes the words away, and a free name goes through.
    erase(8);
    expect(problem()).toBeNull();
    type('ash');
    press('parent-area-name-save');
    expect(onRenameProfile).toHaveBeenCalledTimes(1);
    await flush();
  });

  it('closes without saving when the name has not changed', () => {
    const { onRenameProfile } = renderArea();
    openSam();
    press('parent-area-name-save');
    expect(editorOpen()).toBe(false);
    expect(onRenameProfile).not.toHaveBeenCalled();
    expect(screen.getByTestId('parent-area-rename-profile').props.hasTVPreferredFocus).toBe(true);
  });

  it('lets a kid keep their own name in a different case', async () => {
    const { onRenameProfile } = renderArea();
    openSam();
    erase(3);
    press(key('shift'));
    type('sam');
    expect(draft()).toBe('sam');
    press('parent-area-name-save');
    expect(onRenameProfile).toHaveBeenCalledTimes(1);
    expect(onRenameProfile.mock.calls[0][0].profiles[1].name).toBe('sam');
    await flush();
  });
});

describe('saving a name', () => {
  it('writes one kid\'s name and nothing else, through the result-returning save', async () => {
    const { onRenameProfile, onFamilyChange } = renderArea();
    openSam();
    erase(3);
    type('ash');
    press('parent-area-name-save');

    expect(onRenameProfile).toHaveBeenCalledTimes(1);
    const next: Family = onRenameProfile.mock.calls[0][0];
    expect(next).toEqual({
      ...twoKids,
      profiles: [twoKids.profiles[0], { ...twoKids.profiles[1], name: 'Ash' }],
    });
    expect(next.profiles[1].id).toBe(twoKids.profiles[1].id);
    expect(next.profiles[1].settings).toEqual(twoKids.profiles[1].settings);
    expect(next.activeProfileId).toBe(twoKids.activeProfileId);
    expect(next.floor).toEqual(twoKids.floor);
    // The void callback is not how a name is saved.
    expect(onFamilyChange).not.toHaveBeenCalled();
    await flush();
  });

  it('closes only once the write has committed, and saves nothing twice while it is in flight', async () => {
    let settle!: (accepted: boolean) => void;
    const onRenameProfile = jest.fn(
      (_family: Family) => new Promise<boolean>((resolve) => { settle = resolve; }),
    );
    const { view, props } = renderArea({ onRenameProfile });
    openSam();
    erase(3);
    type('ash');
    press('parent-area-name-save');
    expect(onRenameProfile).toHaveBeenCalledTimes(1);

    // Pending: the editor says so, keeps its draft, and ignores every press.
    expect(editorOpen()).toBe(true);
    expect(screen.getByTestId('parent-area-name-save').props.accessibilityLabel).toBe(NAME_SAVING);
    press('parent-area-name-save');
    expect(onRenameProfile).toHaveBeenCalledTimes(1);
    type('x');
    expect(draft()).toBe('Ash');
    expect(screen.getByTestId(key('x')).props.accessibilityState.disabled).toBe(true);
    press('parent-area-name-cancel');
    expect(editorOpen()).toBe(true);

    await act(async () => { settle(true); });
    expect(editorOpen()).toBe(false);
    // Focus comes back to Edit name, and the header's Back does not take it.
    expect(screen.getByTestId('parent-area-rename-profile').props.hasTVPreferredFocus).toBe(true);
    expect(screen.getByTestId('parent-area-back-top').props.hasTVPreferredFocus).toBe(false);

    // The route re-renders with the record it saved; the chip reads the new name.
    const saved: Family = onRenameProfile.mock.calls[0][0];
    view.rerender(<ParentAreaScreen {...props} family={saved} />);
    expect(screen.getByTestId('parent-area-profiles-profile-2-name').props.children).toBe('Ash');
  });

  it('saves once when two presses land in the same frame, before the screen has re-rendered', async () => {
    // The editor blocks a second press once it has been told a save is in
    // flight, but that word arrives with the next render. Two presses in one
    // frame both see the old state, and the handler's own guard is the one
    // thing between them and two writes.
    let settle!: (accepted: boolean) => void;
    const onRenameProfile = jest.fn(
      (_family: Family) => new Promise<boolean>((resolve) => { settle = resolve; }),
    );
    renderArea({ onRenameProfile });
    openSam();
    erase(3);
    type('ash');
    // The handler itself, as the profile picker's tests reach it, so both
    // presses run before React renders the pending state.
    const save = screen
      .UNSAFE_getAllByType(TouchableOpacity)
      .find((one) => one.props.testID === 'parent-area-name-save')!;
    act(() => {
      save.props.onPress();
      save.props.onPress();
    });
    expect(onRenameProfile).toHaveBeenCalledTimes(1);
    await act(async () => { settle(true); });
    expect(editorOpen()).toBe(false);
  });

  it('keeps the draft and offers Try again and Cancel when the write did not commit', async () => {
    const onRenameProfile = jest
      .fn(async (_family: Family) => true)
      .mockResolvedValueOnce(false)
      .mockResolvedValueOnce(true);
    renderArea({ onRenameProfile });
    openSam();
    erase(3);
    type('ash');
    press('parent-area-name-save');
    await flush();

    expect(editorOpen()).toBe(true);
    expect(draft()).toBe('Ash');
    expect(screen.getByTestId('parent-area-name-failed-title').props.children).toBe(
      NAME_SAVE_FAILED.title,
    );
    expect(screen.queryByTestId('parent-area-name-save')).toBeNull();
    const retry = screen.getByTestId('parent-area-name-retry');
    expect(retry.props.accessibilityLabel).toBe(TRY_NAME_AGAIN_LABEL);
    expect(retry.props.hasTVPreferredFocus).toBe(true);
    expect(screen.getByTestId(key('a')).props.hasTVPreferredFocus).toBe(false);
    expect(screen.getByTestId('parent-area-back-top').props.hasTVPreferredFocus).toBe(false);
    expect(screen.getByTestId('parent-area-name-cancel')).toBeTruthy();

    // Try again saves the same draft onto the same kid.
    fireEvent.press(retry);
    await flush();
    expect(onRenameProfile).toHaveBeenCalledTimes(2);
    expect(onRenameProfile.mock.calls[1][0]).toEqual(onRenameProfile.mock.calls[0][0]);
    expect(editorOpen()).toBe(false);
  });

  it('treats a write that throws as not saved, and Cancel then keeps the old name', async () => {
    const onRenameProfile = jest.fn(async (_family: Family) => {
      throw new Error('disk');
    });
    const { onFamilyChange } = renderArea({ onRenameProfile });
    openSam();
    erase(3);
    type('ash');
    press('parent-area-name-save');
    await flush();
    expect(editorOpen()).toBe(true);
    expect(draft()).toBe('Ash');
    expect(screen.getByTestId('parent-area-name-failed')).toBeTruthy();

    press('parent-area-name-cancel');
    expect(editorOpen()).toBe(false);
    expect(onRenameProfile).toHaveBeenCalledTimes(1);
    expect(onFamilyChange).not.toHaveBeenCalled();
    expect(screen.getByTestId('parent-area-rename-profile').props.hasTVPreferredFocus).toBe(true);
  });

  it('is blocked while the route is saving something else', () => {
    const { view, props, onRenameProfile } = renderArea();
    openSam();
    erase(3);
    type('ash');
    view.rerender(<ParentAreaScreen {...props} saving />);
    expect(screen.getByTestId(key('a')).props.accessibilityState.disabled).toBe(true);
    type('x');
    expect(draft()).toBe('Ash');
    press('parent-area-name-save');
    expect(onRenameProfile).not.toHaveBeenCalled();
    expect(editorOpen()).toBe(true);
  });
});

describe('leaving the editor', () => {
  type Handler = () => boolean;
  let registered: Handler[] = [];
  beforeEach(() => {
    registered = [];
    jest.spyOn(BackHandler, 'addEventListener').mockImplementation(((
      event: string,
      handler: Handler,
    ) => {
      if (event === 'hardwareBackPress') registered.push(handler);
      return { remove: () => { registered = registered.filter((one) => one !== handler); } };
    }) as typeof BackHandler.addEventListener);
  });
  afterEach(() => jest.restoreAllMocks());

  /** What the device does: the most recently registered handler answers first. */
  function pressBack(): boolean {
    let handled = false;
    act(() => {
      for (const handler of [...registered].reverse()) {
        if (handler()) { handled = true; break; }
      }
    });
    return handled;
  }

  it.each(['parent-area-back-top', 'parent-area-back'])(
    '%s cancels the draft before its next press can leave Parents', (button) => {
      const { props, onRenameProfile } = renderArea();
      openSam();
      erase(3);
      type('ash');
      press(button);
      expect(editorOpen()).toBe(false);
      expect(props.onBack).not.toHaveBeenCalled();
      expect(onRenameProfile).not.toHaveBeenCalled();
      expect(screen.getByTestId('parent-area-rename-profile').props.hasTVPreferredFocus).toBe(true);
      press(button);
      expect(props.onBack).toHaveBeenCalledTimes(1);
    },
  );

  it('visible Back controls cannot leave during a pending rename, even in the same frame', async () => {
    let settle!: (accepted: boolean) => void;
    const onRenameProfile = jest.fn(
      (_family: Family) => new Promise<boolean>((resolve) => { settle = resolve; }),
    );
    const { props } = renderArea({ onRenameProfile });
    openSam();
    erase(3);
    type('ash');
    const handler = (id: string) => screen.UNSAFE_getAllByType(TouchableOpacity)
      .find((one) => one.props.testID === id)!.props.onPress;
    const save = handler('parent-area-name-save');
    const headerBack = handler('parent-area-back-top');
    const footerBack = handler('parent-area-back');
    act(() => { save(); headerBack(); footerBack(); });
    expect(props.onBack).not.toHaveBeenCalled();
    expect(editorOpen()).toBe(true);
    press('parent-area-back-top');
    press('parent-area-back');
    expect(props.onBack).not.toHaveBeenCalled();
    await act(async () => { settle(false); });
    press('parent-area-back-top');
    expect(editorOpen()).toBe(false);
    expect(props.onBack).not.toHaveBeenCalled();
  });

  it('Cancel discards the draft, saves nothing and returns focus to Edit name', () => {
    const { onRenameProfile, onFamilyChange } = renderArea();
    openSam();
    erase(3);
    type('ash');
    press('parent-area-name-cancel');
    expect(editorOpen()).toBe(false);
    expect(onRenameProfile).not.toHaveBeenCalled();
    expect(onFamilyChange).not.toHaveBeenCalled();
    expect(screen.getByTestId('parent-area-rename-profile').props.hasTVPreferredFocus).toBe(true);
    expect(screen.getByTestId('parent-area-back-top').props.hasTVPreferredFocus).toBe(false);
    // Opening again starts from the saved name, not the discarded draft.
    press('parent-area-rename-profile');
    expect(draft()).toBe('Sam');
  });

  it('Back closes the editor and nothing else, and a second Back is nobody\'s to answer here', () => {
    const { onRenameProfile, props } = renderArea();
    openSam();
    erase(3);
    type('ash');
    expect(pressBack()).toBe(true);
    expect(editorOpen()).toBe(false);
    expect(onRenameProfile).not.toHaveBeenCalled();
    expect(props.onBack).not.toHaveBeenCalled();
    expect(screen.getByTestId('parent-area-rename-profile').props.hasTVPreferredFocus).toBe(true);
    // With the editor closed this screen registers no handler of its own, so
    // the route decides what Back does next, as it did before.
    expect(pressBack()).toBe(false);
  });

  it('Back waits while a write is in flight rather than showing the old name as the answer', async () => {
    let settle!: (accepted: boolean) => void;
    const onRenameProfile = jest.fn(
      (_family: Family) => new Promise<boolean>((resolve) => { settle = resolve; }),
    );
    renderArea({ onRenameProfile });
    openSam();
    erase(3);
    type('ash');
    press('parent-area-name-save');
    expect(pressBack()).toBe(true);
    expect(editorOpen()).toBe(true);
    await act(async () => { settle(true); });
    expect(editorOpen()).toBe(false);
  });

  it('moving the picker afterwards does not leave Edit name holding focus', () => {
    renderArea();
    openSam();
    press('parent-area-name-cancel');
    expect(screen.getByTestId('parent-area-rename-profile').props.hasTVPreferredFocus).toBe(true);
    press('parent-area-profiles-profile-1');
    expect(screen.getByTestId('parent-area-rename-profile').props.hasTVPreferredFocus).toBe(false);
  });
});

describe('Add a kid, then a name', () => {
  it('still adds a kid with a name nobody has, and the editor renames that kid', async () => {
    const withKid: Family = addProfile(newFamily(DEFAULT_SETTINGS, 'Kid'), 'Robin');
    const { view, props, onFamilyChange, onRenameProfile } = renderArea({ family: withKid });
    press('parent-area-add-profile');
    const added: Family = onFamilyChange.mock.calls[0][0];
    expect(added.profiles.map((one) => one.name)).toEqual(['Kid', 'Robin', 'Kid 2']);

    view.rerender(<ParentAreaScreen {...props} family={added} />);
    press('parent-area-profiles-profile-3');
    press('parent-area-rename-profile');
    expect(screen.getByTestId('parent-area-name-title').props.children).toBe('New name for Kid 2');
    expect(draft()).toBe('Kid 2');
    erase(5);
    type('ash');
    press('parent-area-name-save');
    const renamed: Family = onRenameProfile.mock.calls[0][0];
    expect(renamed.profiles.map((one) => one.name)).toEqual(['Kid', 'Robin', 'Ash']);
    expect(renamed.profiles[2].id).toBe('profile-3');
    await flush();
  });
});
