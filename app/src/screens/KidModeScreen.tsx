import { titlePresentation } from '../calmframes/TitleArtwork';
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
 * Household setup is restored before the shelf opens. Storage failures keep
 * it closed rather than replacing the saved floor or PIN with defaults.
 */

import { RouteProp } from '@amazon-devices/react-navigation__core';
import { StackNavigationProp } from '@amazon-devices/react-navigation__stack';
import React from 'react';
import { BackHandler, Platform } from 'react-native';
import { trace } from '../calmframes/trace';
import HouseholdStorageScreen from '../calmframes/HouseholdStorageScreen';
import {
  deviceHouseholdStorage,
  HouseholdStorage,
} from '../calmframes/householdStorage';
import { useSavedHousehold } from '../calmframes/useSavedHousehold';
import { InterfaceSoundContext, useInterfaceSound } from '../calmframes/useInterfaceSound';
import FirstRunScreen, { FirstRunResult } from '../calmframes/FirstRunScreen';
import {
  DEFAULT_SETTINGS,
  HouseholdSettings,
  PRESETS,
} from '../calmframes/household';
import { forgetProfile, useHideLogs } from '../calmframes/hideLogStore';
import {
  refusedTitle,
  useMapSources,
  waitingTitle,
} from '../calmframes/mapSource';
import KidHomeScreen, { ReturnFocusControl } from '../calmframes/KidHomeScreen';
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
import {
  benignStoryTitle,
  benignStorySettings,
  bundledTitlePublicKey,
  isBundledBenignStory,
} from '../calmframes/benignStory';
import ParentAreaScreen from '../calmframes/ParentAreaScreen';
import { emptyPinGate, PinGateState } from '../calmframes/parentGate';
import {
  CatalogTitle,
  CheckedTitle,
  checkTitle,
  kidModeTitles,
} from '../calmframes/titleStatus';
import TitleDetailsScreen from '../calmframes/TitleDetailsScreen';
import { AppStackParamList, Screens } from '../components/navigation/types';
import { TitleData } from '../types/TitleData';
import { concernsPackagedLibrary, packagedLibrary } from '../calmframes/packagedLibrary';

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
   * The catalog. Defaults to the titles bundled inside the package, which
   * need no network and no backend, so a judge with the device
   * in flight mode still gets a working kid mode.
   */
  catalog?: CatalogTitle[];
  /**
   * Where the signed index of checked titles is.
   *
   * Left out, no index is consulted and every title plays off the map the
   * package or the catalog carried, which is what the app does today. Set, the
   * index is asked about every title first, by the file's hash, and mapSource.ts
   * says what a missing entry does and what a tampered one does. No index has
   * been published yet, so nothing in this repository sets it.
   */
  registryUrl?: string;
  /** Injected so tests do not need a network and a device does not need one. */
  fetchText?: (url: string) => Promise<string | null>;
  /**
   * The public key this build trusts.
   *
   * The app never passes it: the key it ships is the default. It is a prop so
   * that a test can drive the whole shelf against the signed fixtures, which
   * were made with a key whose private half is in nobody's tree.
   */
  publicKeyBase64?: string;
  /** Injected in tests. A device has no crypto API to make a salt with. */
  newSalt?: () => string;
  nowMs?: () => number;
  testID?: string;
  /** Tests can provide local storage without a native device. */
  householdStorage?: HouseholdStorage;
}

/**
 * The bundled demos and checked prepared library are available offline.
 *
 * The order is the shelf's order, and the first title the shelf lists takes
 * the D-pad focus. Harbor leads because it is the one that shows the whole
 * journey: captions, a countdown and a practice hold. The gradient has none of
 * those, so it goes last, where it still proves a title plays with no network.
 */
export function defaultCatalog(settings = DEFAULT_SETTINGS): CatalogTitle[] {
  return [
    benignStoryTitle(),
    ...packagedLibrary.titles(settings),
    offlineTitle(OFFLINE_VIDEO_URI),
  ];
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
    title: titlePresentation(entry.title).name,
    description: '',
    mediaType: 'video',
    mediaSourceType: 'url',
    uri: entry.title.uri,
    textTrack: entry.title.textTrack,
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
    renditionSha256: entry.title.renditionSha256,
    renditionStartOffsetMs: entry.title.renditionStartOffsetMs,
    maps: entry.title.maps,
    settings: benignStorySettings(entry.title, settings),
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
  registryUrl,
  fetchText,
  publicKeyBase64 = OFFLINE_PUBLIC_KEY_BASE64,
  newSalt = makeLocalSalt,
  nowMs = Date.now,
  testID = 'kid-mode',
  householdStorage = deviceHouseholdStorage,
}: KidModeScreenProps) => {
  // The family is the one record: the household floor, the kids and which of
  // them the shelf is for. The settings the guard runs with are derived from
  // it rather than stored beside it, so there is no second copy to disagree.
  const saved = useSavedHousehold(householdStorage);
  const committedFamily = saved.value?.family;
  const previousFamily = React.useRef<Family | null>(null);
  React.useEffect(() => {
    if (!committedFamily) {
      return;
    }
    const previous = previousFamily.current;
    previousFamily.current = committedFamily;
    for (const profile of previous?.profiles ?? []) {
      if (!committedFamily.profiles.some((one) => one.id === profile.id)) {
        forgetProfile(profile.id);
      }
    }
  }, [committedFamily]);
  const family = saved.value?.family ?? newFamily(DEFAULT_SETTINGS);
  const gate = saved.value?.gate ?? emptyPinGate();
  const [interfaceActive, setInterfaceActive] = React.useState(
    () => navigation.isFocused?.() !== false,
  );
  const interfaceSound = useInterfaceSound({
    enabled: Boolean(saved.value && family.interfaceSoundsEnabled === true &&
      (saved.phase === 'ready' || saved.phase === 'saving')),
    active: interfaceActive,
  });
  // A saved change is confirmed from the render that holds the saved record,
  // not from the write's own continuation. On the concurrent root the device
  // uses, that continuation runs before React has rendered the record, so the
  // hook would still read the old one, and the press that turns the sound on
  // would be the one press it never confirmed.
  const [confirmSavedChange, setConfirmSavedChange] = React.useState(false);
  React.useEffect(() => {
    if (confirmSavedChange) {
      setConfirmSavedChange(false);
      interfaceSound.confirm();
    }
  }, [confirmSavedChange, interfaceSound]);
  const setFamily = (next: Family) => {
    if (saved.phase === 'ready' && saved.value) {
      saved.write({ ...saved.value, family: next }).then((accepted) => {
        if (accepted && next.interfaceSoundsEnabled === true) {
          setConfirmSavedChange(true);
        }
      });
    }
  };
  const setGate = async (next: PinGateState) => {
    if (
      !saved.value ||
      saved.phase !== 'ready' ||
      !(await saved.write({ ...saved.value, gate: next }))
    ) {
      throw new Error('PIN state was not saved');
    }
  };
  // The player covers the flagged parts and knows what it hid. It writes each
  // one into the shared store in hideLogStore.ts, which is a module rather
  // than state on either screen, so a hide survives the player being torn down
  // on the way back here. The logs are kept per profile, so one kid's record
  // cannot land in another's.
  const profileLogs = useHideLogs();
  const [view, setView] = React.useState<KidModeView>('home');
  React.useEffect(() => { trace('screen', view); }, [view]);
  const [openId, setOpenId] = React.useState<string | null>(null);
  const [lastOpenedId, setLastOpenedId] = React.useState<string | null>(null);
  const [lastOpenedFrom, setLastOpenedFrom] = React.useState<ReturnFocusControl | undefined>(undefined);
  // The control the shelf reported for the press being handled now; a press
  // that reports none, such as one from the introduction, clears it.
  const launchControl = React.useRef<ReturnFocusControl | undefined>(undefined);
  const rememberLaunch = (entry: CheckedTitle) => {
    setLastOpenedId(entry.title.id);
    setLastOpenedFrom(launchControl.current);
    launchControl.current = undefined;
  };
  // Details offers the practice demo beside Play. Opening it keeps the page
  // it came from, so Back returns there, one level at a time, with focus on
  // the control that was pressed rather than on Play.
  const [practiceFromId, setPracticeFromId] = React.useState<string | null>(null);
  const [detailsFocus, setDetailsFocus] = React.useState<'play' | 'practice'>('play');
  const [focusGeneration, setFocusGeneration] = React.useState(0);
  React.useEffect(() => {
    const removeFocus = navigation.addListener?.('focus', () => {
      // Vega keeps this route mounted behind the player. Restore its controls
      // on return, and permit menu feedback only while this route is active.
      setInterfaceActive(true);
      setFocusGeneration((generation) => generation + 1);
    });
    const removeBlur = navigation.addListener?.('blur', () => {
      interfaceSound.stop();
      setInterfaceActive(false);
    });
    return () => { removeFocus?.(); removeBlur?.(); };
  }, [navigation, interfaceSound]);

  const watching = activeProfile(family);
  // Never the kid's own choice on its own: the stricter of the household floor
  // and the profile, which is what makes a profile unable to loosen anything.
  const settings = React.useMemo(
    () => effectiveSettings(family, watching),
    [family, watching],
  );

  const entries = React.useMemo(() => catalog ?? defaultCatalog(settings), [catalog, settings]);
  // Where each title's map comes from: the signed index first, by the file's
  // hash, then the map the package or the catalog carried. With no index
  // configured this is the catalog itself and nothing is fetched.
  const resolved = useMapSources(entries, {
    registryUrl,
    publicKeyBase64,
    nowMs,
    profiles: (PRESETS[settings.preset] ?? PRESETS.wcag).mapProfiles,
    fetchText,
  });
  // Three answers: the index refused and nothing may be served, the index has
  // been asked and has not answered, or there is a map to check. Only the last
  // can reach the shelf, because only a verified title is listed.
  const titles = React.useMemo(
    () =>
      resolved.map((one) => {
        if (one.refusal) {
          return refusedTitle(one);
        }
        if (one.waiting) {
          return waitingTitle(one.title);
        }
        return checkTitle(one.title, {
          settings: benignStorySettings(one.title, settings),
          publicKeyBase64: concernsPackagedLibrary(one.title)
            ? packagedLibrary.publicKeyFor(one.title, settings) ?? ''
            : bundledTitlePublicKey(one.title, publicKeyBase64),
          nowMs: nowMs(),
        });
      }),
    [resolved, settings, publicKeyBase64, nowMs],
  );
  const open = titles.find((entry) => entry.title.id === openId) ?? null;
  const practice = React.useMemo(
    () => kidModeTitles(titles).find((entry) => isBundledBenignStory(entry.title)) ?? null,
    [titles],
  );
  const leaveDetails = () => {
    if (practiceFromId) {
      setOpenId(practiceFromId);
      setPracticeFromId(null);
      setDetailsFocus('practice');
      return;
    }
    setOpenId(null);
    setView('home');
  };

  // The D-pad back button walks back through these states rather than leaving
  // the app from the middle of them.
  React.useEffect(() => {
    if (!Platform.isTV) {
      return undefined;
    }
    const subscription = BackHandler.addEventListener(
      'hardwareBackPress',
      () => {
        if (navigation.isFocused?.() === false) {
          return false;
        }
        if (view === 'credits') {
          setView('parent');
          interfaceSound.confirm();
          return true;
        }
        if (view === 'details') {
          if (practiceFromId) {
            setOpenId(practiceFromId);
            setPracticeFromId(null);
            setDetailsFocus('practice');
          } else {
            setView('home');
            setOpenId(null);
          }
          interfaceSound.confirm();
          return true;
        }
        if (view === 'parent') {
          setView('home');
          setOpenId(null);
          interfaceSound.confirm();
          return true;
        }
        return false;
      },
    );
    return () => subscription.remove();
  }, [navigation, view, interfaceSound, practiceFromId]);

  const finishFirstRun = (result: FirstRunResult) => {
    // The first run sets the floor, not one kid's settings. Every profile is
    // measured against it afterwards and the stricter one wins.
    saved.write({
      version: 1,
      gate: result.gate,
      family: setFloor(family, result.settings),
    });
    // On a fresh device the first run is on screen because nothing is saved
    // yet, and the view never left the shelf. From the parent area's Set a
    // PIN it is on screen because the view was set to it on purpose, and
    // nothing else sets it back, so without this a parent who finished stayed
    // on the explainer with the PIN already saved. A write that fails still
    // puts the storage screen over everything, and its retry carries this
    // same record.
    setView('home');
  };

  const play = (entry: CheckedTitle) => {
    if (saved.phase !== 'ready' || !saved.value) {
      return;
    }
    // Invalidate pending menu audio before the player can request audio focus.
    interfaceSound.stop();
    setInterfaceActive(false);
    navigation.navigate(Screens.PLAYER_SCREEN, {
      data: titleDataFor(entry),
      showHomeOpening: true,
      guarded: guardedParamsFor(
        entry,
        settings,
        family.chimeEnabled !== false,
        watching,
      ),
    });
  };

  const withInterfaceFeedback = (content: React.ReactElement) => (
    <InterfaceSoundContext.Provider value={interfaceSound}>
      {content}
    </InterfaceSoundContext.Provider>
  );

  if (
    saved.phase === 'loading' ||
    saved.phase === 'error' ||
    (saved.phase === 'saving' && !saved.value)
  ) {
    return withInterfaceFeedback(
      <HouseholdStorageScreen
        testID={`${testID}-storage`}
        failed={saved.phase === 'error'}
        onRetry={saved.retry}
      />
    );
  }

  if (!saved.value || view === 'first-run') {
    return withInterfaceFeedback(
      <FirstRunScreen
        testID={`${testID}-first-run`}
        onDone={finishFirstRun}
        // Opened from the parent area's Set a PIN: Back on the first step
        // returns there. On a fresh device there is nowhere else to go.
        onCancel={saved.value ? () => setView('parent') : undefined}
        newSalt={newSalt}
        settings={settings}
      />
    );
  }

  if (view === 'parent') {
    return withInterfaceFeedback(
      <ParentAreaScreen
        saving={saved.phase === 'saving'}
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
    return withInterfaceFeedback(
      <CreditsScreen
        testID={`${testID}-credits`}
        onBack={() => setView('parent')}
      />
    );
  }

  if (view === 'details' && open) {
    return withInterfaceFeedback(
      <TitleDetailsScreen
        key={`details-${focusGeneration}-${open.title.id}`}
        saving={saved.phase === 'saving'}
        interfaceMotionEnabled={family.interfaceMotionEnabled === true}
        interfaceActive={interfaceActive}
        testID={`${testID}-details`}
        entry={open}
        settings={settings}
        onPlay={(entry) => {
          setDetailsFocus('play');
          play(entry);
        }}
        practice={practice ?? undefined}
        preferPracticeFocus={detailsFocus === 'practice'}
        onOpenPractice={(entry) => {
          setPracticeFromId(open.title.id);
          setDetailsFocus('play');
          setOpenId(entry.title.id);
        }}
        onBack={leaveDetails}
      />
    );
  }

  return withInterfaceFeedback(
    <KidHomeScreen
      key={`home-${focusGeneration}`}
      saving={saved.phase === 'saving'}
      interfaceMotionEnabled={family.interfaceMotionEnabled === true}
      interfaceActive={interfaceActive}
      testID={`${testID}-home`}
      titles={titles}
      onLaunchControl={(control) => { launchControl.current = control; }}
      onPlay={(entry) => {
        rememberLaunch(entry);
        play(entry);
      }}
      returnFocusId={lastOpenedId}
      returnFocusControl={lastOpenedFrom}
      profiles={family.profiles}
      activeProfileId={family.activeProfileId}
      onChooseProfile={(profile) =>
        setFamily(selectProfile(family, profile.id))
      }
      onOpen={(entry) => {
        rememberLaunch(entry);
        setPracticeFromId(null);
        setDetailsFocus('play');
        setOpenId(entry.title.id);
        setView('details');
      }}
      onOpenParentArea={() => {
        setLastOpenedFrom('parent');
        setView('parent');
      }}
    />
  );
};

export default KidModeScreen;
