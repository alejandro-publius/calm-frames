# The upstream contribution

**October 10 final local check.** GitHub API confirms upstream main is still
`ef8e4da89b22ef7973d0d41beedfa2b42f7bb272`. All eleven issues and pull requests
were checked; none concerns this Shaka rejection fix. The current contribution
guide still asks for current-main, duplicate and local-test checks. The preserved
patched pristine sample passes all six focused tests again today, with a clean
working tree. The earlier observed-red controls and mock limitations below
remain relevant. Evidence: `results/upstream_review_2026-10-10.json`.

The contribution remains worthwhile and prepared as the two patches below.
Placeholder patch author metadata must be replaced with the entrant's chosen
public identity before publication. No fork, PR or qualifying public contribution
URL has been created. October 12 is a project target, not the hackathon deadline.

**Target:** [`AmazonAppDev/vega-video-sample`](https://github.com/AmazonAppDev/vega-video-sample), Amazon's reference video app for Vega. It has merged an outside contributor's pull request before: #7, opened June 18 2026 by an account with no association to the repository, merged July 6 2026. So they do take them.

**Status, Fri Oct 2 2026.** The two existing patches and their three added tests
were reapplied and revalidated locally against the pristine sample. They remain
ready-to-apply files in [`docs/upstream-pr/`](upstream-pr/). **No public fork,
issue or pull request has been created.** The contribution link remains due by
Monday October 12.

The Oct 2 read-only GitHub check found upstream `main` still at
[`ef8e4da89b22ef7973d0d41beedfa2b42f7bb272`](https://github.com/AmazonAppDev/vega-video-sample/commit/ef8e4da89b22ef7973d0d41beedfa2b42f7bb272).
The [contributor guide](https://github.com/AmazonAppDev/vega-video-sample/blob/main/CONTRIBUTING.md)
was unchanged, and targeted Shaka issue and pull request searches returned no
matches. The current local evidence is recorded below; the broader historical
suite results keep their original dates.

**Historical live repository check, Sep 17 2026:**

| What | Result, Sep 17 2026 |
|---|---|
| `main` | `ef8e4da89b22ef7973d0d41beedfa2b42f7bb272`, which is the same commit as tag `v0.24-RN83`, last pushed Aug 6 2026 |
| Does the patch still apply to `main` | Yes. `git am` of both patches onto a clean checkout of that commit applies with no fuzz, and the suite passes |
| Open issues | 0 |
| Every issue and pull request ever filed | 11, none of them about Shaka load failures or a stuck buffering spinner. This is not a duplicate |
| Licence | MIT-0 |

Re-run those checks before publishing. The patch has to go on top of the
upstream `main` that exists then.

---

## Which defect, and why this one

Three candidates came out of the build. All three are real symptoms we hit. Only one of them is a defect in the sample's own code that can be fixed in a small diff and covered by a test that runs without a device.

| Candidate | Verdict |
|---|---|
| A plain MP4 over HTTP never starts, and never shows an error either | **This one.** A sample-side defect, about 20 lines, unit-testable today, and the code's own documentation says it is meant to do the thing it does not do. |
| The player tears itself down when the app is backgrounded | Sample-side and fixable, but the teardown is the code doing what it says. The crisp bug next to it is narrower and worth a second pull request. Described below. |
| A video-only stream pauses a few seconds in | **Not a sample defect.** Nothing in the sample waits on audio, and there is no watchdog. The pause comes from below the sample. Mention as a known issue only. |

Two notes on scope. First, `app/` in this repository is a copy of the sample at tag `v0.24-RN83`, commit `ef8e4da89b22ef7973d0d41beedfa2b42f7bb272`, and commit `cf8b752` in this repository holds the untouched copy. The patch below was built from that untouched copy, never from our own tree, so every line number in this file is an upstream line number. `src/w3cmedia/shakaplayer/ShakaPlayer.ts` and `test/utils/VideoHandler.test.ts` are byte for byte upstream here. `src/utils/VideoHandler.ts` is not: Calm Frames added an optional media control handler to its constructor, 20 lines above the method this pull request touches, which shifts our copy down by 14 lines and changes nothing inside `loadAdaptiveMediaPlayer`. Read our `app/` copy for the fix and you will find the same code at a different line number. Second, `src/w3cmedia/shakaplayer/ShakaPlayer.ts` is checked in to the sample rather than generated. Its `shaka-setup/copyOutputs.sh` deletes the copy that comes out of the Shaka tarball and keeps the repository's own, with the comment "this file is checked in & modified". So a pull request may change it.

---

## The defect

A failed Shaka load becomes an unhandled rejection. The app never learns that the load failed, so `isVideoError` is never set, the error view never appears, and the buffering spinner stays up for good. From a user's point of view the app hangs on a spinner with no error, forever.

We hit this with a plain MP4 over HTTP. Any manifest or segment fetch that fails does the same thing: a 404, a redirect the player will not follow, a CORS refusal, a server that does not answer byte ranges.

### Root cause

`load()` is declared as returning `void` and fires its async work unawaited.

`src/w3cmedia/shakaplayer/ShakaPlayer.ts:200`

```ts
  load(content: any, _autoplay: boolean): void {
```

`src/w3cmedia/shakaplayer/ShakaPlayer.ts:456`

```ts
    this.internalLoad(content);
    console.log('shakaplayer: load() OUT');
  }
  private async internalLoad(content: any) {
    await this.player.load(content.uri);      // a rejection here escapes
    console.log('shakaplayer: setTextTrackVisibility');
    this.player.setTextTrackVisibility(true);
```

The caller has a guard, and the guard cannot fire, because it only catches a synchronous throw.

`src/utils/VideoHandler.ts:266`

```ts
        if (this.player.current) {
          try {
            this.player.current.load(this.data, false);     // returns void
            console.log(
              `[VideoHandler.ts] - loadStaticMediaPlayer - Loading Adaptive Media player (Shaka) with: ${this.data}`,
            );
          } catch (loadError) {                             // unreachable for an async failure
            console.error(
              '[VideoHandler.ts] - Error during Shaka player load:',
              loadError,
            );
            this.setIsVideoError(true);
          }
        }
```

This is a good bug to send upstream, because the method's own documentation states the intent that the code cannot meet. The comment block at `src/utils/VideoHandler.ts:238` to `:248` says:

```
   * This method:
   * 1. Configures Shaka Player settings (ABR, resolution limits)
   * 2. Initializes the Shaka Player instance
   * 3. Loads the streaming content
   * 4. Handles any loading errors
```

Step 4, on line 245, is the one that does not happen.

### Why the spinner never stops

`showBuffering` starts as `true` at `src/screens/PlayerScreen.tsx:73` and is only cleared on `playing`, `seeked`, `timeupdate` or an error. None of those arrive when a load fails, so it spins.

### The related contributor, worth mentioning in the pull request but not fixing in it

The sample never sniffs a URL or a MIME type. The only branch is a hand-declared JSON field:

- `src/utils/VideoHandler.ts:205`, `if (this.selectedFileType === VideoFileTypes.MP4)`, set at `:91` from `data.format`
- `src/types/TitleData.d.ts:15` admits `'DASH'` as a `VideoFormat`
- `src/data/videos/index.ts:7` has no `DASH` member of `VideoFileTypes` (it has `MPD`, `HLS`, `MP4` and `MPD_DRM`)

So a source whose `format` is not the exact literal `"MP4"` goes to Shaka, which cannot parse a raw MP4 as a manifest, and then fails the silent way described above. We are not proposing to change the format handling in this pull request, because that is a design decision for the maintainers. The point is that the silent failure is what makes it hard to diagnose.

---

## The fix

Two files of source and one of tests. They land as two commits.

**Commit 1, `ShakaPlayer.ts`: return the promise so a caller can see the failure.**

**Commit 2, `VideoHandler.ts` and `VideoHandler.test.ts`: catch it, report it, and cover it.**

`VideoHandler.ts` uses `Promise.resolve(...)` rather than `await`, which means it works against either signature, so the two commits are independent and either one is safe on its own.

### The patch

The two commits are saved as patch files and those files are the source of truth:

- [`docs/upstream-pr/0001-Return-the-load-promise-from-ShakaPlayer.load.patch`](upstream-pr/0001-Return-the-load-promise-from-ShakaPlayer.load.patch)
- [`docs/upstream-pr/0002-Report-a-failed-Shaka-load-instead-of-dropping-it.patch`](upstream-pr/0002-Report-a-failed-Shaka-load-instead-of-dropping-it.patch)

They were produced with `git format-patch` from a clean checkout of `ef8e4da`, and applied back onto another clean checkout with `git am` to prove they go on cleanly. The combined diff, for reading:

```diff
--- a/src/w3cmedia/shakaplayer/ShakaPlayer.ts
+++ b/src/w3cmedia/shakaplayer/ShakaPlayer.ts
@@ -197,7 +197,7 @@ export class ShakaPlayer implements PlayerInterface {
   }
   // End custom callbacks }}}
 
-  load(content: any, _autoplay: boolean): void {
+  load(content: any, _autoplay: boolean): Promise<void> {
     // Native HLS parsing setup
     if (ShakaPlayer.enableNativeParsing) {
       if (
@@ -453,8 +453,10 @@ export class ShakaPlayer implements PlayerInterface {
       });
     }
 
-    this.internalLoad(content);
     console.log('shakaplayer: load() OUT');
+    // Returned so the caller can see a rejected manifest or segment fetch.
+    // Before this, a failed load became an unhandled rejection.
+    return this.internalLoad(content);
   }
   private async internalLoad(content: any) {
     await this.player.load(content.uri);
--- a/src/utils/VideoHandler.ts
+++ b/src/utils/VideoHandler.ts
@@ -263,10 +263,28 @@ export class VideoHandler {
 
         if (this.player.current) {
           try {
-            this.player.current.load(this.data, false);
+            const loadResult = this.player.current.load(this.data, false);
             console.log(
               `[VideoHandler.ts] - loadStaticMediaPlayer - Loading Adaptive Media player (Shaka) with: ${this.data}`,
             );
+            // load() settles asynchronously, so the catch below can only ever
+            // see a synchronous throw. Without this, a rejected manifest or
+            // segment fetch becomes an unhandled rejection: isVideoError is
+            // never set, the error view never appears, and the buffering
+            // spinner stays up for good.
+            Promise.resolve(loadResult).catch((loadError) => {
+              if (!this.player.current) {
+                // Torn down while the load was in flight.
+                // destroyMediaPlayerSync nulls this ref before the rejection
+                // lands, and an aborted load is not a playback error.
+                return;
+              }
+              console.error(
+                '[VideoHandler.ts] - Error during Shaka player load:',
+                loadError,
+              );
+              this.setIsVideoError(true);
+            });
           } catch (loadError) {
             console.error(
               '[VideoHandler.ts] - Error during Shaka player load:',
--- a/test/utils/VideoHandler.test.ts
+++ b/test/utils/VideoHandler.test.ts
@@ -5,6 +5,7 @@ import { VideoPlayer } from '@amazon-devices/react-native-w3cmedia';
 import React from 'react';
 import { TitleData } from '../../src/types/TitleData';
 import { VideoHandler } from '../../src/utils/VideoHandler';
+import { ShakaPlayer } from '../../src/w3cmedia/shakaplayer/ShakaPlayer';
 
 jest.mock('react', () => ({
   ...jest.requireActual('react'),
@@ -155,4 +156,72 @@ describe('VideoHandler', () => {
       expect(result).toBe(true);
     });
   });
+  describe('loadAdaptiveMediaPlayer', () => {
+    afterEach(() => {
+      (ShakaPlayer as unknown as jest.Mock).mockReset();
+    });
+
+    it('reports a video error when the Shaka load rejects after returning', async () => {
+      const { mockVideoRef, mockSetIsVideoError, videoHandler } =
+        createVideoHandler();
+      mockVideoRef.current = {} as unknown as VideoPlayer;
+
+      const mockLoad = jest.fn().mockRejectedValue(new Error('manifest 404'));
+      (ShakaPlayer as unknown as jest.Mock).mockImplementation(() => ({
+        load: mockLoad,
+        unload: jest.fn(),
+      }));
+
+      videoHandler.loadAdaptiveMediaPlayer();
+      await new Promise(process.nextTick);
+
+      expect(mockLoad).toHaveBeenCalledTimes(1);
+      expect(mockSetIsVideoError).toHaveBeenCalledWith(true);
+    });
+
+    it('stays quiet when the player was torn down while the load was in flight', async () => {
+      const { mockVideoRef, mockPlayer, mockSetIsVideoError, videoHandler } =
+        createVideoHandler();
+      mockVideoRef.current = {} as unknown as VideoPlayer;
+
+      const mockLoad = jest
+        .fn()
+        .mockRejectedValue(new Error('LOAD_INTERRUPTED'));
+      (ShakaPlayer as unknown as jest.Mock).mockImplementation(() => ({
+        load: mockLoad,
+        unload: jest.fn(),
+      }));
+
+      videoHandler.loadAdaptiveMediaPlayer();
+      // Backing out of the player mid-load calls destroyMediaPlayerSync, which
+      // unloads Shaka and nulls this ref before the rejection lands. An
+      // aborted load is not a playback error and must not flash the error
+      // screen on the way out.
+      mockPlayer.current = null;
+      await new Promise(process.nextTick);
+
+      expect(mockLoad).toHaveBeenCalledTimes(1);
+      expect(mockSetIsVideoError).not.toHaveBeenCalled();
+    });
+
+    it('reports a video error when the Shaka load throws synchronously', async () => {
+      const { mockVideoRef, mockSetIsVideoError, videoHandler } =
+        createVideoHandler();
+      mockVideoRef.current = {} as unknown as VideoPlayer;
+
+      const mockLoad = jest.fn(() => {
+        throw new Error('bad configuration');
+      });
+      (ShakaPlayer as unknown as jest.Mock).mockImplementation(() => ({
+        load: mockLoad,
+        unload: jest.fn(),
+      }));
+
+      videoHandler.loadAdaptiveMediaPlayer();
+      await new Promise(process.nextTick);
+
+      expect(mockLoad).toHaveBeenCalledTimes(1);
+      expect(mockSetIsVideoError).toHaveBeenCalledWith(true);
+    });
+  });
 });
```

### Why the tests need no new mocks

The sample's own `jest.setup.ts` already mocks the module:

```ts
jest.mock('./src/w3cmedia/shakaplayer/ShakaPlayer', () => ({
  ShakaPlayer: jest.fn(),
}));
```

so each test only re-implements that constructor for its own case, and the `afterEach` resets it so the three cannot leak into each other. `test/utils/VideoHandler.test.ts` already neutralises the `useCallback`-inside-a-class problem with its own `jest.mock('react', ...)`, and `createVideoHandler()` already returns `mockSetIsVideoError` and `mockPlayer`. No device, no native module, no new dependency.

The three tests are three different claims:

1. **The async one** is the bug. It fails on unmodified upstream.
2. **The teardown one** is the guard inside the fix. Backing out of the player mid-load makes Shaka reject with `OPERATION_ABORTED` or `LOAD_INTERRUPTED`, and that must not flash the error screen on the way out. Without the guard, this test goes red.
3. **The synchronous one** pins the path that already worked. It passes with or without the change, on purpose. Without it, someone could satisfy the first test through the pre-existing `catch` block and think the async path was covered.

---

## What was verified, and how

**Revalidated Oct 2 2026, Node 22.23.2.** A fresh scratch repository was
extracted with `git archive cf8b752:app`, the pristine local copy of the current
upstream commit. Both existing patches applied cleanly with `git am`.
Dependencies were borrowed through scratch-only symlinks and the same four
empty mock-resolution stubs described below. The project checkout and installed
dependencies were not modified.

| Current focused check | Result |
|---|---|
| Pristine `VideoHandler.test.ts` | 3 passed |
| Both patches applied, then restored after controls | 6 passed in each run |
| Remove the new promise rejection handler | 2 failed, 4 passed |
| Remove only its teardown guard | 1 failed, 5 passed |
| Revert only `ShakaPlayer.ts`, keep the handler | 6 passed; the existing mocked-Shaka coverage gap remains |
| ESLint and Prettier on the three changed files | Both exit 0 |
| Final scratch diff and working tree | No whitespace errors; clean after restoration |

The commands, return codes and scratch provenance are recorded in
`.logs/upstream-shaka-review.json`; individual logs use
`.logs/upstream-shaka-*.log`. This recheck covers promise error handling in unit
tests. It adds no device or external adoption evidence. The historical full
suite and type checks below were not rerun in this checkpoint.

Two clean checkouts of upstream `ef8e4da` were made in a scratch directory from commit `cf8b752` of this repository, which is that commit byte for byte. `node_modules` is a directory of symlinks into this repository's `app/node_modules`, plus four resolution stubs for `@amazon-devices` packages that Calm Frames removed from its own install and the pristine `jest.setup.ts` still mocks: `kepler-channel`, `kepler-media-account-login`, `kepler-media-content-launcher` and `kepler-epg-sync-scheduler`. Each stub is an empty module that exists only so `jest.mock` can resolve a path. Nothing else about the sample was touched, and this repository's own `node_modules` was not written to.

Historical broad run on Sep 17 2026, Node 22.23.2:

| Step | Result |
|---|---|
| `jest test/utils/VideoHandler.test.ts` on unmodified upstream | 3 passed |
| Add the three new tests, **no fix applied** | **2 failed**, 4 passed. The async test fails with `setIsVideoError` "Number of calls: 0". The teardown test fails on the unhandled `LOAD_INTERRUPTED` rejection, which is the bug itself showing up in the test runner. The synchronous test passes, as it should. |
| Apply both halves of the fix | 6 passed |
| Full suite, unmodified upstream | 2 suites failed, 61 passed, 1 skipped. 3 tests failed, 348 passed, 4 skipped |
| Full suite, with the fix | 2 suites failed, 61 passed, 1 skipped. 3 tests failed, **351** passed, 4 skipped. The three extra passes are the new tests |
| `eslint` on all three changed files | clean, exit 0 |
| `prettier --check` on all three changed files | clean |
| `tsc --noEmit` | the same 4 pre-existing `TS2742` errors with and without the change |
| `git am` of both patch files onto a second clean checkout | applies with no fuzz, 6 passed |

**The three failing tests and the four type errors are both artifacts of where the checkout lives, and neither is an upstream defect.** The failures are snapshot mismatches in `DrawerContent.test.tsx` and `Preview.test.tsx`, where the recorded snapshot holds an asset `testUri` that is written relative to the project root: from a deep scratch path it comes out absolute and the snapshot does not match. The same two suites pass in `app/` in this repository, which is the same code at a normal path. The `TS2742` errors are the usual complaint about a symlinked `node_modules` outside the project and name four store slices nobody touched. Both appear identically with and without the change.

One real upstream problem did turn up while running the suite, and it is not this pull request's subject: **`npx jest --ci` exits 1 on a clean checkout with every test passing**, because `test/blocks/components/MediaItemShoveler/__snapshots__/MediaItemShoveler.test.tsx.snap` holds two snapshot entries no current test produces, and `--ci` treats an obsolete snapshot as a failure. Deleting those two entries fixes it. It is worth a sentence in the pull request so a reviewer does not blame this change for a red run, and it is worth a separate two-line pull request.

**The guards were broken on purpose and seen to go red**, which is the rule in this project: a green new test proves nothing on its own.

| Mutation | Result |
|---|---|
| Remove the whole `Promise.resolve(loadResult).catch(...)` block | The async test and the teardown test both go red. Nothing else moves |
| Remove only the `if (!this.player.current) return;` guard inside the catch | Only the teardown test goes red |
| Revert only `ShakaPlayer.ts`, keep the caller-side catch | **All six still pass.** This is the limitation below, measured rather than assumed |

That last row is the honest gap, and the pull request says so: the test covers the `VideoHandler` half, because `jest.setup.ts` mocks `ShakaPlayer`. The `ShakaPlayer.ts` return type change has no unit coverage, and reverting it alone would not turn any test red.

---

## Risk

Real and contained. Streams that used to hang on a spinner now show the error view. That is the point of the change, and it is still a behaviour change for anyone who had learned to live with the spinner.

The one race worth naming is teardown. Backing out of the player mid-load calls `destroyMediaPlayerSync`, which calls `unload()`, which makes Shaka reject the in-flight `load()` with `OPERATION_ABORTED` or `LOAD_INTERRUPTED`. That would flash the error screen on the way out. The `if (!this.player.current) return;` guard covers it, because `destroyMediaPlayerSync` nulls `this.player.current` at `src/utils/VideoHandler.ts:549` before the rejection can land, and the third test in the file holds it to that.

---

## The pull request, ready to paste

### Title

```
[BUG] Shaka load failures are silently dropped: player hangs on the buffering spinner with no error
```

### Body

```
## Description

### For Bug Reports:

| Field | Value |
|-------|-------|
| Device | Vega Virtual Device. No physical device was used |
| App Version | 3.24.0 (manifest.toml) |
| Image Build | Vega OS 1.2 (TV Ship/101520710) |
| VDT Version | Vega CLI 1.3.4, Vega SDK 0.24.9914 |
| Video/Img showing the issue | Not included. The symptom is a spinner that never stops, which is not informative as a video. The unit tests in this PR reproduce it deterministically. |
| Expected Behavior | When Shaka fails to load a source, the app reports a playback error. `loadAdaptiveMediaPlayer` documents this itself: its comment block says the method "4. Handles any loading errors", and it has a try/catch around the load that calls `setIsVideoError(true)`. |
| Current Behaviour | The error is never seen. `ShakaPlayer.load()` is declared `void` and calls `internalLoad(content)` without returning or awaiting it, so a rejection from `this.player.load(content.uri)` becomes an unhandled rejection. The caller's try/catch in `VideoHandler.loadAdaptiveMediaPlayer` can only catch a synchronous throw, so it never fires. `setIsVideoError` is never called, `ErrorView` never renders, and `showBuffering` (initialised true in `PlayerScreen.tsx`, cleared only on `playing` / `seeked` / `timeupdate` / error) stays up for good. The user sees a spinner forever with no error. |
| Reproduction Rate | Deterministic. The unit tests added here reproduce it on every run with no device. On the Vega Virtual Device it reproduced each time we handed Shaka a plain MP4 over HTTP, which happens when a title's `format` field is not the literal "MP4", and each time the server answered a byte range request with 200 instead of 206. Any other source Shaka cannot load, such as a 404 manifest, takes the same code path; we did not count trials of those. |

For Pull Requests:

* This PR addresses issue #: (filled in when the issue is filed)

* Changes made:

  1. `src/w3cmedia/shakaplayer/ShakaPlayer.ts` - `load()` now returns the
     promise from `internalLoad()` instead of dropping it, and its return type
     changes from `void` to `Promise<void>`. Two lines.

  2. `src/utils/VideoHandler.ts` - `loadAdaptiveMediaPlayer` attaches a
     `.catch` to the result of `load()` and calls `setIsVideoError(true)` from
     it, with a guard that stays quiet when the player was torn down while the
     load was in flight (`destroyMediaPlayerSync` nulls `this.player.current`
     before the rejection lands, and an aborted load is not a playback error).
     It uses `Promise.resolve(...)` rather than `await`, so it behaves
     correctly whether `load()` returns a promise or not, which keeps the two
     changes independent.

  3. `test/utils/VideoHandler.test.ts` - three tests. One proves an
     asynchronously rejected load sets the video error. One proves an aborted
     load during teardown does not, which is the guard above. One proves a
     synchronously thrown load still does, so the existing behaviour is pinned
     and the two paths cannot be confused for each other.

  Not changed, but worth flagging: the sample picks its player purely from the
  hand-declared `format` field (`VideoHandler.ts`, `selectedFileType`), and
  `VideoFormat` in `types/TitleData.d.ts` admits `'DASH'` while
  `VideoFileTypes` in `data/videos/index.ts` does not. Anything whose `format`
  is not exactly "MP4" goes to Shaka. That is a design decision for you rather
  than something to change in a bug fix, but it is how we first hit this: a
  plain MP4 over HTTP went to Shaka, failed, and said nothing.

* Testing performed:

  - `npx jest test/utils/VideoHandler.test.ts` against unmodified upstream:
    3 passed.
  - Added the three tests with no fix applied: the async test fails
    (`setIsVideoError` "Number of calls: 0") and the teardown test fails on the
    unhandled rejection, which is the bug itself surfacing in the runner. The
    synchronous test passes. This is the guard being seen to fail before it is
    trusted.
  - Applied the fix: 6 passed.
  - Full suite before and after: the same suites and the same three tests fail
    either way in our environment, for reasons unrelated to this change, and
    `test/utils/VideoHandler.test.ts` moves from failing to passing. No new
    failure is introduced.
  - `eslint` and `prettier --check` on all three changed files: clean.
  - Removing only the new `.catch` block turns the async and teardown tests red
    again. Removing only the teardown guard turns the teardown test red.
    Nothing else moves either way.

  One limitation, stated plainly: the tests cover the `VideoHandler` half,
  because `jest.setup.ts` mocks `ShakaPlayer`. The `ShakaPlayer.ts` return type
  change has no unit coverage, and we checked that: reverting it alone leaves
  all six tests green. It is a one-line contract change.

  Unrelated, and flagging it so a red CI run is not blamed on this change:
  `npx jest --ci` exits 1 on a clean checkout of main at ef8e4da (Aug 6 2026)
  with every test passing, because
  `test/blocks/components/MediaItemShoveler/__snapshots__/MediaItemShoveler.test.tsx.snap`
  holds two snapshot entries that no current test produces, and `--ci` counts
  an obsolete snapshot as a failure. Happy to send that two-line deletion as a
  separate PR if it would help.

* Dependencies added/modified: none.

By submitting this pull request, I confirm that you can use, modify, copy, and redistribute this contribution, under the terms of your choice.

### Additional Notes

We found this while building an accessibility layer on top of this sample for
the Fire TV track of the Amazon Developer Hackathon. The silent failure cost us
a long time, because a spinner that never stops looks like a network problem
rather than a load error, and there is nothing in the log that says otherwise
unless you are watching for an unhandled rejection.

Happy to split this into two pull requests, or to drop the `ShakaPlayer.ts`
half and keep only the caller-side `.catch`, if you would rather not change
that file. The caller-side change is useful on its own once `load()` returns
anything awaitable, and harmless if it never does.

### Checklist

* [x] I have reviewed my own code
* [x] I have tested my changes
* [ ] I have updated the documentation accordingly. No documentation change
  is included: the comment block on `loadAdaptiveMediaPlayer` already says the
  method handles loading errors, and this change makes the code match it.
```

---

## How to open it

`CONTRIBUTING.md` in that repository asks contributors to work against the latest `main`, to check existing and recently merged pull requests first, and to open an issue to discuss any significant work. Filing the bug first also means the contribution URL exists earlier, which is what the Devpost Open Source field needs.

1. **Check first.** Look through open and recently closed issues and pull requests for anything about Shaka load failures or a stuck buffering spinner. As of Sep 17 there were none and no open issues at all, but check again on the day. Re-read `CONTRIBUTING.md` in case it changed.
2. **File the issue.** Use the `[BUG]` table above, without the "For Pull Requests" part. Note its number.
3. **Fork** `AmazonAppDev/vega-video-sample` to your own account.
4. **Clone your fork and branch from the latest `main`:**

   ```sh
   git clone https://github.com/<your-username>/vega-video-sample.git
   cd vega-video-sample
   git checkout -b fix/surface-shaka-load-failures
   ```

5. **Apply the two commits.** This is the whole change, messages included:

   ```sh
   git am /path/to/calm-frames/docs/upstream-pr/0001-*.patch \
          /path/to/calm-frames/docs/upstream-pr/0002-*.patch
   git rebase --exec 'git commit --amend --no-edit --reset-author' HEAD~2
   ```

   The second line matters. The patches carry a placeholder author, `Your Name <you@example.com>`, because this machine must not guess which identity you want on a public contribution. The rebase rewrites both commits as you. Check with `git log --format='%an <%ae> %s' -2` before pushing.

   If `git am` refuses because `main` has moved on, fall back to `git apply` on each patch and commit twice by hand, with the messages from the patch files. The three anchors are small: `load(content: any, _autoplay: boolean): void {`, `this.internalLoad(content);` and `this.player.current.load(this.data, false);`.

6. **Run the tests** with their full dependency set:

   ```sh
   npm install
   npx jest test/utils/VideoHandler.test.ts
   npx eslint src/utils/VideoHandler.ts test/utils/VideoHandler.test.ts src/w3cmedia/shakaplayer/ShakaPlayer.ts --ext .ts
   npx prettier --check src/utils/VideoHandler.ts test/utils/VideoHandler.test.ts src/w3cmedia/shakaplayer/ShakaPlayer.ts
   ```

   Expect 6 passed in that file. `npm install` runs the Shaka build in `postinstall`, which needs a JDK on the path; see `docs/ENVIRONMENT.md`.

7. **Push the branch to your fork and open the pull request** with the title and body above, referencing the issue number.

8. **Record the links.** Paste the pull request URL into `docs/SUBMISSION.md` field 12.1 and your GitHub username into 12.3. The fields are listed at the end of this file.

One decision that is yours, not this machine's: the patches carry no co-author or generated-with trailer. Our own repository puts one on every commit. A contribution to someone else's repository goes out under your name, so the trailer is left off rather than added on your behalf. Add one before pushing if you would rather it were there.

It does not need to be merged by the deadline. It needs to exist by **Monday October 12**. The only outside pull request this repository has ever merged was a two-line documentation change, and it took eighteen days, so plan for the link rather than the merge.

---

## For Lane H: the SUBMISSION.md fields

Three fields in `docs/SUBMISSION.md` depend on this file. None of them can be filled from here.

| Field | What goes in it | State |
|---|---|---|
| 12.1 Contribution URL | The pull request URL, `https://github.com/AmazonAppDev/vega-video-sample/pull/<n>`. If the issue is filed first and the pull request is late, the issue URL is a usable stand-in on the same repository | **NEEDS ALEX.** Nothing is pushed. Due Mon Oct 12 |
| 12.3 GitHub username | The account that owns the fork, which is the account that appears on the pull request | **NEEDS ALEX.** The repository here is under `alejandro-publius`; confirm the same account forks upstream, or say which one does |
| 12.4 What we did, and why it matters | Written. The upstream half says three tests, two of which fail without the fix | Ready |

The vega-video-sample feedback already carries two things measured while this was prepared: `jest --ci` exits 1 on a clean checkout over two obsolete snapshot entries, and `main` has not moved since Aug 6 2026. Both are in `docs/FEEDBACK.md` section 3, which is what `docs/SUBMISSION.md` section 10 pastes from.

---

## The second candidate, if there is time

Worth a separate pull request, and not needed for the submission.

`handleAppStateChange` in `src/screens/PlayerScreen.tsx:252` reuses `navigateBack`, which is the hardware-back UI affordance, as its lifecycle teardown. `navigateBack` has an early return at `:231`:

```ts
  const navigateBack = useCallback(() => {
    if (captionStatus.current) {
      captionStatus.current = false;
      return true;
    }
```

`captionStatus` is a one-shot latch set when the captions menu consumes a BACK press. If the app is backgrounded while that latch is set, the media pipeline is never released at all: no `clearSurfaceHandle`, no `destroyVideoElements`. Separately, the `setTimeout(() => navigation.goBack(), 700)` at `:247` is never stored in the component's `timer`, so a back press racing a background event can pop the stack twice.

The fix is to extract a `releasePlayer()` from the body of `navigateBack` and call that from `handleAppStateChange`, leaving the captions latch on the back-press path where it belongs. It is testable without a device: `jest.setup.ts` already mocks `useKeplerAppStateManager().addAppStateListener`, so a test can capture the handler and assert that teardown runs with the latch set.

## The third candidate

Not a sample defect, and there is nothing to send upstream. A search across the whole pristine `src/` for `audioTrack`, `audioTracks`, `readyState`, `stalled`, `canplay`, `canPlayType` and `preload` finds only two unrelated Redux `preloadedState` hits. There is no buffering watchdog and nothing that waits on audio. The sample's only handlers are `onWaiting`, which shows the spinner, and `onPlaying` and `onSeeked`, which hide it. None of them pause. A video-only stream pausing a few seconds in comes from below the sample, in Shaka or in the W3C media pipeline. It stays in our own notes as a working constraint: every test clip we generate carries an audio track, even a silent one.
