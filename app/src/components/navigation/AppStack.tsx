// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { createStackNavigator } from '@amazon-devices/react-navigation__stack';
import React from 'react';
import { WithSuspense } from '../../utils/WithSuspense';
import HarborOpening from '../../calmframes/HarborOpening';
import { CALM_WORLD } from '../../calmframes/calmStyles';
import { playerRouteFallback } from './playerRouteFallback';
import { AppStackParamList, Screens } from './types';

const AppDrawer = React.lazy(() => import('./AppDrawer'));
const DetailsScreen = React.lazy(() => import('../../screens/DetailsScreen'));
const PlayerScreen = React.lazy(() => import('../../screens/PlayerScreen'));
const KidModeScreen = React.lazy(() => import('../../screens/KidModeScreen'));
const SearchResultsScreen = React.lazy(
  () => import('../../screens/SearchResultsScreen'),
);
const FeedBackScreen = React.lazy(() => import('../../screens/FeedbackScreen'));

const KidModeRoute = WithSuspense(KidModeScreen, <HarborOpening />);
const LegacyRoute = WithSuspense(AppDrawer);
const DetailsRoute = WithSuspense(DetailsScreen);
const PlayerRoute = WithSuspense(PlayerScreen, playerRouteFallback);
const SearchRoute = WithSuspense(SearchResultsScreen);
const FeedbackRoute = WithSuspense(FeedBackScreen);

const Stack = createStackNavigator<AppStackParamList>();
const AppStack = () => {
  const navigationOptions = {
    headerShown: false,
    animationEnabled: false,
    // The navigator paints before a lazy route. Never expose its near-white default.
    cardStyle: { backgroundColor: CALM_WORLD.BACKGROUND },
  };

  return (
    // Calm Frames opens on Calm Frames. The app is a safety layer with a
    // player behind it, not a player with a safety setting, so the first
    // screen is the first run or the shelf, and the sample's own home is
    // still in this stack behind it.
    <Stack.Navigator
      initialRouteName={Screens.KID_MODE_SCREEN}
      screenOptions={navigationOptions}>
      <Stack.Screen
        name={Screens.KID_MODE_SCREEN}
        component={KidModeRoute}
      />
      <Stack.Screen name={Screens.APP_DRAWER} component={LegacyRoute} />
      <Stack.Screen
        name={Screens.DETAILS_SCREEN}
        component={DetailsRoute}
      />
      <Stack.Screen
        name={Screens.PLAYER_SCREEN}
        component={PlayerRoute}
      />

      <Stack.Screen
        name={Screens.SEARCH_RESULTS_SCREEN}
        component={SearchRoute}
      />

      <Stack.Screen
        name={Screens.FEEDBACK_SCREEN}
        component={FeedbackRoute}
      />
    </Stack.Navigator>
  );
};

export default React.memo(AppStack);
