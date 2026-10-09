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
