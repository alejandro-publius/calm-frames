/**
 * What the player route shows while its module loads.
 *
 * PlayerScreen is lazy, and Metro's import() is an async function: it returns
 * a pending promise even for a module already in the bundle, and the first
 * load evaluates the player's own modules. (Not Shaka's compiled player on the
 * MP4 path: Metro's default inline requires load it only inside the HLS and
 * DASH branch of VideoHandler.) So the first Watch of a session
 * always renders this route's Suspense fallback before the player itself. The
 * default fallback is the opaque black loading screen, which put a black
 * frame between the harbor details page and the player's own harbor opening.
 *
 * A route that will open on that harbor scene shows the same scene while it
 * loads, so Watch answers at once and nothing goes blank. Its status is not a
 * live region: the player's own opening announces it once. Back here simply
 * leaves the route; there is no player yet to tear down. Any other route keeps
 * the default fallback.
 */

import React from 'react';
import PlayerOpening from '../../calmframes/PlayerOpening';
import { AppStackScreenProps, Screens } from './types';

export function playerRouteFallback({
  navigation,
  route,
}: AppStackScreenProps<Screens.PLAYER_SCREEN>): React.ReactNode {
  if (route?.params?.showHomeOpening !== true) {
    return undefined;
  }
  return (
    <PlayerOpening
      title={route.params.data.title}
      menuArt={route.params.data.calmMenuArt}
      onBack={() => navigation.goBack()}
      liveStatus={false}
    />
  );
}
