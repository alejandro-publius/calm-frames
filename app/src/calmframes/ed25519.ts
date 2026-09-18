/**
 * Ed25519 signature checking, verify only.
 *
 * A flash map is signed by the pipeline with an Ed25519 key and the app ships
 * only the public half. Vega has no crypto API for this: React Native has no
 * WebCrypto and the Kepler security manager only deals in privileges, so the
 * check is done here in JavaScript.
 *
 * This is RFC 8032 section 5.1.7 with the strict checks: a non-canonical point
 * encoding is refused, a scalar S at or above the group order is refused, and
 * the cofactorless equation [S]B = R + [k]A is the one that has to hold. Being
 * stricter than the signer only ever means refusing a map, and refusing a map
 * keeps the picture hidden, which is the safe direction.
 *
 * It runs once per title, before play starts. On a stick that is a few hundred
 * milliseconds of arithmetic, which is why it is never on the path of a frame.
 */

import { sha512 } from './sha512';

const P = (1n << 255n) - 19n;
const L =
  (1n << 252n) + 27742317777372353535851937790883648493n;
const D =
  37095705934669439343138083508754565189542113879843219016388785533085940283555n;
const SQRT_M1 =
  19681161376707505956807079304988542015446066515923890162744021073123829784752n;

const BASE_Y = (4n * modInverse(5n)) % P;

interface Point {
  x: bigint;
  y: bigint;
  z: bigint;
  t: bigint;
}

function mod(value: bigint): bigint {
  const out = value % P;
  return out < 0n ? out + P : out;
}

function power(base: bigint, exponent: bigint): bigint {
  let result = 1n;
  let b = mod(base);
  let e = exponent;
  while (e > 0n) {
    if (e & 1n) {
      result = mod(result * b);
    }
    b = mod(b * b);
    e >>= 1n;
  }
  return result;
}

function modInverse(value: bigint): bigint {
  return power(value, P - 2n);
}

function pointAdd(a: Point, b: Point): Point {
  const A = mod((a.y - a.x) * (b.y - b.x));
  const B = mod((a.y + a.x) * (b.y + b.x));
  const C = mod(2n * a.t * b.t * D);
  const Dd = mod(2n * a.z * b.z);
  const E = B - A;
  const F = Dd - C;
  const G = Dd + C;
  const H = B + A;
  return {
    x: mod(E * F),
    y: mod(G * H),
    z: mod(F * G),
    t: mod(E * H),
  };
}

function scalarMultiply(point: Point, scalar: bigint): Point {
  let result: Point = { x: 0n, y: 1n, z: 1n, t: 0n };
  let addend = point;
  let value = scalar;
  while (value > 0n) {
    if (value & 1n) {
      result = pointAdd(result, addend);
    }
    addend = pointAdd(addend, addend);
    value >>= 1n;
  }
  return result;
}

function pointsEqual(a: Point, b: Point): boolean {
  // Projective coordinates, so compare after cross multiplying.
  if (mod(a.x * b.z - b.x * a.z) !== 0n) {
    return false;
  }
  return mod(a.y * b.z - b.y * a.z) === 0n;
}

function littleEndianToBigInt(bytes: Uint8Array): bigint {
  let value = 0n;
  for (let index = bytes.length - 1; index >= 0; index -= 1) {
    value = (value << 8n) | BigInt(bytes[index]);
  }
  return value;
}

/** Turn a compressed 32 byte point into coordinates, or null if it is not one. */
function decompress(bytes: Uint8Array): Point | null {
  if (bytes.length !== 32) {
    return null;
  }
  const raw = littleEndianToBigInt(bytes);
  const sign = (raw >> 255n) & 1n;
  const y = raw & ((1n << 255n) - 1n);
  if (y >= P) {
    // Non-canonical encoding: two different byte strings would name one point.
    return null;
  }
  const y2 = mod(y * y);
  const u = mod(y2 - 1n);
  const v = mod(D * y2 + 1n);
  // The candidate square root of u/v, as x = (u v^3) (u v^7)^((p-5)/8).
  const uv3 = mod(u * mod(v * v) * v);
  const uv7 = mod(uv3 * mod(mod(v * v) * mod(v * v)));
  let x = mod(uv3 * power(uv7, (P - 5n) / 8n));
  if (mod(v * x * x) === mod(u)) {
    // x is already the root.
  } else if (mod(v * x * x) === mod(-u)) {
    x = mod(x * SQRT_M1);
  } else {
    return null;
  }
  if (x === 0n && sign === 1n) {
    return null;
  }
  if ((x & 1n) !== sign) {
    x = mod(-x);
  }
  return { x, y, z: 1n, t: mod(x * y) };
}

const BASE_POINT: Point = (() => {
  const y = BASE_Y;
  const y2 = mod(y * y);
  const u = mod(y2 - 1n);
  const v = mod(D * y2 + 1n);
  const uv3 = mod(u * mod(v * v) * v);
  const uv7 = mod(uv3 * mod(mod(v * v) * mod(v * v)));
  let x = mod(uv3 * power(uv7, (P - 5n) / 8n));
  if (mod(v * x * x) !== mod(u)) {
    x = mod(x * SQRT_M1);
  }
  if ((x & 1n) === 1n) {
    x = mod(-x);
  }
  return { x, y, z: 1n, t: mod(x * y) };
})();

/**
 * True when signature is a valid Ed25519 signature of message under publicKey.
 *
 * Never throws: a malformed key, signature or point is a false, because the
 * caller's answer to "is this map trustworthy" must be no rather than a crash.
 */
export function verifyEd25519(
  signature: Uint8Array,
  message: Uint8Array,
  publicKey: Uint8Array,
): boolean {
  try {
    if (signature.length !== 64 || publicKey.length !== 32) {
      return false;
    }
    const rBytes = signature.slice(0, 32);
    const sBytes = signature.slice(32, 64);
    const s = littleEndianToBigInt(sBytes);
    if (s >= L) {
      return false;
    }
    const rPoint = decompress(rBytes);
    const aPoint = decompress(publicKey);
    if (!rPoint || !aPoint) {
      return false;
    }

    const toHash = new Uint8Array(64 + message.length);
    toHash.set(rBytes, 0);
    toHash.set(publicKey, 32);
    toHash.set(message, 64);
    const k = littleEndianToBigInt(sha512(toHash)) % L;

    const left = scalarMultiply(BASE_POINT, s);
    const right = pointAdd(rPoint, scalarMultiply(aPoint, k));
    return pointsEqual(left, right);
  } catch {
    return false;
  }
}

/** Decode standard base64 into bytes, or null when the text is not base64. */
export function base64ToBytes(text: string): Uint8Array | null {
  const alphabet =
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
  const clean = text.trim();
  if (!/^[A-Za-z0-9+/]*={0,2}$/.test(clean) || clean.length % 4 !== 0) {
    return null;
  }
  const out: number[] = [];
  let buffer = 0;
  let bits = 0;
  for (const character of clean) {
    if (character === '=') {
      break;
    }
    const index = alphabet.indexOf(character);
    if (index < 0) {
      return null;
    }
    buffer = (buffer << 6) | index;
    bits += 6;
    if (bits >= 8) {
      bits -= 8;
      out.push((buffer >> bits) & 0xff);
    }
  }
  return Uint8Array.from(out);
}
