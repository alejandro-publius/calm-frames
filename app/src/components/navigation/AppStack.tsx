// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { createStackNavigator } from '@amazon-devices/react-navigation__stack';
import React, { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../store';
import { fetchPlaylists } from '../../store/search/searchSlice';
import { WithSuspense } from '../../utils/WithSuspense';
import AppDrawer from './AppDrawer';
import HarborOpening from '../../calmframes/HarborOpening';
import { AppStackParamList, Screens } from './types';

const DetailsScreen = React.lazy(() => import('../../screens/DetailsScreen'));
const PlayerScreen = React.lazy(() => import('../../screens/PlayerScreen'));
const KidModeScreen = React.lazy(() => import('../../screens/KidModeScreen'));
const SearchResultsScreen = React.lazy(
  () => import('../../screens/SearchResultsScreen'),
);
const FeedBackScreen = React.lazy(() => import('../../screens/FeedbackScreen'));

const Stack = createStackNavigator<AppStackParamList>();
const AppStack = () => {
  const dispatch = useDispatch<AppDispatch>();

  useEffect(() => {
    //fetching local file data for search flow
    dispatch(fetchPlaylists());
  }, [dispatch]);

  const navigationOptions = {
    headerShown: false,
    animationEnabled: false,
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
        component={WithSuspense(KidModeScreen, <HarborOpening />)}
      />
      <Stack.Screen name={Screens.APP_DRAWER} component={AppDrawer} />
      <Stack.Screen
        name={Screens.DETAILS_SCREEN}
        component={WithSuspense(DetailsScreen)}
      />
      <Stack.Screen
        name={Screens.PLAYER_SCREEN}
        component={WithSuspense(PlayerScreen)}
      />

      <Stack.Screen
        name={Screens.SEARCH_RESULTS_SCREEN}
        component={WithSuspense(SearchResultsScreen)}
      />

      <Stack.Screen
        name={Screens.FEEDBACK_SCREEN}
        component={WithSuspense(FeedBackScreen)}
      />
    </Stack.Navigator>
  );
};

export default React.memo(AppStack);
