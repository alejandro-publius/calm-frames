import { VideoPlayer } from '@amazon-devices/react-native-w3cmedia';

export interface CaptionButtonProps {
  onPress: () => void;
  video: VideoPlayer;
  captionMenuVisibility: boolean;
  testID: string;
  playerControlType?: string;
  isCaptionButtonFocused: boolean | null;
}

export interface CaptionOptionProps {
  video: VideoPlayer;
  enableCaption: (captionId: string) => void;
  selectedCaptionId: string | null;
}

export interface CaptionMenuItemProps {
  text: string;
  index?: string;
  selected?: boolean;
  onPress: () => void;
  testID?: string;
}

export interface CaptionMenuProps {
  captionMenuVisibility: boolean;
  video: VideoPlayer;
  setSelectedCaption: (id: string) => void;
  setCaptionMenuVisibility: (visible: boolean) => void;
  /**
   * Calm Frames: the track the player has showing, when it chose one itself.
   * Left out, the menu keeps its own choice the way the sample did.
   */
  selectedCaptionId?: string;
}
