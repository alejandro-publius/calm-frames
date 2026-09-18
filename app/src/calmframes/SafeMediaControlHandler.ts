/**
 * Alexa and the remote's transport commands, made safe.
 *
 * Vega Media Controls delivers "skip forward", "rewind", "start over" and a
 * plain seek to the app through a KeplerMediaControlHandler that the app hands
 * to VideoPlayer.setMediaControlFocus. The default handler moves the playhead
 * itself, which is exactly what must not happen here: a voice command can land
 * inside a flagged part with nothing on screen to stop it.
 *
 * So every one of those callbacks is overridden and none of them calls super.
 * They all go through the same seek engine the on-screen controls use, which
 * covers first and only then moves.
 *
 * The manifest has to opt in to these commands. app/manifest.toml carries the
 * IMediaPlaybackServer extras block with command_options StartOver, Previous,
 * Next, SkipForward and SkipBackward, and the AdvancedSeek feature, and
 * test/calmframes/manifest.test.ts fails if that block goes missing, because
 * the Kepler build rewrites manifest.toml on every build.
 */

import { IMediaSessionId, ITimeValue } from '@amazon-devices/kepler-media-controls';
import { KeplerMediaControlHandler } from '@amazon-devices/react-native-w3cmedia';
import { SeekEngine } from './seekSafety';

/** How far a plain fast forward or rewind press moves, in milliseconds. */
export const DEFAULT_TRANSPORT_STEP_MS = 10_000;

export function timeValueToMs(value: ITimeValue | null | undefined): number {
  if (!value) {
    return 0;
  }
  const seconds = Number(value.seconds ?? 0);
  const nanoseconds = Number(value.nanoseconds ?? 0);
  if (!Number.isFinite(seconds) || !Number.isFinite(nanoseconds)) {
    return 0;
  }
  return seconds * 1000 + nanoseconds / 1e6;
}

export interface SafeMediaControlDeps {
  /** The one seek funnel. */
  engine: SeekEngine;
  /** Where the playhead is now, in milliseconds. */
  getCurrentMs: () => number;
  /** How far a fast forward or rewind press moves. */
  stepMs?: number;
}

export class SafeMediaControlHandler extends KeplerMediaControlHandler {
  private readonly deps: SafeMediaControlDeps;

  constructor(deps: SafeMediaControlDeps) {
    super();
    this.deps = deps;
  }

  private get stepMs(): number {
    return this.deps.stepMs ?? DEFAULT_TRANSPORT_STEP_MS;
  }

  private async goTo(targetMs: number): Promise<void> {
    await this.deps.engine.requestSeek('media-control', targetMs);
  }

  // Each of these deliberately does not call super. The base class would move
  // the playhead straight away, with no cover.

  async handleSeek(
    position: ITimeValue,
    _sessionId?: IMediaSessionId,
  ): Promise<void> {
    await this.goTo(timeValueToMs(position));
  }

  async handleSkipForward(
    delta: ITimeValue,
    _sessionId?: IMediaSessionId,
  ): Promise<void> {
    await this.goTo(this.deps.getCurrentMs() + timeValueToMs(delta));
  }

  async handleSkipBackward(
    delta: ITimeValue,
    _sessionId?: IMediaSessionId,
  ): Promise<void> {
    await this.goTo(this.deps.getCurrentMs() - timeValueToMs(delta));
  }

  async handleFastForward(_sessionId?: IMediaSessionId): Promise<void> {
    await this.goTo(this.deps.getCurrentMs() + this.stepMs);
  }

  async handleRewind(_sessionId?: IMediaSessionId): Promise<void> {
    await this.goTo(this.deps.getCurrentMs() - this.stepMs);
  }

  async handleStartOver(_sessionId?: IMediaSessionId): Promise<void> {
    await this.goTo(0);
  }
}
