import { VideoPlayer } from '@amazon-devices/react-native-w3cmedia';
import { fireEvent, render, screen } from '@testing-library/react-native';
import React from 'react';
import { Text, TouchableOpacity, View } from 'react-native';
import { CAPTION_DISABLE_ID, CAPTION_DISABLE_TEXT } from '../../../src/constants';
import { CaptionMenu } from '../../../src/w3cmedia/mediacontrols/Captions';

// Keep the menu, options, callbacks and React state real. Only native focus
// plumbing is replaced so the actual choices can be pressed in this test.
jest.mock('@amazon-devices/react-native-kepler', () => ({
  TVFocusGuideView: 'View',
}));
jest.mock('../../../src/components/FocusableElement', () => 'TouchableOpacity');
jest.unmock('../../../src/utils/lodashHelper');

it.each([true, false])('keeps one active native track when switching language, using Off: %s', (useOff) => {
  const english = { id: 'english', label: 'English', mode: 'hidden' };
  const spanish = { id: 'spanish', label: 'Spanish', mode: 'hidden' };
  const tracks = Object.assign([english, spanish], {
    getTrackById: (id: string) => tracks.find((track) => track.id === id),
  });
  const video = { textTracks: tracks } as unknown as VideoPlayer;

  function PlayerCaptions() {
    const [visible, setVisible] = React.useState(true);
    const [selected, setSelected] = React.useState(CAPTION_DISABLE_ID);
    return (
      <View>
        <Text testID="selected-caption">{selected}</Text>
        <TouchableOpacity onPress={() => setVisible(true)} testID="open-captions">
          <Text>Open captions</Text>
        </TouchableOpacity>
        <CaptionMenu
          captionMenuVisibility={visible}
          video={video}
          setSelectedCaption={setSelected}
          setCaptionMenuVisibility={setVisible}
        />
      </View>
    );
  }

  render(<PlayerCaptions />);
  fireEvent.press(screen.getByText('English'));
  expect(english.mode).toBe('showing');
  expect(screen.getByTestId('selected-caption').props.children).toBe('english');
  fireEvent.press(screen.getByTestId('open-captions'));
  if (useOff) {
    fireEvent.press(screen.getByText(CAPTION_DISABLE_TEXT));
    expect(english.mode).toBe('hidden');
    expect(screen.getByTestId('selected-caption').props.children).toBe(CAPTION_DISABLE_ID);
    fireEvent.press(screen.getByTestId('open-captions'));
  }
  fireEvent.press(screen.getByText('Spanish'));
  expect(spanish.mode).toBe('showing');
  expect(english.mode).toBe('hidden');
  expect(tracks.filter((track) => track.mode === 'showing')).toHaveLength(1);
  expect(screen.getByTestId('selected-caption').props.children).toBe('spanish');
});

/**
 * Calm Frames turns a title's captions on before anyone opens the menu, so the
 * menu has to start from the track the player says is showing.
 *
 * Seen to fail, Oct 9 2026: with CaptionMenu ignoring selectedCaptionId, the
 * menu did not mark English as chosen, Off left English showing, and choosing
 * Spanish left English showing beside it.
 */
describe('a menu opened on captions the player already turned on', () => {
  function setup() {
    const english = { id: 'english', label: 'English', mode: 'showing' };
    const spanish = { id: 'spanish', label: 'Spanish', mode: 'hidden' };
    const tracks = Object.assign([english, spanish], {
      getTrackById: (id: string) => tracks.find((track) => track.id === id),
    });
    const video = { textTracks: tracks } as unknown as VideoPlayer;

    function PlayerCaptions() {
      const [visible, setVisible] = React.useState(true);
      // What PlayerScreen holds after turning English on by default.
      const [selected, setSelected] = React.useState('english');
      return (
        <View>
          <Text testID="selected-caption">{selected}</Text>
          <CaptionMenu
            captionMenuVisibility={visible}
            video={video}
            selectedCaptionId={selected}
            setSelectedCaption={setSelected}
            setCaptionMenuVisibility={setVisible}
          />
        </View>
      );
    }

    render(<PlayerCaptions />);
    return { english, spanish, tracks };
  }

  /**
   * Whether the menu item with this label is drawn as the chosen one.
   *
   * FocusableElement is the TouchableOpacity stand in here, and CaptionMenuItem
   * gives it a style only when the item is selected.
   */
  const chosen = (label: string) => {
    let node = screen.getByText(label).parent;
    while (node && (node.type as unknown) !== 'TouchableOpacity') {
      node = node.parent;
    }
    if (!node) {
      throw new Error(`no menu item drawn for ${label}`);
    }
    return Boolean(node.props.style);
  };

  it('shows the playing track as the chosen one, not Off', () => {
    setup();
    expect(chosen('English')).toBe(true);
    expect(chosen(CAPTION_DISABLE_TEXT)).toBe(false);
  });

  it('turns the playing track off when Off is chosen', () => {
    const { english } = setup();
    fireEvent.press(screen.getByText(CAPTION_DISABLE_TEXT));
    expect(english.mode).toBe('hidden');
    expect(screen.getByTestId('selected-caption').props.children).toBe(
      CAPTION_DISABLE_ID,
    );
  });

  it('swaps tracks without leaving two showing', () => {
    const { english, spanish, tracks } = setup();
    fireEvent.press(screen.getByText('Spanish'));
    expect(spanish.mode).toBe('showing');
    expect(english.mode).toBe('hidden');
    expect(tracks.filter((track) => track.mode === 'showing')).toHaveLength(1);
  });
});
