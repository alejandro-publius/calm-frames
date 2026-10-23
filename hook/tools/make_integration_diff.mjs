/**
 * Rebuild the diff in docs/INTEGRATION_DIFF.md.
 *
 * The document claims to be the real output of `git diff` against a clean
 * vega-video-sample checkout, so it has to stay that. This script takes the
 * four files out of the pinned sample commit, applies the integration, runs
 * git diff, and prints the patch. It writes nothing: the patch goes to stdout
 * so a person can look at it before it lands in the document.
 *
 *     node hook/tools/make_integration_diff.mjs
 *
 * The sample is pinned at tag v0.24-RN83, commit cf8b752 in this repository's
 * history, which is the unchanged sample as it was added.
 */

import { execFileSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const SAMPLE_COMMIT = 'cf8b752';

/** The four files an app touches, and where they live in the sample. */
const FILES = {
  'src/screens/PlayerScreen.tsx': 'app/src/screens/PlayerScreen.tsx',
  'src/components/Seekbar.tsx': 'app/src/components/Seekbar.tsx',
  'src/w3cmedia/mediacontrols/PlaybackControls.tsx':
    'app/src/w3cmedia/mediacontrols/PlaybackControls.tsx',
  'src/w3cmedia/mediacontrols/VideoPlayerUI.tsx':
    'app/src/w3cmedia/mediacontrols/VideoPlayerUI.tsx',
};

/** Each edit, as the exact text to find and what it becomes. */
const EDITS = {
  'src/screens/PlayerScreen.tsx': [
    [
      "import isEqual from 'lodash/isEqual';",
      `import {
  CalmCard,
  CoverLayer,
  SafeMediaControlHandler,
  useFlashGuard,
} from '@calm-frames/flash-guard';
import isEqual from 'lodash/isEqual';`,
    ],
    [
      '  const videoHandler = new VideoHandler(',
      `  const guard = useFlashGuard({
    mediaRef: videoRef,
    mapUrls: { wcag: data.flashMapUrl },
    expectedSha256: data.sha256,
    publicKeyBase64: FLASH_MAP_PUBLIC_KEY,
    ready: isVideoInitialized,
    titleName: data.title,
  });

  const videoHandler = new VideoHandler(`,
    ],
    [
      `    setShowBuffering,
  );`,
      `    setShowBuffering,
    // Alexa and the remote's transport commands go through the guard too.
    new SafeMediaControlHandler({
      engine: guard.seekEngine,
      getCurrentMs: () => (videoRef.current?.currentTime ?? 0) * 1000,
    }),
  );`,
    ],
    [
      `            <KeplerCaptionsView
              onCaptionViewCreated={onCaptionViewCreated}`,
      `            <CoverLayer visible={guard.covered} mode={guard.coverMode} imageUri={guard.coverImageUri} />
            <KeplerCaptionsView
              onCaptionViewCreated={onCaptionViewCreated}`,
    ],
    [
      `        {showVideoPlayerUI && (
          <VideoPlayerUI`,
      `        <CalmCard card={guard.card} onSkip={guard.skipTo} />
        {showVideoPlayerUI && (
          <VideoPlayerUI
            requestSeek={guard.requestSeek}`,
    ],
  ],
  'src/w3cmedia/mediacontrols/PlaybackControls.tsx': [
    [
      '    videoRef.current.currentTime = newTime;',
      `    // Every way of moving the playhead goes through the guard, which covers
    // the picture first when the target lands in a flagged part.
    requestSeek(seekSeconds >= 0 ? 'dpad-fast-forward' : 'dpad-rewind', newTime * 1000);`,
    ],
  ],
  'src/w3cmedia/mediacontrols/VideoPlayerUI.tsx': [
    [
      `  bifFrameImagesRef: React.MutableRefObject<FrameImageSource | null>;
  videoData: TitleData;
}`,
      `  bifFrameImagesRef: React.MutableRefObject<FrameImageSource | null>;
  videoData: TitleData;
  requestSeek: (source: SeekSource, targetMs: number) => void;
}`,
    ],
    [
      `    videoData,
  }: VideoPlayerUIProps) => {`,
      `    videoData,
    requestSeek,
  }: VideoPlayerUIProps) => {`,
    ],
    [
      `              handleShowControlsOnKeyEvent={handleShowControlsOnKeyEvent}
            />`,
      `              handleShowControlsOnKeyEvent={handleShowControlsOnKeyEvent}
              requestSeek={requestSeek}
            />`,
    ],
  ],
  'src/components/Seekbar.tsx': [
    [
      '  seekBarRef: React.MutableRefObject<null>;',
      `  seekBarRef: React.MutableRefObject<null>;
  requestSeek: (source: SeekSource, targetMs: number) => void;`,
    ],
    [
      `  seekBarRef,
  testID,`,
      `  seekBarRef,
  requestSeek,
  testID,`,
    ],
    [
      '      videoRef.current.fastSeek(value);',
      "      requestSeek('seek-bar', value * SECOND_IN_MILIS);",
    ],
  ],
};

const work = mkdtempSync(join(tmpdir(), 'calm-frames-integration-'));
for (const side of ['clean', 'withguard']) {
  for (const [target, source] of Object.entries(FILES)) {
    const text = execFileSync(
      'git',
      ['show', `${SAMPLE_COMMIT}:${source}`],
      { cwd: repoRoot, encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 },
    );
    let out = text;
    if (side === 'withguard') {
      for (const [from, to] of EDITS[target] ?? []) {
        if (!out.includes(from)) {
          throw new Error(`${target}: the sample no longer contains\n${from}`);
        }
        out = out.replace(from, to);
      }
    }
    const path = join(work, side, target);
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, out);
  }
}

let patch = '';
try {
  execFileSync('git', ['diff', '--no-index', '--no-prefix', '-U1', 'clean', 'withguard'], {
    cwd: work,
    encoding: 'utf8',
  });
} catch (error) {
  // git diff exits 1 when there is a difference, which is the whole point.
  patch = String(error.stdout ?? '');
}
if (!patch) {
  throw new Error('the integration produced no diff');
}
patch = patch.split('clean/').join('').split('withguard/').join('');
const added = patch.split('\n').filter((l) => l.startsWith('+') && !l.startsWith('+++')).length;
const removed = patch.split('\n').filter((l) => l.startsWith('-') && !l.startsWith('---')).length;
process.stdout.write(patch);
process.stderr.write(`\n${added} lines added, ${removed} replaced\n`);

// A courtesy check: the document should be quoting this patch.
const doc = readFileSync(join(repoRoot, 'docs', 'INTEGRATION_DIFF.md'), 'utf8');
if (!doc.includes(patch.trim())) {
  process.stderr.write(
    'docs/INTEGRATION_DIFF.md does not contain this patch any more\n',
  );
  process.exitCode = 1;
}
