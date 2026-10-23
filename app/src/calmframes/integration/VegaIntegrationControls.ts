import {
  IMediaSessionId,
  ITimeValue,
} from '@amazon-devices/kepler-media-controls';
import { KeplerMediaControlHandler } from '@amazon-devices/react-native-w3cmedia';
import { attachVegaCoverage } from './vegaCoverageAdapter';

type Adapter = ReturnType<typeof attachVegaCoverage>;
/** Register before initialize; bind the adapter after initialization. No raw fallback. */
export class VegaIntegrationControls extends KeplerMediaControlHandler {
  constructor(
    private readonly getAdapter: () => Adapter | null,
    private readonly currentMs: () => number,
    private readonly paused: () => boolean,
  ) {
    super();
  }
  private adapter(): Adapter {
    const adapter = this.getAdapter();
    if (!adapter) throw new Error('Coverage adapter unavailable');
    return adapter;
  }
  private milliseconds(value: ITimeValue): number {
    const time =
      Number(value.seconds ?? 0) * 1000 + Number(value.nanoseconds ?? 0) / 1e6;
    if (!Number.isFinite(time)) throw new Error('Invalid transport time');
    return time;
  }
  private async seek(ms: number): Promise<void> {
    if (!(await this.adapter().seek(ms))) throw new Error('Seek refused');
  }
  async handleSeek(value: ITimeValue, _session?: IMediaSessionId) {
    await this.seek(this.milliseconds(value));
  }
  async handleSkipForward(value: ITimeValue, _session?: IMediaSessionId) {
    await this.seek(this.currentMs() + this.milliseconds(value));
  }
  async handleSkipBackward(value: ITimeValue, _session?: IMediaSessionId) {
    await this.seek(Math.max(0, this.currentMs() - this.milliseconds(value)));
  }
  async handleFastForward(_session?: IMediaSessionId) {
    await this.seek(this.currentMs() + 10000);
  }
  async handleRewind(_session?: IMediaSessionId) {
    await this.seek(Math.max(0, this.currentMs() - 10000));
  }
  async handleStartOver(_session?: IMediaSessionId) {
    await this.seek(0);
  }
  async handlePlay(_session?: IMediaSessionId) {
    if (!(await this.adapter().play())) throw new Error('Play refused');
  }
  async handlePause(_session?: IMediaSessionId) {
    this.adapter().pause();
  }
  async handleStop(_session?: IMediaSessionId) {
    this.adapter().pause();
  }
  async handleTogglePlayPause(_session?: IMediaSessionId) {
    if (this.paused()) await this.handlePlay();
    else await this.handlePause();
  }
  async handleSetPlaybackSpeed() {
    throw new Error('Rate changes unsupported');
  }
  async handleSetRepeatMode() {
    throw new Error('Repeat unsupported');
  }
  async handleNext() {
    throw new Error('Detach and verify the next edition first');
  }
  async handlePrevious() {
    throw new Error('Detach and verify the previous edition first');
  }
}
