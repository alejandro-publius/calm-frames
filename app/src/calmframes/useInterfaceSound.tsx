import { useKeplerAppStateManager } from '@amazon-devices/react-native-kepler';
import { createContext, useContext, useEffect, useLayoutEffect, useRef } from 'react';
import { AccessibilityInfo, AppState } from 'react-native';
import { createInterfaceSoundController, InterfaceFeedback } from './interfaceSound';

const silent: InterfaceFeedback = { confirm: () => {}, stop: () => {} };
export const InterfaceSoundContext = createContext<InterfaceFeedback>(silent);
export const useInterfaceFeedback = (): InterfaceFeedback => useContext(InterfaceSoundContext);

/** Unknown app or screen-reader state stays silent. stop() also cancels a pending cue. */
export function useInterfaceSound({ enabled, active }: {
  enabled: boolean;
  active: boolean;
}): InterfaceFeedback {
  const manager = useKeplerAppStateManager();
  const controller = useRef<ReturnType<typeof createInterfaceSoundController> | null>(null);
  if (!controller.current) { controller.current = createInterfaceSoundController(); }
  const state = useRef({
    enabled, active, mounted: false, stopped: false,
    foreground: false, keplerForeground: false, focused: true,
    screenReader: true,
  });
  state.current.enabled = enabled;
  state.current.active = active;
  const reconcile = useRef(() => {});
  reconcile.current = () => {
    const s = state.current;
    controller.current?.setAllowed(s.mounted && s.enabled && s.active && !s.stopped &&
      s.foreground && s.keplerForeground && s.focused && !s.screenReader);
  };
  const feedback = useRef<InterfaceFeedback>({
    confirm: () => {
      reconcile.current();
      controller.current?.confirm();
    },
    stop: () => {
      state.current.stopped = true;
      controller.current?.stop();
    },
  });

  useLayoutEffect(() => {
    state.current.stopped = false;
    reconcile.current();
    return () => controller.current?.stop();
  }, [enabled, active]);

  useEffect(() => {
    const s = state.current;
    s.mounted = true;
    s.screenReader = true;
    let live = true;
    let readerChanged = false;
    const subscriptions: Array<{ remove(): void }> = [];
    try {
      subscriptions.push(AppState.addEventListener('change', (next) => {
        s.foreground = next === 'active';
        reconcile.current();
      }));
      s.foreground = AppState.currentState === 'active';
      subscriptions.push(manager.addEventListener('change', (next) => {
        s.keplerForeground = next === 'active';
        reconcile.current();
      }));
      subscriptions.push(manager.addEventListener('blur', () => {
        s.focused = false;
        reconcile.current();
      }));
      subscriptions.push(manager.addEventListener('focus', () => {
        s.focused = true;
        reconcile.current();
      }));
      s.keplerForeground = manager.getCurrentState() === 'active';
      // SDK 0.24 maps screenReaderChanged to the Kepler native event of the
      // same name. Subscribe before querying so a late query cannot undo it.
      subscriptions.push(AccessibilityInfo.addEventListener('screenReaderChanged', (next) => {
        readerChanged = true;
        s.screenReader = next !== false;
        reconcile.current();
      }));
      AccessibilityInfo.isScreenReaderEnabled().then((next) => {
        if (live && !readerChanged) {
          s.screenReader = next !== false;
          reconcile.current();
        }
      }).catch(() => { /* Unresolved accessibility state stays silent. */ });
    } catch {
      s.screenReader = true;
    }
    reconcile.current();
    return () => {
      live = false;
      s.mounted = false;
      controller.current?.stop();
      for (const subscription of subscriptions) {
        try { subscription.remove(); } catch { /* Nothing left to play. */ }
      }
    };
  }, [manager]);
  return feedback.current;
}
