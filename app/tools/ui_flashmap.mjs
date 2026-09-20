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
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

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
  const venv = join(repoRoot, '.venv', 'bin', 'python');
  return existsSync(venv) ? venv : 'python3';
}

async function main() {
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

  for (const frame of frames) {
    const pixels = paint(frame);
    for (let repeat = 0; repeat < held; repeat += 1) {
      if (!ffmpeg.stdin.write(pixels)) {
        await new Promise((resolve) => ffmpeg.stdin.once('drain', resolve));
      }
    }
  }
  ffmpeg.stdin.end();

  const encoded = await new Promise((resolve) => ffmpeg.on('close', resolve));
  if (encoded !== 0) {
    console.error(`ffmpeg failed with ${encoded}`);
    process.exit(2);
  }

  const result = spawnSync(
    pythonCommand(),
    ['-m', 'flashmap', 'check', videoPath, '--profile', 'wcag'],
    { cwd: repoRoot, encoding: 'utf8' },
  );
  const output = `${result.stdout ?? ''}${result.stderr ?? ''}`;
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
  const pattern = spawnSync(
    pythonCommand(),
    ['-m', 'flashmap', 'check', videoPath, '--profile', 'broadcast'],
    { cwd: repoRoot, encoding: 'utf8' },
  );
  const patternOutput = `${pattern.stdout ?? ''}${pattern.stderr ?? ''}`;
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

main().catch((error) => {
  console.error(error);
  process.exit(2);
});
