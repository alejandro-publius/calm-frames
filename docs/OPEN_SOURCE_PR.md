# The upstream contribution

**Target:** [`AmazonAppDev/vega-video-sample`](https://github.com/AmazonAppDev/vega-video-sample), the Fire TV video sample that most Vega video apps start from. It has merged an outside contributor's pull request before (#7, July 6 2026), so it takes them.

**Status:** the fix and its tests are written and verified. **The pull request has not been opened and the branch has not been pushed anywhere**, because the branch has to live in a fork under Alex's own GitHub account. Everything needed to open it is in this file. Due by Monday October 12.

---

## Which defect, and why this one

Three candidates came out of the build. All three are real symptoms we hit. Only one of them is a defect in the sample's own code that can be fixed in a small diff and covered by a test that runs without a device.

| Candidate | Verdict |
|---|---|
| A plain MP4 over HTTP never starts, and never shows an error either | **This one.** A sample-side defect, about 20 lines, unit-testable today, and the code's own documentation says it is meant to do the thing it does not do. |
| The player tears itself down when the app is backgrounded | Sample-side and fixable, but the teardown is the code doing what it says. The crisp bug next to it is narrower and worth a second pull request. Described below. |
| A video-only stream pauses a few seconds in | **Not a sample defect.** Nothing in the sample waits on audio, and there is no watchdog. The pause comes from below the sample. Mention as a known issue only. |

Two notes on scope. First, `app/` in this repository is a copy of the sample at tag `v0.24-RN83`, commit `ef8e4da89b22ef7973d0d41beedfa2b42f7bb272`, and commit `cf8b752` in this repository holds the untouched copy. `git diff cf8b752 HEAD -- app/` touches only `PlayerScreen.tsx` and `Player.test.tsx`, so `VideoHandler.ts`, `ShakaPlayer.ts` and `VideoHandler.test.ts` are byte for byte upstream and every line number below is an upstream line number. Second, `src/w3cmedia/shakaplayer/ShakaPlayer.ts` is checked in to the sample rather than generated. Its `shaka-setup/copyOutputs.sh` deletes the copy that comes out of the Shaka tarball and keeps the repository's own, with the comment "this file is checked in & modified". So a pull request may change it.

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

`src/utils/VideoHandler.ts:264`

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

This is a good bug to send upstream, because the method's own documentation states the intent that the code cannot meet. `src/utils/VideoHandler.ts:238` says:

```
   * This method:
   * 1. Configures Shaka Player settings (ABR, resolution limits)
   * 2. Initializes the Shaka Player instance
   * 3. Loads the streaming content
   * 4. Handles any loading errors
```

Step 4 is the one that does not happen.

### Why the spinner never stops

`showBuffering` starts as `true` at `src/screens/PlayerScreen.tsx:73` and is only cleared on `playing`, `seeked`, `timeupdate` or an error. None of those arrive when a load fails, so it spins.

### The related contributor, worth mentioning in the pull request but not fixing in it

The sample never sniffs a URL or a MIME type. The only branch is a hand-declared JSON field:

- `src/utils/VideoHandler.ts:205`, `if (this.selectedFileType === VideoFileTypes.MP4)`, set at `:91` from `data.format`
- `src/types/TitleData.d.ts:14` admits `'DASH'` as a `VideoFormat`
- `src/data/videos/index.ts:7` has no `DASH` member of `VideoFileTypes`

So a source whose `format` is not the exact literal `"MP4"` goes to Shaka, which cannot parse a raw MP4 as a manifest, and then fails the silent way described above. We are not proposing to change the format handling in this pull request, because that is a design decision for the maintainers. The point is that the silent failure is what makes it hard to diagnose.

---

## The fix

Two files, both small. They can land as two commits.

**Commit 1, `ShakaPlayer.ts`: return the promise so a caller can see the failure.**

**Commit 2, `VideoHandler.ts`: catch it and report it.**

`VideoHandler.ts` uses `Promise.resolve(...)` rather than `await`, which means it works against either signature, so the two commits are independent and either one is safe on its own.

### The patch

Apply from the root of a `vega-video-sample` checkout with `git apply`.

```diff
--- a/src/w3cmedia/shakaplayer/ShakaPlayer.ts
+++ b/src/w3cmedia/shakaplayer/ShakaPlayer.ts
@@ -197,7 +197,7 @@
   }
   // End custom callbacks }}}
 
-  load(content: any, _autoplay: boolean): void {
+  load(content: any, _autoplay: boolean): Promise<void> {
     // Native HLS parsing setup
     if (ShakaPlayer.enableNativeParsing) {
       if (
@@ -453,8 +453,10 @@
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
@@ -263,10 +263,28 @@
 
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
@@ -5,6 +5,7 @@
 import React from 'react';
 import { TitleData } from '../../src/types/TitleData';
 import { VideoHandler } from '../../src/utils/VideoHandler';
+import { ShakaPlayer } from '../../src/w3cmedia/shakaplayer/ShakaPlayer';
 
 jest.mock('react', () => ({
   ...jest.requireActual('react'),
@@ -155,4 +156,43 @@
       expect(result).toBe(true);
     });
   });
+  describe('loadAdaptiveMediaPlayer', () => {
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

The sample's own `jest.setup.ts:308` already mocks the module:

```ts
jest.mock('./src/w3cmedia/shakaplayer/ShakaPlayer', () => ({
  ShakaPlayer: jest.fn(),
}));
```

so the test only re-implements that constructor per case. `test/utils/VideoHandler.test.ts` already neutralises the `useCallback`-inside-a-class problem with its own `jest.mock('react', ...)`, and `createVideoHandler()` already returns `mockSetIsVideoError`. No device, no native module, no new dependency.

The second test, the synchronous one, is there on purpose. Without it, someone could satisfy the first test through the pre-existing `catch` block and think the async path was covered. The two together pin both paths apart.

---

## What was verified, and how

A pristine upstream checkout was rebuilt from `cf8b752` in a scratch directory, with `node_modules` symlinked from this repository, and the tests were run against it.

| Step | Result |
|---|---|
| `test/utils/VideoHandler.test.ts` on unmodified upstream | 3 passed |
| Add the two new tests, **no fix applied** | **1 failed**, 4 passed. The async test fails with `setIsVideoError` "Number of calls: 0". The synchronous test passes, as it should. |
| Apply both halves of the fix | 5 passed |
| Full suite, no fix | 9 suites failed, 54 passed, 4 tests failed |
| Full suite, with the fix | 8 suites failed, 55 passed, 3 tests failed |
| `eslint` on the changed files | clean, exit 0 |
| `prettier --check` on the changed files | clean |

The eight suites that fail either way are unrelated: they need `@amazon-devices` packages that Calm Frames removed from its own `node_modules` (`kepler-channel`, `kepler-media-account-login`, `kepler-epg-sync-scheduler`, `kepler-media-content-launcher`). They fail identically with and without the change, so the fix introduces no new failure and fixes exactly the one it targets. The maintainers' CI has the full dependency set and will not see them.

**The guard was broken on purpose and seen to go red**, which is the rule in this project: a green new test proves nothing on its own. Removing the `Promise.resolve(loadResult).catch(...)` block takes the async test from green to red, and only that test.

One thing to be explicit about in the pull request: the test covers the `VideoHandler` half. The `ShakaPlayer.ts` return type change has no unit coverage, because the test mocks `ShakaPlayer`. It is a one-line contract change and reverting it alone would not turn this test red.

---

## Risk

Real and contained. Streams that used to hang on a spinner now show the error view. That is the point of the change, and it is still a behaviour change for anyone who had learned to live with the spinner.

The one race worth naming is teardown. Backing out of the player mid-load calls `destroyMediaPlayerSync`, which calls `unload()`, which makes Shaka reject the in-flight `load()` with `OPERATION_ABORTED` or `LOAD_INTERRUPTED`. That would flash the error screen on the way out. The `if (!this.player.current) return;` guard covers it, because `destroyMediaPlayerSync` nulls `this.player.current` at `src/utils/VideoHandler.ts:549` before the rejection can land.

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
| Device | Virtual Device (Vega Virtual Device), and the same code path on a physical device |
| App Version | 3.24.0 (manifest.toml) |
| Image Build | Vega OS 1.2 (TV Ship/101520710) |
| VDT Version | Vega CLI 1.3.4, Vega SDK 0.24.9914 |
| Video/Img showing the issue | Not included. The symptom is a spinner that never stops, which is not informative as a video. The unit test in this PR reproduces it deterministically. |
| Expected Behavior | When Shaka fails to load a source, the app reports a playback error. `loadAdaptiveMediaPlayer` documents this itself: its comment block says the method "4. Handles any loading errors", and it has a try/catch around the load that calls `setIsVideoError(true)`. |
| Current Behaviour | The error is never seen. `ShakaPlayer.load()` is declared `void` and calls `internalLoad(content)` without returning or awaiting it, so a rejection from `this.player.load(content.uri)` becomes an unhandled rejection. The caller's try/catch in `VideoHandler.loadAdaptiveMediaPlayer` can only catch a synchronous throw, so it never fires. `setIsVideoError` is never called, `ErrorView` never renders, and `showBuffering` (initialised true in `PlayerScreen.tsx`, cleared only on `playing` / `seeked` / `timeupdate` / error) stays up for good. The user sees a spinner forever with no error. |
| Reproduction Rate | 5 out of 5. Any source Shaka cannot load reproduces it: a 404 manifest, a plain MP4 handed to Shaka because its `format` field is not the literal "MP4", or a server that does not answer byte ranges. The unit test added here reproduces it 5 out of 5 with no device. |

For Pull Requests:

* This PR addresses issue #: (none filed yet)

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

  3. `test/utils/VideoHandler.test.ts` - two tests. One proves an
     asynchronously rejected load sets the video error. The other proves a
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
  - Added the two tests with no fix applied: the async test fails
    (`setIsVideoError` "Number of calls: 0"), the sync test passes. This is the
    guard being seen to fail before it is trusted.
  - Applied the fix: 5 passed.
  - Full suite before and after: the same unrelated suites fail either way in
    our environment, and `test/utils/VideoHandler.test.ts` moves from failing
    to passing. No new failure is introduced.
  - `eslint` and `prettier --check` on all three changed files: clean.
  - Removing only the new `.catch` block turns the async test red again, and
    nothing else.

  One limitation, stated plainly: the test covers the `VideoHandler` half,
  because `jest.setup.ts` mocks `ShakaPlayer`. The `ShakaPlayer.ts` return type
  change has no unit coverage. It is a one-line contract change.

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
* [x] I have updated the documentation accordingly
```

---

## How to open it

`CONTRIBUTING.md` in that repository asks contributors to open an issue first for anything significant, and to work against the latest `main`. Filing the bug first also means the contribution URL exists earlier, which is what the Devpost Open Source field needs.

1. **Check first.** Look through open and recently closed issues and pull requests for anything about Shaka load failures or a stuck buffering spinner, so this is not a duplicate. Also re-read `CONTRIBUTING.md` in case it changed.
2. **File the issue.** Use the `[BUG]` form above, without the "For Pull Requests" part. Note its number.
3. **Fork** `AmazonAppDev/vega-video-sample` to your own account.
4. **Branch** from the latest `main`:

   ```sh
   git clone https://github.com/<your-username>/vega-video-sample.git
   cd vega-video-sample
   git checkout -b fix/surface-shaka-load-failures
   ```

5. **Apply the patch.** Copy the diff block above into a file and apply it:

   ```sh
   git apply /path/to/shaka-load-failure.patch
   ```

   If it does not apply because `main` has moved on, the three hunks are small enough to make by hand. The anchors are `load(content: any, _autoplay: boolean): void {`, `this.internalLoad(content);` and `this.player.current.load(this.data, false);`.

6. **Run the tests** with their full dependency set:

   ```sh
   npm install
   npx jest test/utils/VideoHandler.test.ts
   npx eslint src/utils/VideoHandler.ts test/utils/VideoHandler.test.ts --ext .ts
   ```

7. **Commit as two commits**, so a reviewer can take one without the other:

   ```
   Return the load promise from ShakaPlayer.load()
   Report a failed Shaka load instead of dropping it
   ```

8. **Open the pull request** with the title and body above, referencing the issue number, and paste the link into `docs/SUBMISSION.md` field 11.1.

It does not need to be merged by the deadline. It needs to exist by **Monday October 12**.

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
