/**
 * The exact bytes a flash map was signed over.
 *
 * docs/SIDECAR_SPEC.md says the signed message is the map with the signature
 * key removed, serialised by Python as:
 *
 *     json.dumps(doc, sort_keys=True, separators=(",", ":"),
 *                ensure_ascii=False, allow_nan=False).encode("utf-8")
 *
 * A reader has to rebuild those bytes from the file it was handed. Doing that
 * with JSON.parse and JSON.stringify does not work, because parsing throws
 * away how a number was written. Python writes the float 1450.0 as "1450.0"
 * and JavaScript writes the same parsed value as "1450", so the rebuilt bytes
 * would differ from the signed bytes and every real map would look forged.
 *
 * So this module scans the text itself and keeps the source text of every
 * scalar. Canonical form is then the same tokens, with object keys sorted and
 * all whitespace removed. Nothing is re-formatted, so nothing can drift from
 * what the producer wrote.
 *
 * Anything this scanner cannot make sense of is an error, and a caller that
 * cannot rebuild the bytes has to treat the map as unverified and keep the
 * picture hidden.
 */

export type JsonPlain =
  | string
  | number
  | boolean
  | null
  | JsonPlain[]
  | { [key: string]: JsonPlain };

export type JsonNode =
  | { kind: 'scalar'; raw: string; value: string | number | boolean | null }
  | { kind: 'array'; items: JsonNode[] }
  | { kind: 'object'; entries: Array<{ key: string; keyRaw: string; value: JsonNode }> };

export class CanonicalJsonError extends Error {}

const WHITESPACE = new Set([' ', '\t', '\n', '\r']);

class Scanner {
  private at = 0;

  constructor(private readonly text: string) {}

  parse(): JsonNode {
    this.skipWhitespace();
    const node = this.parseValue();
    this.skipWhitespace();
    if (this.at !== this.text.length) {
      throw new CanonicalJsonError(`trailing text at ${this.at}`);
    }
    return node;
  }

  private fail(message: string): never {
    throw new CanonicalJsonError(`${message} at ${this.at}`);
  }

  private skipWhitespace(): void {
    while (this.at < this.text.length && WHITESPACE.has(this.text[this.at])) {
      this.at += 1;
    }
  }

  private expect(character: string): void {
    if (this.text[this.at] !== character) {
      this.fail(`expected ${character}`);
    }
    this.at += 1;
  }

  private parseValue(): JsonNode {
    const character = this.text[this.at];
    if (character === undefined) {
      this.fail('unexpected end of text');
    }
    if (character === '{') {
      return this.parseObject();
    }
    if (character === '[') {
      return this.parseArray();
    }
    if (character === '"') {
      const start = this.at;
      const value = this.parseString();
      return { kind: 'scalar', raw: this.text.slice(start, this.at), value };
    }
    return this.parseLiteral();
  }

  private parseObject(): JsonNode {
    this.expect('{');
    const entries: Array<{ key: string; keyRaw: string; value: JsonNode }> = [];
    const seen = new Set<string>();
    this.skipWhitespace();
    if (this.text[this.at] === '}') {
      this.at += 1;
      return { kind: 'object', entries };
    }
    for (;;) {
      this.skipWhitespace();
      const keyStart = this.at;
      const key = this.parseString();
      const keyRaw = this.text.slice(keyStart, this.at);
      if (seen.has(key)) {
        // Python's parser keeps the last duplicate and its writer emits one, so
        // a document with duplicates cannot be reproduced byte for byte.
        this.fail(`duplicate key ${key}`);
      }
      seen.add(key);
      this.skipWhitespace();
      this.expect(':');
      this.skipWhitespace();
      const value = this.parseValue();
      entries.push({ key, keyRaw, value });
      this.skipWhitespace();
      if (this.text[this.at] === ',') {
        this.at += 1;
        continue;
      }
      this.expect('}');
      return { kind: 'object', entries };
    }
  }

  private parseArray(): JsonNode {
    this.expect('[');
    const items: JsonNode[] = [];
    this.skipWhitespace();
    if (this.text[this.at] === ']') {
      this.at += 1;
      return { kind: 'array', items };
    }
    for (;;) {
      this.skipWhitespace();
      items.push(this.parseValue());
      this.skipWhitespace();
      if (this.text[this.at] === ',') {
        this.at += 1;
        continue;
      }
      this.expect(']');
      return { kind: 'array', items };
    }
  }

  private parseString(): string {
    this.expect('"');
    let out = '';
    for (;;) {
      const character = this.text[this.at];
      if (character === undefined) {
        this.fail('unterminated string');
      }
      if (character === '"') {
        this.at += 1;
        return out;
      }
      if (character === '\\') {
        this.at += 1;
        const escape = this.text[this.at];
        this.at += 1;
        switch (escape) {
          case '"':
            out += '"';
            break;
          case '\\':
            out += '\\';
            break;
          case '/':
            out += '/';
            break;
          case 'b':
            out += '\b';
            break;
          case 'f':
            out += '\f';
            break;
          case 'n':
            out += '\n';
            break;
          case 'r':
            out += '\r';
            break;
          case 't':
            out += '\t';
            break;
          case 'u': {
            const hex = this.text.slice(this.at, this.at + 4);
            if (!/^[0-9a-fA-F]{4}$/.test(hex)) {
              this.fail('bad \\u escape');
            }
            out += String.fromCharCode(parseInt(hex, 16));
            this.at += 4;
            break;
          }
          default:
            this.fail(`bad escape ${escape}`);
        }
        continue;
      }
      if (character < ' ') {
        this.fail('raw control character in string');
      }
      out += character;
      this.at += 1;
    }
  }

  private parseLiteral(): JsonNode {
    const start = this.at;
    if (this.text.startsWith('true', this.at)) {
      this.at += 4;
      return { kind: 'scalar', raw: 'true', value: true };
    }
    if (this.text.startsWith('false', this.at)) {
      this.at += 5;
      return { kind: 'scalar', raw: 'false', value: false };
    }
    if (this.text.startsWith('null', this.at)) {
      this.at += 4;
      return { kind: 'scalar', raw: 'null', value: null };
    }
    // A number. JSON's grammar, nothing else: no leading plus, no hex, no
    // Infinity or NaN, which Python would have refused to write anyway.
    const match = /^-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?/.exec(
      this.text.slice(this.at),
    );
    if (!match || match[0].length === 0) {
      this.fail('not a JSON value');
    }
    this.at += match[0].length;
    const raw = this.text.slice(start, this.at);
    return { kind: 'scalar', raw, value: Number(raw) };
  }
}

/** Parse, keeping the source text of every scalar. */
export function parseJsonNode(text: string): JsonNode {
  return new Scanner(text).parse();
}

/** The ordinary JavaScript value of a parsed node. */
export function nodeToPlain(node: JsonNode): JsonPlain {
  if (node.kind === 'scalar') {
    return node.value;
  }
  if (node.kind === 'array') {
    return node.items.map(nodeToPlain);
  }
  const out: { [key: string]: JsonPlain } = {};
  for (const entry of node.entries) {
    out[entry.key] = nodeToPlain(entry.value);
  }
  return out;
}

/**
 * Compare two strings by Unicode code point.
 *
 * Python sorts dict keys that way. JavaScript's default sort compares UTF-16
 * code units, which puts some astral characters in a different place. Every
 * key in the map schema is ASCII, where the two agree, but the signed bytes
 * have to match for any map, not only the ones we wrote.
 */
export function compareCodePoints(a: string, b: string): number {
  const left = Array.from(a);
  const right = Array.from(b);
  const shared = Math.min(left.length, right.length);
  for (let index = 0; index < shared; index += 1) {
    const x = left[index].codePointAt(0) ?? 0;
    const y = right[index].codePointAt(0) ?? 0;
    if (x !== y) {
      return x < y ? -1 : 1;
    }
  }
  return left.length - right.length;
}

/** Re-emit a node with keys sorted and no whitespace, scalars unchanged. */
export function canonicalText(node: JsonNode): string {
  if (node.kind === 'scalar') {
    return node.raw;
  }
  if (node.kind === 'array') {
    return `[${node.items.map(canonicalText).join(',')}]`;
  }
  const entries = [...node.entries].sort((a, b) =>
    compareCodePoints(a.key, b.key),
  );
  const parts = entries.map(
    (entry) => `${entry.keyRaw}:${canonicalText(entry.value)}`,
  );
  return `{${parts.join(',')}}`;
}

/**
 * UTF-8 bytes, written here rather than taken from TextEncoder.
 *
 * TextEncoder is a polyfill on Vega, and a signature check that silently
 * depends on which polyfill happened to load is not something to leave to
 * chance.
 */
export function utf8Bytes(text: string): Uint8Array {
  const out: number[] = [];
  for (const character of text) {
    const code = character.codePointAt(0) ?? 0;
    if (code < 0x80) {
      out.push(code);
    } else if (code < 0x800) {
      out.push(0xc0 | (code >> 6), 0x80 | (code & 0x3f));
    } else if (code < 0x10000) {
      out.push(
        0xe0 | (code >> 12),
        0x80 | ((code >> 6) & 0x3f),
        0x80 | (code & 0x3f),
      );
    } else {
      out.push(
        0xf0 | (code >> 18),
        0x80 | ((code >> 12) & 0x3f),
        0x80 | ((code >> 6) & 0x3f),
        0x80 | (code & 0x3f),
      );
    }
  }
  return Uint8Array.from(out);
}

/**
 * The bytes a signature covers: the document without one named key, in
 * canonical form.
 */
export function canonicalBytesWithout(
  node: JsonNode,
  omitKey: string,
): Uint8Array {
  if (node.kind !== 'object') {
    throw new CanonicalJsonError('a map has to be a JSON object');
  }
  const stripped: JsonNode = {
    kind: 'object',
    entries: node.entries.filter((entry) => entry.key !== omitKey),
  };
  return utf8Bytes(canonicalText(stripped));
}
