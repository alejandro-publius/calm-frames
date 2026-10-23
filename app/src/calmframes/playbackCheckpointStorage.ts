import { createCheckpointStore } from './playbackCheckpoint';
import { deviceHouseholdStorage } from './householdStorage';
/** One write queue across old/new player instances, separate from household settings. */
export const deviceCheckpointStore = createCheckpointStore(deviceHouseholdStorage);
