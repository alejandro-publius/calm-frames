import React from 'react';
import {
  HouseholdStorage,
  loadHousehold,
  saveHousehold,
  SavedHousehold,
} from './householdStorage';

export type HouseholdStoragePhase = 'loading' | 'ready' | 'saving' | 'error';

/** Do not expose a default shelf or replace a failed write with older settings. */
export function useSavedHousehold(storage: HouseholdStorage) {
  const [value, setValue] = React.useState<SavedHousehold | null>(null);
  const [phase, setPhase] = React.useState<HouseholdStoragePhase>('loading');
  const phaseRef = React.useRef<HouseholdStoragePhase>('loading');
  const pending = React.useRef<SavedHousehold | null>(null);
  const mounted = React.useRef(false);
  const operation = React.useRef(0);

  const mark = React.useCallback((next: HouseholdStoragePhase) => {
    phaseRef.current = next;
    if (mounted.current) {
      setPhase(next);
    }
  }, []);

  const read = React.useCallback(async () => {
    const token = ++operation.current;
    mark('loading');
    try {
      const saved = await loadHousehold(storage);
      if (mounted.current && token === operation.current) {
        setValue(saved);
        mark('ready');
      }
    } catch {
      if (token === operation.current) {
        mark('error');
      }
    }
  }, [storage, mark]);

  React.useEffect(() => {
    mounted.current = true;
    read();
    return () => {
      mounted.current = false;
      operation.current += 1;
    };
  }, [read]);

  const write = React.useCallback(
    async (next: SavedHousehold): Promise<boolean> => {
      if (phaseRef.current === 'saving' || phaseRef.current === 'loading') {
        return false;
      }
      pending.current = next;
      const token = ++operation.current;
      mark('saving');
      try {
        await saveHousehold(storage, next);
        if (mounted.current && token === operation.current) {
          setValue(next);
          pending.current = null;
          mark('ready');
          return true;
        }
      } catch {
        if (token === operation.current) {
          mark('error');
        }
      }
      return false;
    },
    [storage, mark],
  );

  const retry = React.useCallback(() => {
    if (phaseRef.current !== 'error') {
      return;
    }
    // Retain the intended change. Loading the older disk record would lose it.
    if (pending.current) {
      write(pending.current);
    } else {
      read();
    }
  }, [read, write]);

  return { value, phase, write, retry };
}
