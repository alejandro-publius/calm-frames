/**
 * Calm Frames, as a person meets it.
 *
 * Until this screen existed the shelf, the details page and the parent area
 * were real, tested components that nothing in the app ever rendered. They
 * could only be reached by a test. This is the route that puts them on the
 * television and hands the player a checked title.
 *
 * One route holds all four states because they share three things: the
 * household setting, the PIN gate and the list of checked titles. Splitting
 * them across four routes would mean passing that between screens, and a
 * screen rendered with a setting that is not the one in force is a screen
 * that can show a title as ready when this household needs it checked again.
 *
 * What it will not do:
 *
 * - it never navigates to the player without the map. The play path builds
 *   the guarded parameters from the same checked title the shelf listed, and
 *   the player refuses to show a picture without them anyway. Two locks,
 *   because the whole project is the claim that nothing plays unchecked;
 * - it never lists a title that did not verify. That is kidModeTitles, and
 *   the parent area is the only place the others appear.
 *
 * Not done yet, and worth knowing: the PIN and the room setting live in
 * memory, so the first run comes back on the next launch. Writing them to
 * /data is a small job and a separate one.
 */

import { RouteProp } from '@amazon-devices/react-navigation__core';
import { StackNavigationProp } from '@amazon-devices/react-navigation__stack';
import React from 'react';
import { BackHandler, Platform } from 'react-native';
import FirstRunScreen, { FirstRunResult } from '../calmframes/FirstRunScreen';
import { DEFAULT_SETTINGS, HouseholdSettings } from '../calmframes/household';
import { useHideLogs } from '../calmframes/hideLogStore';
import KidHomeScreen from '../calmframes/KidHomeScreen';
import {
  activeProfile,
  allProfileHides,
  effectiveSettings,
  Family,
  newFamily,
  Profile,
  selectProfile,
  setFloor,
} from '../calmframes/profiles';
import {
  OFFLINE_PUBLIC_KEY_BASE64,
  OFFLINE_VIDEO_URI,
  offlineTitle,
} from '../calmframes/offlineTitle';
import CreditsScreen from '../calmframes/CreditsScreen';
import ParentAreaScreen from '../calmframes/ParentAreaScreen';
import { emptyPinGate, PinGateState } from '../calmframes/parentGate';
import { CatalogTitle, CheckedTitle, checkTitles } from '../calmframes/titleStatus';
import TitleDetailsScreen from '../calmframes/TitleDetailsScreen';
import {
  AppStackParamList,
  Screens,
} from '../components/navigation/types';
import { TitleData } from '../types/TitleData';

export type KidModeView =
  | 'first-run'
  | 'home'
  | 'details'
  | 'parent'
  | 'credits';

export interface KidModeScreenProps {
  navigation: StackNavigationProp<AppStackParamList, Screens.KID_MODE_SCREEN>;
  route?: RouteProp<AppStackParamList, Screens.KID_MODE_SCREEN>;
  /**
   * The catalog. Defaults to the title bundled inside the package, which is
   * the one that needs no network and no backend, so a judge with the device
   * in flight mode still gets a working kid mode.
   */
  catalog?: CatalogTitle[];
  /** Injected in tests. A device has no crypto API to make a salt with. */
  newSalt?: () => string;
  nowMs?: () => number;
  testID?: string;
}

/** The bundled title, and nothing else until a backend is wired in. */
export function defaultCatalog(): CatalogTitle[] {
  return [offlineTitle(OFFLINE_VIDEO_URI)];
}

/**
 * A salt for a new PIN.
 *
 * Vega has no crypto API, so this is the clock and Math.random together. It
 * does not have to be unguessable: the salt stops one stored hash being
 * compared against another device's, and the thing that stops a child is the
 * rate limit in parentGate.ts.
 */
function makeLocalSalt(): string {
  const noise = Math.floor(Math.random() * 0xffffffff).toString(16);
  return `${Date.now().toString(16)}-${noise}`;
}

/** What the player needs to open a file, from what the catalog published. */
export function titleDataFor(entry: CheckedTitle): TitleData {
  return {
    id: entry.title.id,
    title: entry.title.title,
    description: '',
    mediaType: 'video',
    mediaSourceType: 'url',
    uri: entry.title.uri,
    categories: [],
    channelID: '',
    posterUrl: entry.title.posterUrl ?? '',
    format: 'MP4',
    uhd: false,
    secure: false,
    rentAmount: '',
  };
}

/**
 * The parameters the player needs to run the guard over this title.
 *
 * Built from the checked title itself rather than from anything the caller
 * holds separately, so the map that goes to the player is the map the shelf
 * verified.
 */
export function guardedParamsFor(
  entry: CheckedTitle,
  settings: HouseholdSettings,
  chimeEnabled = true,
  watching?: Profile,
) {
  return {
    sha256: entry.title.sha256,
    maps: entry.title.maps,
    settings,
    durationMs: entry.title.durationMs,
    titleId: entry.title.id,
    // The household switch travels with the title, because the player screen
    // is where the cue is raised and it has no other way to learn the answer.
    chimeEnabled,
    // Who is watching, for the same reason: the player writes the hide log and
    // this is the only way it can know whose sitting it was.
    profileId: watching?.id,
    profileName: watching?.name,
  };
}

const KidModeScreen = ({
  navigation,
  catalog,
  newSalt = makeLocalSalt,
  nowMs = Date.now,
  testID = 'kid-mode',
}: KidModeScreenProps) => {
  // The family is the one record: the household floor, the kids and which of
  // them the shelf is for. The settings the guard runs with are derived from
  // it rather than stored beside it, so there is no second copy to disagree.
  const [family, setFamily] = React.useState<Family>(() => newFamily(DEFAULT_SETTINGS));
  const [gate, setGate] = React.useState<PinGateState>(emptyPinGate());
  // The player covers the flagged parts and knows what it hid. It writes each
  // one into the shared store in hideLogStore.ts, which is a module rather
  // than state on either screen, so a hide survives the player being torn down
  // on the way back here. The logs are kept per profile, so one kid's record
  // cannot land in another's.
  const profileLogs = useHideLogs();
  const [view, setView] = React.useState<KidModeView>('first-run');
  const [openId, setOpenId] = React.useState<string | null>(null);

  const watching = activeProfile(family);
  // Never the kid's own choice on its own: the stricter of the household floor
  // and the profile, which is what makes a profile unable to loosen anything.
  const settings = React.useMemo(
    () => effectiveSettings(family, watching),
    [family, watching],
  );

  const entries = React.useMemo(() => catalog ?? defaultCatalog(), [catalog]);
  const titles = React.useMemo(
    () =>
      checkTitles(entries, {
        settings,
        publicKeyBase64: OFFLINE_PUBLIC_KEY_BASE64,
        nowMs: nowMs(),
      }),
    [entries, settings, nowMs],
  );
  const open = titles.find((entry) => entry.title.id === openId) ?? null;

  // The D-pad back button walks back through these states rather than leaving
  // the app from the middle of them.
  React.useEffect(() => {
    if (!Platform.isTV) {
      return undefined;
    }
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => {
      if (view === 'details' || view === 'parent') {
        setView('home');
        setOpenId(null);
        return true;
      }
      return false;
    });
    return () => subscription.remove();
  }, [view]);

  const finishFirstRun = (result: FirstRunResult) => {
    setGate(result.gate);
    // The first run sets the floor, not one kid's settings. Every profile is
    // measured against it afterwards and the stricter one wins.
    setFamily((previous) => setFloor(previous, result.settings));
    setView('home');
  };

  const play = (entry: CheckedTitle) => {
    navigation.navigate(Screens.PLAYER_SCREEN, {
      data: titleDataFor(entry),
      guarded: guardedParamsFor(
        entry,
        settings,
        family.chimeEnabled !== false,
        watching,
      ),
    });
  };

  if (view === 'first-run') {
    return (
      <FirstRunScreen
        testID={`${testID}-first-run`}
        onDone={finishFirstRun}
        newSalt={newSalt}
        settings={settings}
      />
    );
  }

  if (view === 'parent') {
    return (
      <ParentAreaScreen
        testID={`${testID}-parent`}
        gate={gate}
        onGateChange={setGate}
        settings={family.floor}
        onSettingsChange={(next) => setFamily(setFloor(family, next))}
        log={allProfileHides(profileLogs)}
        family={family}
        onFamilyChange={setFamily}
        profileLogs={profileLogs}
        titles={titles}
        nowMs={nowMs}
        onBack={() => setView('home')}
        onSetPin={() => setView('first-run')}
        onCredits={() => setView('credits')}
      />
    );
  }

  // Behind the PIN on purpose. The credits are a parent's screen, and CC BY
  // asks for attribution somewhere a person can actually read it, which NOTICE
  // in the repository is not for somebody holding a remote.
  if (view === 'credits') {
    return (
      <CreditsScreen
        testID={`${testID}-credits`}
        onBack={() => setView('parent')}
      />
    );
  }

  if (view === 'details' && open) {
    return (
      <TitleDetailsScreen
        testID={`${testID}-details`}
        entry={open}
        settings={settings}
        onPlay={play}
        onBack={() => {
          setOpenId(null);
          setView('home');
        }}
      />
    );
  }

  return (
    <KidHomeScreen
      testID={`${testID}-home`}
      titles={titles}
      profiles={family.profiles}
      activeProfileId={family.activeProfileId}
      onChooseProfile={(profile) => setFamily(selectProfile(family, profile.id))}
      onOpen={(entry) => {
        setOpenId(entry.title.id);
        setView('details');
      }}
      onOpenParentArea={() => setView('parent')}
    />
  );
};

export default KidModeScreen;
