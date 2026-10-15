// jest.setup.js or setupTests.js

import { configure } from '@testing-library/react-native';
import { HWEvent } from '@amazon-devices/react-native-kepler';

// Configure RNTL for RN 0.83 + Kepler runtime compatibility
(configure as any)({
  hostComponentNames: {
    text: 'Text',
    textInput: 'TextInput',
    switch: 'Switch',
    scrollView: 'ScrollView',
    modal: 'Modal',
  },
});

class MockContentRatingBuilder {
  ratingsSystem() {
    return this;
  }
  rating() {
    return this;
  }
  build() {
    return {};
  }
}
const MOCK_CONTENT_RATING_BUILDER = new MockContentRatingBuilder();
beforeEach(() => {
  expect.hasAssertions();
});

// Add spyOn here
jest.spyOn(console, 'warn').mockImplementation(() => {});
jest.spyOn(console, 'error').mockImplementation(() => {});
export const consoleInfoSpy = jest
  .spyOn(console, 'info')
  .mockImplementation(() => {});

// Add mocks of libraries here
jest.mock('@amazon-devices/react-native-vector-icons/MaterialIcons', () =>
  jest.requireMock('./test/helperMocks/MockMaterialIcons'),
);
jest.mock('@amazon-devices/kepler-content-personalization', () => ({
  __esModule: true,
  PlaybackState: jest.fn(),
  ContentPersonalizationServer: {
    reportNewContentEntitlement: jest.fn(),
    reportRemovedContentEntitlement: jest.fn(),
    reportNewCustomerListEntry: jest.fn(),
    reportRemovedCustomerListEntry: jest.fn(),
    reportNewContentInteraction: jest.fn(),
    reportRefreshedCustomerList: jest.fn(),
    reportRefreshedContentEntitlements: jest.fn(),
    reportRefreshedPlaybackEvents: jest.fn(),
  },
  ContentInteractionType: {
    INGRESS: 'INGRESS',
  },
  CustomerListType: {
    WATCHLIST: 'WATCHLIST',
  },
  ContentIdNamespaces: {
    NAMESPACE_CDF_ID: 'NAMESPACE_CDF_ID',
  },
}));
jest.mock('@amazon-devices/kepler-epg-provider', () => ({
  __esModule: true,
  ChannelDescriptorBuilder: jest.fn(),
  IChannelDescriptor: jest.fn(),
}));
jest.mock('@amazon-devices/react-native-w3cmedia', () => ({
  __esModule: true,
  KeplerVideoSurfaceView: ({
    onSurfaceViewCreated,
    onSurfaceViewDestroyed,
  }: {
    onSurfaceViewCreated: (_surfaceHandle: string) => void;
    onSurfaceViewDestroyed: (_surfaceHandle: string) => void;
  }) => {
    onSurfaceViewCreated('SurfaceViewCreated');
    onSurfaceViewDestroyed('SurfaceViewDestroyed');
    return null;
  },
  KeplerCaptionsView: ({
    onCaptionViewCreated,
    onCaptionViewDestroyed,
  }: {
    onCaptionViewCreated: ((captionsViewHandle: string) => void) | undefined;
    onCaptionViewDestroyed: (captionsHandle: string) => void;
  }) => {
    onCaptionViewCreated?.('CaptionViewCreated');
    onCaptionViewDestroyed?.('CaptionViewDestroyed');
    return null;
  },
  VideoPlayer: jest.fn().mockImplementation(() => ({
    destroyVideoElements: jest.fn(),
    preBufferVideo: jest.fn(),
  })),
  // The real base class carries these on its prototype. Calm Frames subclasses
  // it in SafeMediaControlHandler, so the mock has to be a class, and its
  // methods have to be prototype methods: instance fields would shadow the
  // subclass overrides and a test would be measuring the mock.
  KeplerMediaControlHandler: class KeplerMediaControlHandler {
    async handlePlay() {}
    async handlePause() {}
    async handleStop() {}
    async handleTogglePlayPause() {}
    async handleStartOver() {}
    async handleFastForward() {}
    async handleRewind() {}
    async handleSeek() {}
    async handleSkipForward() {}
    async handleSkipBackward() {}
  },
}));
jest.mock('@amazon-devices/lottie-react-native', () => ({
  __esModule: true,
  default: jest.fn(),
}));
jest.mock('@amazon-devices/react-native-kepler', () => {
  return {
    __esModule: true,
    HWEvent: jest.fn(),
    KeplerAppStateChangeData: jest.fn(),
    useCallback: jest.fn(),
    useTVEventHandler: jest.fn((evt: HWEvent) => {
      return evt;
    }),
    useKeplerAppStateManager: jest.fn().mockReturnValue({
      getComponentInstance: jest.fn().mockReturnValue({
        setSurfaceHandle: jest.fn(),
        setCaptionViewHandle: jest.fn(),
      }),
      addAppStateListener: jest.fn().mockReturnValue({
        remove: jest.fn(),
      }),
    }),
    TVFocusGuideView: jest.fn(),
    default: jest.fn(),
  };
});
jest.mock('lodash', () => ({
  isEqual: jest.fn(() => true),
}));
jest.mock('@amazon-devices/react-native-device-info', () => ({
  getApplicationName: jest.fn().mockResolvedValue('Test Application'),
  getModel: jest.fn().mockResolvedValue('Test Model'),
  getSystemName: jest.fn().mockResolvedValue('Test System'),
  getVersion: jest.fn().mockResolvedValue('1.0'),
  getDeviceType: jest.fn().mockResolvedValue('Test Device'),
  getBaseOs: jest.fn().mockResolvedValue('Test Base OS'),
  getManufacturer: jest.fn().mockResolvedValue('Test Manufacturer'),
}));
jest.mock('@amazon-devices/react-native-gesture-handler', () => ({
  GestureHandlerRootView: 'GestureHandlerRootView',
  TapGestureHandler: 'TapGestureHandler',
  PanGestureHandler: 'PanGestureHandler',
  State: {
    UNDETERMINED: 0,
    FAILED: 1,
    BEGAN: 2,
    CANCELLED: 3,
    ACTIVE: 4,
    END: 5,
  },
}));
jest.mock('@amazon-devices/react-native-localize', () => ({
  getCountry: jest.fn(),
  getLocales: jest.fn(),
}));
jest.mock('@amazon-devices/keplerscript-netmgr-lib', () => ({
  __esModule: true,
  fetch: jest.fn(),
  NetInfoConnectedDetails: jest.fn(),
  NetInfoState: jest.fn(),
  refresh: jest.fn(),
}));
jest.mock('@amazon-devices/react-navigation__core', () => ({
  __esModule: true,
  useFocusEffect: jest.fn(),
}));
jest.mock('@amazon-devices/kepler-file-system', () => ({
  handleReadFileAsString: jest.fn(() => null),
  handleGetEntries: jest.fn(() => null),
}));
jest.mock('react-redux', () => ({
  useDispatch: jest.fn(),
  useSelector: jest.fn(),
}));
jest.mock('@amazon-devices/react-navigation__native', () => ({
  ...jest.requireActual('@amazon-devices/react-navigation__native'),
  useNavigation: jest.fn(),
}));

jest.mock('@amazon-devices/react-navigation__drawer', () => ({
  useDrawerStatus: jest.fn().mockReturnValue('closed'),
}));
jest.mock('react-native-event-listeners', () => ({
  EventRegister: {
    addEventListener: jest.fn((_eventName) => {
      return 'mockListenerId';
    }),
    removeEventListener: jest.fn(),
  },
}));
jest.mock('@amazon-devices/kepler-performance-api', () => ({
  useReportFullyDrawn: jest.fn().mockReturnValue(jest.fn()),
}));

jest.mock('./src/utils/lodashHelper', () => ({
  areComponentPropsEqual: jest.fn((prevProps, nextProps) => {
    return JSON.stringify(prevProps) === JSON.stringify(nextProps);
  }),
}));

jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  RN.Animated.timing = jest.fn().mockReturnValue({
    start: jest.fn(),
  });
  RN.Dimensions = {
    get: jest.fn().mockReturnValue({ width: 1920, height: 1080, scale: 1, fontScale: 1 }),
    set: jest.fn(),
    addEventListener: jest.fn(() => ({ remove: jest.fn() })),
    removeEventListener: jest.fn(),
  };
  RN.PixelRatio = {
    get: jest.fn().mockReturnValue(1),
    getFontScale: jest.fn().mockReturnValue(1),
    getPixelSizeForLayoutSize: jest.fn((size: number) => size),
    roundToNearestPixel: jest.fn((uxUnit: number) => uxUnit),
  };

  return RN;
});
jest.mock('./src/utils/pixelUtils', () => {
  return {
    scaleUxToDp: jest.fn((uxUnit: number) => uxUnit),
  };
});
jest.mock('@amazon-devices/react-navigation__stack', () => ({
  Header: jest.fn(),
}));
jest.mock('react-native-responsive-screen', () => ({
  heightPercentageToDP: jest.fn(),
  widthPercentageToDP: jest.fn(),
}));
jest.mock('@amazon-devices/react-native-svg', () => ({
  Path: jest.fn(),
  Svg: jest.fn(),
}));

// Add mocks of internal files here
jest.mock('./src/iap/utils/IAPManager', () => ({
  IAPManager: {
    getPurchaseUpdates: jest.fn(),
    triggerPurchase: jest.fn(),
  },
}));
jest.mock('./src/iap/IAPConstants', () => ({
  IAPConstants: {
    MONTHLY_SUBSCRIPTION_SKU: 'monthly_subscription_sku',
    PURCHASE_TITLE_SKU: 'purchase_title_sku',
  },
}));
jest.mock('./src/config/AppConfig', () => ({
  isContentPersonalizationEnabled: jest.fn(() => true),
  isInAppPurchaseEnabled: jest.fn(() => true),
  // Calm Frames removed the account login service component, so this is off.
  isAccountLoginEnabled: jest.fn(() => false),
  isDpadControllerSupported: jest.fn(() => true),
  isChannelTuningV2Enabled: jest.fn(() => true),
}));
jest.mock('./src/w3cmedia/shakaplayer/ShakaPlayer', () => ({
  ShakaPlayer: jest.fn(),
}));
jest.mock('./src/components/MovieCarousel', () => 'MovieCarousel');

jest.mock('./src/services/dataProviderFactory', () => ({
  createDataProvider: jest.fn(() => ({
    fetchData: jest.fn(),
  })),
}));
jest.mock('./src/components/rotator/AutoRotator', () => 'AutoRotator');
jest.mock('./src/components/miniDetails/MiniDetails', () => 'MiniDetails');
jest.mock('./src/components/RadioPicker', () => 'RadioPicker');
jest.mock('./src/components/GradientButton', () => 'GradientButton');

jest.mock('@amazon-devices/react-linear-gradient', () => 'LinearGradient');

jest.mock('@amazon-devices/security-manager-lib', () => ({
  SecurityManager: {
    getPrivilegeState: jest.fn(() => Promise.resolve('ALLOW')),
    requestPrivilege: jest.fn(() => Promise.resolve('ALLOW')),
  },
  PrivilegeState: {
    ALLOW: 'ALLOW',
    DENY: 'DENY',
    UNKNOWN: 'UNKNOWN',
  },
}));

// Tests must never reach for a measurement run. readHarnessConfig asks the
// device and then the network, and in CI that fetch fails and logs after the
// test that started it has finished, which jest counts as an error. The
// dedicated tests for this module call jest.unmock to get the real one.
jest.mock('./src/calmframes/harnessConfig', () => ({
  ...jest.requireActual('./src/calmframes/harnessConfig'),
  readHarnessConfig: jest.fn().mockResolvedValue(null),
}));

// The bring-up beacon posts to the machine running a device session. A unit
// test has no business opening a socket, and a fetch that outlives the test
// that started it makes jest leave a worker behind.
import { setBeaconEnabled } from './src/calmframes/timingLog';
import { setTraceEnabled } from './src/calmframes/trace';
setBeaconEnabled(false);
setTraceEnabled(false);
