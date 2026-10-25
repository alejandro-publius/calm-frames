// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { ThemeProvider } from '@amazon-devices/kepler-ui-components';
import {
  Platform,
  useHideSplashScreenCallback,
  usePreventHideSplashScreen,
} from '@amazon-devices/react-native-kepler';
import { NavigationContainer } from '@amazon-devices/react-navigation__native';
import { Store } from '@reduxjs/toolkit';
import React, { useEffect, useMemo, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { Provider } from 'react-redux';
import AppStack from './components/navigation/AppStack';
import HarborOpening from './calmframes/HarborOpening';
import { CALM_WORLD } from './calmframes/calmStyles';
import { CalmControlAppearance } from './calmframes/CalmControlSurface';
import { initializeStore } from './store';
import { createTheme } from './styles/ThemeBuilders';

const App = () => {
  const [store, setStore] = useState<Store | null>(null);
  const isTv = Platform.isTV;
  const preventHideSplashScreen = usePreventHideSplashScreen;
  const hideSplashScreen = useHideSplashScreenCallback();

  if (isTv) {
    preventHideSplashScreen();
  }

  const initStore = async () => {
    const initializedStore = await initializeStore();
    setStore(initializedStore);
  };

  useEffect(() => {
    initStore();
  }, []);

  const theme = useMemo(() => createTheme(), []);

  return (
    <CalmControlAppearance.Provider value>
    <View testID="app-root" style={styles.root} onLayout={hideSplashScreen}>
      {store ? (
        <Provider store={store}>
          <ThemeProvider theme={theme}>
            <NavigationContainer>
              <AppStack />
            </NavigationContainer>
          </ThemeProvider>
        </Provider>
      ) : <HarborOpening />}
    </View>
    </CalmControlAppearance.Provider>
  );
};

const styles = StyleSheet.create({ root: { flex: 1, backgroundColor: CALM_WORLD.BACKGROUND } });
export default App;
