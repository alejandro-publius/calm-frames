/**
 * The local PIN on the parent area.
 *
 * This is a lock on a shelf, not an account. There is no server, no recovery
 * question and nothing leaves the device. What it has to do is stop a child
 * from changing the setting that protects them, and it has to keep doing that
 * after someone reads the device's storage.
 *
 * So the PIN is never stored. What is stored is a salted hash of it, with the
 * hash iterated enough to make guessing a four digit PIN from the stored value
 * slow, and entries are rate limited so guessing at the keypad is slow too.
 *
 * Nothing here protects against someone who can run code on the device. It is
 * not meant to.
 */

import { bytesToHex, sha512 } from './sha512';
import { utf8Bytes } from './canonicalJson';

export const PIN_LENGTH = 4;
/**
 * How many times the hash is applied.
 *
 * Measured here: 5000 rounds of this SHA-512 takes 777 ms on the build
 * machine, and a stick is slower, so 1000 rounds is about the most a parent
 * should wait to open the area.
 *
 * Be plain about what that buys. It does not make a four digit PIN strong:
 * someone who can read the device's storage can try all ten thousand PINs in
 * well under an hour. What stops a child is the rate limit below, and that is
 * the threat this is for.
 */
export const PIN_ROUNDS = 1_000;

export const MAX_ATTEMPTS = 5;
export const LOCKOUT_MS = 60_000;

export interface PinRecord {
  salt: string;
  hash: string;
  rounds: number;
}

export interface PinGateState {
  record: PinRecord | null;
  failedAttempts: number;
  /** Wall clock when entry is allowed again, or null. */
  lockedUntilMs: number | null;
}

export function emptyPinGate(): PinGateState {
  return { record: null, failedAttempts: 0, lockedUntilMs: null };
}

export function isValidPin(pin: string): boolean {
  return new RegExp(`^[0-9]{${PIN_LENGTH}}$`).test(pin);
}

/** Make a salt from a source of randomness the caller provides. */
export function makeSalt(randomBytes: Uint8Array): string {
  return bytesToHex(randomBytes);
}

export function hashPin(pin: string, salt: string, rounds = PIN_ROUNDS): string {
  let digest = sha512(utf8Bytes(`calm-frames:${salt}:${pin}`));
  for (let round = 1; round < rounds; round += 1) {
    digest = sha512(digest);
  }
  return bytesToHex(digest);
}

export function setPin(
  state: PinGateState,
  pin: string,
  salt: string,
  rounds = PIN_ROUNDS,
): PinGateState {
  if (!isValidPin(pin)) {
    throw new Error(`a PIN is ${PIN_LENGTH} digits`);
  }
  return {
    record: { salt, hash: hashPin(pin, salt, rounds), rounds },
    failedAttempts: 0,
    lockedUntilMs: null,
  };
}

export interface PinAttemptResult {
  state: PinGateState;
  ok: boolean;
  /** Plain wording for the screen. */
  message: string;
}

export function attemptPin(
  state: PinGateState,
  pin: string,
  nowMs: number,
): PinAttemptResult {
  if (!state.record) {
    return {
      state,
      ok: false,
      message: 'No PIN is set yet. Set one to lock the parent area.',
    };
  }
  if (state.lockedUntilMs !== null && nowMs < state.lockedUntilMs) {
    const seconds = Math.ceil((state.lockedUntilMs - nowMs) / 1000);
    return {
      state,
      ok: false,
      message: `Too many tries. Wait ${seconds} seconds.`,
    };
  }

  const candidate = hashPin(pin, state.record.salt, state.record.rounds);
  if (constantTimeEquals(candidate, state.record.hash)) {
    return {
      state: { ...state, failedAttempts: 0, lockedUntilMs: null },
      ok: true,
      message: 'Unlocked.',
    };
  }

  const failedAttempts = state.failedAttempts + 1;
  const locked = failedAttempts >= MAX_ATTEMPTS;
  return {
    state: {
      ...state,
      failedAttempts: locked ? 0 : failedAttempts,
      lockedUntilMs: locked ? nowMs + LOCKOUT_MS : state.lockedUntilMs,
    },
    ok: false,
    message: locked
      ? 'Too many tries. The parent area is locked for a minute.'
      : `That PIN is not right. ${MAX_ATTEMPTS - failedAttempts} tries left.`,
  };
}

/**
 * Compare without leaking where two strings differ through timing.
 *
 * A PIN hash comparison is not the weak link here, but a comparison that
 * returns early is a habit worth not having.
 */
export function constantTimeEquals(left: string, right: string): boolean {
  if (left.length !== right.length) {
    return false;
  }
  let difference = 0;
  for (let index = 0; index < left.length; index += 1) {
    difference |= left.charCodeAt(index) ^ right.charCodeAt(index);
  }
  return difference === 0;
}
