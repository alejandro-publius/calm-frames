/**
 * Run flashmap over the app's own screens.
 *
 * docs/BUILD_PROMPT.md 4.5: the app's own screens and transitions have to pass
 * flashmap. Vega gives the app no way to read its pixels back, and screenshots
 * of the virtual device come back black because the app draws on a layer the
 * capture misses, so the frames come from what the app records it paints. See
 * src/calmframes/uiCapture.ts for what was tried and why.
 *
 * What this does:
 *
 *   1. reads build/ui-capture/ui-frames.json, written by
 *      test/calmframes/uiCapture.test.tsx, which renders every Calm Frames
 *      screen for real and reads the colours off the rendered tree;
 *   2. paints each frame: the background over the whole picture, then one
 *      block per painted colour, each a full WCAG ten degree window wide and
 *      tall. A real card is smaller than that, so the picture this measures
 *      overstates the flashing area rather than understating it;
 *   3. holds each frame for 100 ms, which is faster than a held remote key
 *      repeats, so the transition rate is a worst case too, and fast enough
 *      that a flashing screen really would fail this check;
 *   4. encodes it losslessly and runs `python -m flashmap check` over it.
 *
 * Exit code 0 means no segment broke the thresholds. Anything else means the
 * app's own screens would have to change.
 *
 *     npm run ui:flashmap
 */

import { spawn, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { Readable } from 'node:stream';
import { pipeline } from 'node:stream/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';

const appRoot = join(dirname(fileURLToPath(import.meta.url)), '..');
const repoRoot = join(appRoot, '..');
const captureFile = join(appRoot, 'build', 'ui-capture', 'ui-frames.json');
const outDir = join(appRoot, 'build', 'ui-capture');

const WIDTH = 640;
const HEIGHT = 360;
const FPS = 24;
/**
 * How long each captured frame is held.
 *
 * This number decides whether the check can fail at all, so it is not a taste
 * choice. A flash is a pair of opposing transitions, and the WCAG general rule
 * is more than three flashes in any one second. At 250 ms a frame the fastest
 * the picture can change is four transitions a second, which is two flashes,
 * and no arrangement of screens could ever break the limit: the check would
 * pass whatever the app looked like.
 *
 * 100 ms is ten transitions a second, five flashes, comfortably over the
 * limit. It is also the real worst case: the sample's own seek bar repeats a
 * held key every 200 ms, so a focus ring moving on every repeat changes the
 * picture five times a second, and 100 ms is twice as fast as that again.
 *
 * Breaking it on purpose is in the test: give the capture a screen that
 * alternates white and near black and this run turns red.
 */
const HOLD_MS = 100;
/**
 * A WCAG ten degree window is 341 of 1024 across and 256 of 768 down.
 * SPEC_SOURCES section 2, through docs/SIDECAR_SPEC.md.
 */
const WINDOW_W = Math.round((WIDTH * 341) / 1024);
const WINDOW_H = Math.round((HEIGHT * 256) / 768);
/** What the video behind the app's layer is painted as. See uiFrames.ts. */
const VIDEO_STAND_IN = '#808080';

function parseColour(value) {
  const text = value === 'video' ? VIDEO_STAND_IN : value;
  const hex = /^#?([0-9a-fA-F]{6})$/.exec(String(text));
  if (!hex) {
    throw new Error(`not a colour this tool can paint: ${value}`);
  }
  const number = parseInt(hex[1], 16);
  return [(number >> 16) & 0xff, (number >> 8) & 0xff, number & 0xff];
}

/** One frame, as raw RGB24. */
function paint(frame) {
  const pixels = Buffer.alloc(WIDTH * HEIGHT * 3);
  const [br, bg, bb] = parseColour(frame.background);
  for (let index = 0; index < WIDTH * HEIGHT; index += 1) {
    pixels[index * 3] = br;
    pixels[index * 3 + 1] = bg;
    pixels[index * 3 + 2] = bb;
  }

  frame.surfaces.forEach((colour, order) => {
    const [r, g, b] = parseColour(colour);
    const left = (order * WINDOW_W) % Math.max(1, WIDTH - WINDOW_W + 1);
    const top = Math.min(
      HEIGHT - WINDOW_H,
      Math.floor(order / Math.max(1, Math.floor(WIDTH / WINDOW_W))) * WINDOW_H,
    );
    for (let y = top; y < Math.min(HEIGHT, top + WINDOW_H); y += 1) {
      for (let x = left; x < Math.min(WIDTH, left + WINDOW_W); x += 1) {
        const index = (y * WIDTH + x) * 3;
        pixels[index] = r;
        pixels[index + 1] = g;
        pixels[index + 2] = b;
      }
    }
  });

  return pixels;
}

function pythonCommand() {
  // PY names an interpreter, as it does for check_video.sh and the Makefile;
  // otherwise the repository .venv, otherwise whatever python3 is on PATH.
  if (process.env.PY) return process.env.PY;
  const venv = join(repoRoot, '.venv', 'bin', 'python');
  return existsSync(venv) ? venv : 'python3';
}

/** Encode raw RGB24 frames losslessly, each held for HOLD_MS, and return ffmpeg's exit code. */
async function encode(frames, videoPath) {
  const held = Math.max(1, Math.round((HOLD_MS / 1000) * FPS));
  const ffmpeg = spawn(
    'ffmpeg',
    [
      '-y',
      '-loglevel', 'error',
      '-f', 'rawvideo',
      '-pixel_format', 'rgb24',
      '-video_size', `${WIDTH}x${HEIGHT}`,
      '-framerate', String(FPS),
      '-i', 'pipe:0',
      // Lossless, so nothing the encoder does can change a luminance step.
      '-c:v', 'libx264',
      '-qp', '0',
      '-pix_fmt', 'yuv444p',
      '-color_primaries', 'bt709',
      '-color_trc', 'bt709',
      '-colorspace', 'bt709',
      videoPath,
    ],
    { stdio: ['pipe', 'inherit', 'inherit'] },
  );
  function* repeatedFrames() {
    for (const pixels of frames) {
      for (let repeat = 0; repeat < held; repeat += 1) yield pixels;
    }
  }
  const completion = new Promise((resolve, reject) => {
    ffmpeg.once('error', reject);
    ffmpeg.once('close', resolve);
  });
  try {
    const [, status] = await Promise.all([
      pipeline(Readable.from(repeatedFrames()), ffmpeg.stdin),
      completion,
    ]);
    return status;
  } catch (error) {
    ffmpeg.kill();
    await completion.catch(() => {});
    throw error;
  }
}

function check(videoPath, profile, reportPath) {
  const result = spawnSync(
    pythonCommand(),
    ['-m', 'flashmap', 'check', videoPath, '--profile', profile,
      ...(reportPath ? ['--json', reportPath] : [])],
    { cwd: repoRoot, encoding: 'utf8' },
  );
  return { status: result.status, error: result.error, signal: result.signal,
    output: `${result.stdout ?? ''}${result.stderr ?? ''}` };
}

/** Exit 1 alone can also be a crash. Require the matching measured finding. */
function measuredControl(result, videoPath, profile, reportPath, reason) {
  const passes = reason === undefined;
  if (result.error || result.signal || result.status !== (passes ? 0 : 1)) return false;
  try {
    if (statSync(reportPath).size > 1024 * 1024) return false;
    const report = JSON.parse(readFileSync(reportPath, 'utf8'));
    const hash = createHash('sha256').update(readFileSync(videoPath)).digest('hex');
    if (report.version !== 1 || report.source?.sha256 !== hash ||
      report.profile?.name !== profile || report.summary?.pass !== passes ||
      !Array.isArray(report.segments) || report.summary.segment_count !== report.segments.length) return false;
    const expectedLine = passes ? `PASS ${videoPath}: below the ${profile} thresholds` :
      `FAIL ${videoPath}: ${report.segments.length} segment(s) over the thresholds`;
    if (!result.output.split(/\r?\n/).includes(expectedLine) || result.output.includes('Traceback (most recent call last)')) return false;
    if (passes) return report.segments.length === 0 && report.summary.flash_pass === true && report.summary.pattern_pass === true;
    return report.segments.some((segment) => segment.reason === reason &&
      Number.isFinite(segment.start_ms) && Number.isFinite(segment.end_ms) &&
      segment.start_ms >= 0 && segment.end_ms > segment.start_ms) &&
      report.summary[reason === 'pattern' ? 'pattern_pass' : 'flash_pass'] === false;
  } catch {
    return false;
  }
}

/** A whole frame of one colour, as raw RGB24. */
function solid(colour) {
  return paint({ background: colour, surfaces: [] });
}

/** A frame of vertical black and white stripes, `pairs` of them across the picture. */
function stripes(pairs) {
  const pixels = Buffer.alloc(WIDTH * HEIGHT * 3);
  const barWidth = WIDTH / (pairs * 2);
  for (let y = 0; y < HEIGHT; y += 1) {
    for (let x = 0; x < WIDTH; x += 1) {
      const value = Math.floor(x / barWidth) % 2 === 0 ? 0 : 255;
      const index = (y * WIDTH + x) * 3;
      pixels[index] = value;
      pixels[index + 1] = value;
      pixels[index + 2] = value;
    }
  }
  return pixels;
}

/**
 * The negative control: the check has to be seen refusing something, or a
 * green run says nothing. Two sequences are painted the way the real screens
 * are and put through the same two passes. The first alternates white and
 * near black at HOLD_MS, five flashes a second across the whole picture, which
 * the wcag profile must refuse. The second is a static grating of sixteen
 * black and white pairs filling the picture, which the broadcast profile's
 * regular pattern rule must refuse and the wcag profile, which has no pattern
 * rule, must pass. If either refusal does not happen, this exits non-zero and
 * the main run's green means nothing until it is understood.
 *
 *     node tools/ui_flashmap.mjs --negative-control
 *
 * Seen to fail on purpose, Oct 11 2026: with the flashing sequence replaced by
 * a static mid grey the control reported that wcag had passed it and exited 1.
 */
export async function negativeControl({
  encodeFrames = encode,
  checkVideo = check,
  outputDir = outDir,
  mediaRoot = join(repoRoot, 'media'),
} = {}) {
  mkdirSync(outputDir, { recursive: true });
  mkdirSync(mediaRoot, { recursive: true });
  const scratch = mkdtempSync(join(mediaRoot, 'HAZARD_ui-control-'));
  const flashPath = join(scratch, 'HAZARD_negative-control-flash.mp4');
  const patternPath = join(scratch, 'HAZARD_negative-control-pattern.mp4');
  const flashReport = join(scratch, 'flash-wcag.json');
  const patternReport = join(scratch, 'pattern-broadcast.json');
  const patternWcagReport = join(scratch, 'pattern-wcag.json');

  try {
    const flashing = [];
    for (let index = 0; index < 20; index += 1) {
      flashing.push(solid(index % 2 === 0 ? '#ffffff' : '#101010'));
    }
    const grating = [];
    for (let index = 0; index < 10; index += 1) {
      grating.push(stripes(16));
    }
    const encodedFlash = await encodeFrames(flashing, flashPath);
    const encodedPattern = await encodeFrames(grating, patternPath);
    if (encodedFlash !== 0 || encodedPattern !== 0) {
      console.error('ffmpeg failed to encode a negative control');
      return 2;
    }

    const flashWcag = checkVideo(flashPath, 'wcag', flashReport);
    const patternBroadcast = checkVideo(patternPath, 'broadcast', patternReport);
    const patternWcag = checkVideo(patternPath, 'wcag', patternWcagReport);
    const verdicts = {
      flashing_sequence_refused_by_wcag: measuredControl(flashWcag, flashPath, 'wcag', flashReport, 'general'),
      grating_refused_by_broadcast: measuredControl(patternBroadcast, patternPath, 'broadcast', patternReport, 'pattern'),
      grating_passed_by_wcag_which_has_no_pattern_rule: measuredControl(patternWcag, patternPath, 'wcag', patternWcagReport),
    };
    writeFileSync(
      join(outputDir, 'ui-flashmap-negative-control.json'),
      `${JSON.stringify(
        {
          held_ms: HOLD_MS,
          flashing_frames: flashing.length,
          grating_frames: grating.length,
          grating_pairs: 16,
          verdicts,
          flash_wcag_exit: flashWcag.status,
          pattern_broadcast_exit: patternBroadcast.status,
          pattern_wcag_exit: patternWcag.status,
          note: 'The same painter, hold and encoder as the real screens. A control the check cannot refuse would mean the real run proves nothing.',
        },
        null,
        2,
      )}\n`,
    );
    const failed = Object.entries(verdicts).filter(([, ok]) => !ok).map(([name]) => name);
    if (failed.length > 0) {
      console.error(`\nnegative control failed: ${failed.join(', ')}. The check did not refuse what it must refuse, so a green run of the real screens means nothing.`);
      return 1;
    }
    console.log(
      '\nnegative control: the wcag profile refused the flashing sequence, the broadcast profile ' +
        'refused the grating, and the wcag profile passed the grating, as it must.',
    );
    return 0;
  } finally {
    // These clips exist only for this measurement and must never be opened.
    rmSync(scratch, { recursive: true, force: true });
  }
}

async function main() {
  // A missing analyzer is not a threshold finding. Say so and exit 2, the
  // code flashmap itself uses for "could not tell", before anything is painted.
  const probe = spawnSync(pythonCommand(), ['-c', 'import flashmap'], { cwd: repoRoot, encoding: 'utf8' });
  if (probe.error || probe.status !== 0) {
    console.error(
      `flashmap is not importable by ${pythonCommand()}. Install it first ` +
        '(python -m pip install -e "flashmap[dev]" from the repository root, or create the ' +
        'repository .venv). This is not a threshold failure.',
    );
    process.exit(2);
  }
  if (process.argv.includes('--negative-control')) {
    process.exit(await negativeControl());
  }
  if (!existsSync(captureFile)) {
    console.error(
      `no capture at ${captureFile}. Run the app's tests first:\n` +
        '  npx jest test/calmframes/uiCapture.test.tsx',
    );
    process.exit(2);
  }
  const capture = JSON.parse(readFileSync(captureFile, 'utf8'));
  const frames = capture.frames ?? [];
  if (frames.length === 0) {
    console.error('the capture has no frames in it');
    process.exit(2);
  }

  mkdirSync(outDir, { recursive: true });
  const videoPath = join(outDir, 'ui-screens.mp4');

  const encoded = await encode(frames.map(paint), videoPath);
  if (encoded !== 0) {
    console.error(`ffmpeg failed with ${encoded}`);
    process.exit(2);
  }

  const result = check(videoPath, 'wcag');
  const output = result.output;
  process.stdout.write(output);

  // The second pass, and the reason it is a second one. The wcag profile has no regular
  // pattern rule at all, so until now nothing in the app's own screens had ever been put in
  // front of ITU-R BT.1702-3 Guideline 2. The broadcast profile carries it.
  //
  // What this pass can and cannot see. These frames are painted from the colours the app
  // records it drew, one block per painted colour, so there is no text in them: this asks
  // whether the layout of the app's own blocks forms a regular pattern, not what the rule
  // makes of a glyph. eval/pattern_text_precision.py is where text is measured.
  console.log('\nthe same screens under the broadcast profile, which carries the regular pattern rule:');
  const pattern = check(videoPath, 'broadcast');
  const patternOutput = pattern.output;
  process.stdout.write(patternOutput);

  writeFileSync(
    join(outDir, 'ui-flashmap.json'),
    `${JSON.stringify(
      {
        frames: frames.length,
        held_ms: HOLD_MS,
        width: WIDTH,
        height: HEIGHT,
        fps: FPS,
        window_px: [WINDOW_W, WINDOW_H],
        video: 'build/ui-capture/ui-screens.mp4',
        flashmap_exit: result.status,
        flashmap_output: output.trim(),
        pattern_profile: 'broadcast',
        pattern_exit: pattern.status,
        pattern_output: patternOutput.trim(),
        note:
          'Each painted colour is given a block a full WCAG ten degree window wide, which is larger than the real surfaces, so this overstates the flashing area rather than understating it.',
        pattern_note:
          'The broadcast pass adds ITU-R BT.1702-3 Guideline 2, which the wcag profile does not carry. These frames hold no text, so it asks whether the layout of the app\'s own blocks is a regular pattern. What the rule makes of glyphs is measured in results/pattern_text_precision.json.',
      },
      null,
      2,
    )}\n`,
  );

  if (result.status !== 0) {
    console.error(
      `\nflashmap exited ${result.status}. The app's own screens are over the thresholds.`,
    );
    process.exit(result.status ?? 1);
  }
  if (pattern.status !== 0) {
    console.error(
      `\nflashmap exited ${pattern.status} under the broadcast profile. The app's own screens ` +
        'hold a regular pattern finding. That is not a WCAG failure, because WCAG 2.2 SC 2.3.1 ' +
        'has no pattern rule, but it is a layout a child should not be shown.',
    );
    process.exit(pattern.status ?? 1);
  }
  console.log(
    `\nflashmap: no segment broke the thresholds across ${frames.length} screens and ` +
      'transitions, under the wcag profile and under the broadcast profile with the regular ' +
      'pattern rule.',
  );
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error);
    process.exit(2);
  });
}
