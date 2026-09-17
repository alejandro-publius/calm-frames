// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { DrawerScreenProps } from '@amazon-devices/react-navigation__drawer/lib/typescript/src/types';
import { StackNavigationProp } from '@amazon-devices/react-navigation__stack';
import { StackScreenProps } from '@amazon-devices/react-navigation__stack/lib/typescript/src/types';
import { ImageSourcePropType, TouchableOpacity } from 'react-native';
import { ReferencePatch } from '../../calmframes/CoverLayer';
import { FlashSegment } from '../../calmframes/coverSchedule';
import { HarnessMode } from '../../calmframes/useCoverHarness';
import { TitleData } from '../../types/TitleData';

export enum Screens {
  DEFAULT_SCREEN = 'Home',
  APP_DRAWER = 'AppDrawer',
  HOME_SCREEN = 'Home',
  DETAILS_SCREEN = 'Details',
  PLAYER_SCREEN = 'Player',
  SETTINGS_SCREEN = 'Settings',
  SEARCH_SCREEN = 'Search',
  SEARCH_RESULTS_SCREEN = 'SearchResultsScreen',
  FEEDBACK_SCREEN = 'FeedBackScreen',
}

export enum DrawerType {
  PERMANENT = 'permanent',
  FRONT = 'front',
  SLIDE = 'slide',
  BACK = 'back',
}

export type AppStackParamList = {
  [Screens.APP_DRAWER]: undefined;
  [Screens.HOME_SCREEN]: undefined;
  [Screens.SEARCH_SCREEN]: undefined;
  [Screens.SETTINGS_SCREEN]: undefined;
  [Screens.FEEDBACK_SCREEN]: undefined;
  [Screens.SEARCH_RESULTS_SCREEN]: {
    searchKeyword: string;
  };
  [Screens.DETAILS_SCREEN]: {
    data: TitleData;
    focusId?: number | string;
  };
  [Screens.PLAYER_SCREEN]: {
    data: TitleData;
    focusId?: number | string;
    /**
     * Calm Frames cover harness. "layering" is the phase 1.5 check and
     * "timing" is the GATE 1 harness. Leave it out for normal playback.
     */
    coverTest?: HarnessMode;
    /** Timing mode: the flagged segments to hide. */
    coverSegments?: FlashSegment[];
    /** Which schedule produced those segments, for the log. */
    scheduleLabel?: string;
    guardBandMs?: number;
    /** Layering mode: how often the cover toggles, milliseconds. */
    toggleEveryMs?: number;
    /** Screen area the cover leaves visible for the camera harness. */
    referencePatch?: ReferencePatch;
  };
};

export type AppStackScreenProps<T extends keyof AppStackParamList> =
  StackScreenProps<AppStackParamList, T>;

export type HomeScreenNavigationProps = StackNavigationProp<
  AppStackParamList,
  Screens.HOME_SCREEN
>;

export type AppDrawerParamList = {
  [Screens.HOME_SCREEN]: undefined;
  [Screens.SETTINGS_SCREEN]: undefined;
  [Screens.SEARCH_SCREEN]: undefined;
  [Screens.FEEDBACK_SCREEN]: undefined;
};

export type AppDrawerScreenProps<T extends keyof AppDrawerParamList> =
  DrawerScreenProps<AppDrawerParamList, T>;

declare global {
  namespace ReactNavigation {
    interface RootParamList extends AppStackParamList {}
  }
}

export interface ButtonConfig {
  onPress: () => void;
  image: ImageSourcePropType;
  label: string;
  ref?: React.RefObject<React.ComponentRef<typeof TouchableOpacity>>;
  testID: string;
}
