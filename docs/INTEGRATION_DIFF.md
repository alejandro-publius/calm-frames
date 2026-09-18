# Adding the flash guard to a Vega video app

This is the whole change, made against a clean checkout of
[AmazonAppDev/vega-video-sample](https://github.com/AmazonAppDev/vega-video-sample)
at tag `v0.24-RN83`. The four files below came out of that checkout with
`git show`, the hook was added to them, and `git diff` produced what follows.
Nothing here is illustrative: it is the output of the diff, and
`hook/tools/make_integration_diff.mjs` regenerates it.

**32 lines added, 2 replaced, across four files.** Two of those files only
pass a prop along.

## What the app gets for it

- every flagged part of a title is hidden before it starts, while the sound and
  the captions keep playing;
- a card five seconds ahead saying it is coming, with a Skip button that has
  D-pad focus, and a card afterwards saying what was hidden;
- a map that is missing, stale, unsigned, unreadable or bound to a different
  file keeps the picture hidden and says the title is not checked yet;
- every way of moving the playhead, including Alexa and the remote's transport
  commands, covers the picture before it moves;
- a VoiceView announcement for every card.

## Before you start

    npm install @calm-frames/flash-guard

Two things the app has to supply:

- `FLASH_MAP_PUBLIC_KEY`, the base64 Ed25519 public key whoever analysed the
  content signs maps with. The app ships the public half only.
- `data.sha256` and `data.flashMapUrl` on each catalog entry: the hash of the
  file that will play, and where its map lives. The hash is the binding. A map
  that verifies against a different file says nothing about this one.

The sample's `manifest.toml` already carries the `IMediaPlaybackServer` extras
block that Alexa and remote transport commands need, so there is no manifest
change in this diff. An app that removed that block has to put it back, and add
`com.amazon.devconf.privilege.accessibility` under `[wants]` for the
announcements.

## The diff

```diff
diff --git src/components/Seekbar.tsx src/components/Seekbar.tsx
index d1776de..46a8b23 100644
--- src/components/Seekbar.tsx
+++ src/components/Seekbar.tsx
@@ -44,2 +44,3 @@ const Seekbar = ({
   seekBarRef,
+  requestSeek,
   testID,
@@ -51,2 +52,3 @@ const Seekbar = ({
   seekBarRef: React.MutableRefObject<null>;
+  requestSeek: (source: SeekSource, targetMs: number) => void;
   testID?: string;
@@ -94,3 +96,3 @@ const Seekbar = ({
       setProgress(value);
-      videoRef.current.fastSeek(value);
+      requestSeek('seek-bar', value * SECOND_IN_MILIS);
       videoRef.current.play();
diff --git src/screens/PlayerScreen.tsx src/screens/PlayerScreen.tsx
index a8a3bbf..4c8aa92 100644
--- src/screens/PlayerScreen.tsx
+++ src/screens/PlayerScreen.tsx
@@ -24,2 +24,8 @@ import {
 } from '@amazon-devices/react-native-w3cmedia';
+import {
+  CalmCard,
+  CoverLayer,
+  SafeMediaControlHandler,
+  useFlashGuard,
+} from '@calm-frames/flash-guard';
 import isEqual from 'lodash/isEqual';
@@ -106,2 +112,11 @@ const PlayerScreen = ({
 
+  const guard = useFlashGuard({
+    mediaRef: videoRef,
+    mapUrls: { wcag: data.flashMapUrl },
+    expectedSha256: data.sha256,
+    publicKeyBase64: FLASH_MAP_PUBLIC_KEY,
+    ready: isVideoInitialized,
+    titleName: data.title,
+  });
+
   const videoHandler = new VideoHandler(
@@ -115,2 +130,7 @@ const PlayerScreen = ({
     setShowBuffering,
+    // Alexa and the remote's transport commands go through the guard too.
+    new SafeMediaControlHandler({
+      engine: guard.seekEngine,
+      getCurrentMs: () => (videoRef.current?.currentTime ?? 0) * 1000,
+    }),
   );
@@ -435,2 +455,3 @@ const PlayerScreen = ({
             />
+            <CoverLayer visible={guard.covered} mode={guard.coverMode} />
             <KeplerCaptionsView
@@ -448,4 +469,6 @@ const PlayerScreen = ({
         )}
+        <CalmCard card={guard.card} onSkip={guard.skipTo} />
         {showVideoPlayerUI && (
           <VideoPlayerUI
+            requestSeek={guard.requestSeek}
             videoRef={videoRef}
diff --git src/w3cmedia/mediacontrols/PlaybackControls.tsx src/w3cmedia/mediacontrols/PlaybackControls.tsx
index 7c854d3..51cbff1 100644
--- src/w3cmedia/mediacontrols/PlaybackControls.tsx
+++ src/w3cmedia/mediacontrols/PlaybackControls.tsx
@@ -34,3 +34,5 @@ export const seek = (
     }
-    videoRef.current.currentTime = newTime;
+    // Every way of moving the playhead goes through the guard, which covers
+    // the picture first when the target lands in a flagged part.
+    requestSeek(seekSeconds >= 0 ? 'dpad-fast-forward' : 'dpad-rewind', newTime * 1000);
     if (videoRef.current.paused) {
diff --git src/w3cmedia/mediacontrols/VideoPlayerUI.tsx src/w3cmedia/mediacontrols/VideoPlayerUI.tsx
index b15cfd4..4873b25 100644
--- src/w3cmedia/mediacontrols/VideoPlayerUI.tsx
+++ src/w3cmedia/mediacontrols/VideoPlayerUI.tsx
@@ -38,2 +38,3 @@ interface VideoPlayerUIProps {
   videoData: TitleData;
+  requestSeek: (source: SeekSource, targetMs: number) => void;
 }
@@ -55,2 +56,3 @@ export const VideoPlayerUI = React.memo(
     videoData,
+    requestSeek,
   }: VideoPlayerUIProps) => {
@@ -212,2 +214,3 @@ export const VideoPlayerUI = React.memo(
               handleShowControlsOnKeyEvent={handleShowControlsOnKeyEvent}
+              requestSeek={requestSeek}
             />
```

## Reading it

**`src/screens/PlayerScreen.tsx`** does the work. `useFlashGuard` takes the
player ref and where the map is, and gives back `covered`, `card`,
`requestSeek` and `seekEngine`. `CoverLayer` goes between the video surface and
the captions view, which is what keeps captions readable while the picture is
hidden. `CalmCard` goes above both. `SafeMediaControlHandler` is handed to the
player's media control focus, so a spoken "skip forward" goes through the same
seek function as the on-screen bar.

**`src/w3cmedia/mediacontrols/PlaybackControls.tsx`** and
**`src/components/Seekbar.tsx`** are the two places the sample moves the
playhead itself. Both now ask the guard instead. This is the part that varies
between apps: the rule is that no code writes `currentTime` or calls
`fastSeek` directly any more.

**`src/w3cmedia/mediacontrols/VideoPlayerUI.tsx`** only passes the function
down.

## What it does not do

The guard hides what a signed map says is over the published thresholds in the
video it plays. It does not analyse video on the device, it is not a medical
device, and a title with no map is a title that stays hidden.
