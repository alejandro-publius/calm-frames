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
 *
 * Every callback also writes one debug line, the commands that do not move
 * the playhead included, which is the only reason those are overridden: on a
 * device the first questions are which commands arrive and how many per
 * press. The lines are console.log, which the Release build strips.
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

  private async goTo(command: string, targetMs: number): Promise<void> {
    const plan = await this.deps.engine.requestSeek('media-control', targetMs);
    console.log(
      `[SafeMediaControlHandler.ts] - ${command} - asked for ${Math.round(
        plan.requestedMs,
      )} ms, going to ${Math.round(plan.targetMs)} ms, ${
        plan.coverFirst ? 'cover first' : 'no cover needed'
      }, ${plan.reason}`,
    );
  }

  // Each of these deliberately does not call super. The base class would move
  // the playhead straight away, with no cover.

  async handleSeek(
    position: ITimeValue,
    _sessionId?: IMediaSessionId,
  ): Promise<void> {
    await this.goTo('handleSeek', timeValueToMs(position));
  }

  async handleSkipForward(
    delta: ITimeValue,
    _sessionId?: IMediaSessionId,
  ): Promise<void> {
    await this.goTo(
      'handleSkipForward',
      this.deps.getCurrentMs() + timeValueToMs(delta),
    );
  }

  async handleSkipBackward(
    delta: ITimeValue,
    _sessionId?: IMediaSessionId,
  ): Promise<void> {
    await this.goTo(
      'handleSkipBackward',
      this.deps.getCurrentMs() - timeValueToMs(delta),
    );
  }

  async handleFastForward(_sessionId?: IMediaSessionId): Promise<void> {
    await this.goTo('handleFastForward', this.deps.getCurrentMs() + this.stepMs);
  }

  async handleRewind(_sessionId?: IMediaSessionId): Promise<void> {
    await this.goTo('handleRewind', this.deps.getCurrentMs() - this.stepMs);
  }

  async handleStartOver(_sessionId?: IMediaSessionId): Promise<void> {
    await this.goTo('handleStartOver', 0);
  }

  // None of these moves the playhead, so each one logs and then lets the base
  // class do exactly what it did before. They are here only for the line.

  handlePlay(...args: Parameters<KeplerMediaControlHandler['handlePlay']>) {
    console.log('[SafeMediaControlHandler.ts] - handlePlay - passed to the player');
    return super.handlePlay(...args);
  }

  handlePause(...args: Parameters<KeplerMediaControlHandler['handlePause']>) {
    console.log('[SafeMediaControlHandler.ts] - handlePause - passed to the player');
    return super.handlePause(...args);
  }

  handleTogglePlayPause(
    ...args: Parameters<KeplerMediaControlHandler['handleTogglePlayPause']>
  ) {
    console.log(
      '[SafeMediaControlHandler.ts] - handleTogglePlayPause - passed to the player',
    );
    return super.handleTogglePlayPause(...args);
  }

  handleStop(...args: Parameters<KeplerMediaControlHandler['handleStop']>) {
    console.log('[SafeMediaControlHandler.ts] - handleStop - passed to the player');
    return super.handleStop(...args);
  }

  handleSetPlaybackSpeed(
    ...args: Parameters<KeplerMediaControlHandler['handleSetPlaybackSpeed']>
  ) {
    console.log(
      `[SafeMediaControlHandler.ts] - handleSetPlaybackSpeed - ${args[0]}, passed to the player`,
    );
    return super.handleSetPlaybackSpeed(...args);
  }

  handleSetAudioVolume(
    ...args: Parameters<KeplerMediaControlHandler['handleSetAudioVolume']>
  ) {
    console.log(
      `[SafeMediaControlHandler.ts] - handleSetAudioVolume - ${args[0]}, passed to the player`,
    );
    return super.handleSetAudioVolume(...args);
  }

  handleSetAudioTrack(
    ...args: Parameters<KeplerMediaControlHandler['handleSetAudioTrack']>
  ) {
    console.log(
      '[SafeMediaControlHandler.ts] - handleSetAudioTrack - passed to the player',
    );
    return super.handleSetAudioTrack(...args);
  }

  handleEnableTextTrack(
    ...args: Parameters<KeplerMediaControlHandler['handleEnableTextTrack']>
  ) {
    console.log(
      '[SafeMediaControlHandler.ts] - handleEnableTextTrack - passed to the player',
    );
    return super.handleEnableTextTrack(...args);
  }

  handleDisableTextTrack(
    ...args: Parameters<KeplerMediaControlHandler['handleDisableTextTrack']>
  ) {
    console.log(
      '[SafeMediaControlHandler.ts] - handleDisableTextTrack - passed to the player',
    );
    return super.handleDisableTextTrack(...args);
  }

  handleNext(...args: Parameters<KeplerMediaControlHandler['handleNext']>) {
    console.log('[SafeMediaControlHandler.ts] - handleNext - passed to the player');
    return super.handleNext(...args);
  }

  handlePrevious() {
    console.log(
      '[SafeMediaControlHandler.ts] - handlePrevious - passed to the player',
    );
    return super.handlePrevious();
  }

  handleEnableShuffle(
    ...args: Parameters<KeplerMediaControlHandler['handleEnableShuffle']>
  ) {
    console.log(
      '[SafeMediaControlHandler.ts] - handleEnableShuffle - passed to the player',
    );
    return super.handleEnableShuffle(...args);
  }

  handleSetRepeatMode(
    ...args: Parameters<KeplerMediaControlHandler['handleSetRepeatMode']>
  ) {
    console.log(
      '[SafeMediaControlHandler.ts] - handleSetRepeatMode - passed to the player',
    );
    return super.handleSetRepeatMode(...args);
  }

  handleSetRating(
    ...args: Parameters<KeplerMediaControlHandler['handleSetRating']>
  ) {
    console.log(
      '[SafeMediaControlHandler.ts] - handleSetRating - passed to the player',
    );
    return super.handleSetRating(...args);
  }

  handleGetMetadataInfo(
    ...args: Parameters<KeplerMediaControlHandler['handleGetMetadataInfo']>
  ) {
    console.log(
      '[SafeMediaControlHandler.ts] - handleGetMetadataInfo - passed to the player',
    );
    return super.handleGetMetadataInfo(...args);
  }

  handleCustomAction(
    ...args: Parameters<KeplerMediaControlHandler['handleCustomAction']>
  ) {
    console.log(
      '[SafeMediaControlHandler.ts] - handleCustomAction - passed to the player',
    );
    return super.handleCustomAction(...args);
  }

  handleGetSessionState(
    ...args: Parameters<KeplerMediaControlHandler['handleGetSessionState']>
  ) {
    console.log(
      '[SafeMediaControlHandler.ts] - handleGetSessionState - passed to the player',
    );
    return super.handleGetSessionState(...args);
  }
}
