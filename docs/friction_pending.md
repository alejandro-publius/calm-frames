# Friction working notes. This is not the friction log

**The friction log is [`docs/FRICTION_LOG.md`](FRICTION_LOG.md), and it is the only one to read or submit.** This file is the scratch pad the lanes write into while they are working, so that something found at 2am is written down before it is forgotten. Nothing here is final and nothing here should be quoted.

It used to hold eleven draft entries. Those drafts were the first eleven entries of the log, and they are now in the log in full, written better, so the drafts have been removed rather than left here to be read by mistake. The log holds 33 entries as of September 17 2026.

## How to add one

Write the six fields Amazon asks for: task, steps, expected versus actual, severity, workaround, suggestion. Real entries only, the way `CLAUDE.md` says. If it did not happen on this build, it does not go in, and if it is a platform rule we adopted rather than a failure we watched, say so in the entry itself. The log has three of those and each one is labelled.

Then move it into `docs/FRICTION_LOG.md`, give it the next number, add its row to the summary table at the top, and update the counts line under that table.

## Where the log's later entries came from

The first eleven were written here as they happened. The other twenty-two were not: the lanes hit them while working rather than while keeping notes, so each one was found again in a commit, a code comment, a results file or a decision entry. Here is where each came from, so nobody has to take the log on trust.

| # in the log | Where the evidence is |
|---|---|
| 12 device drops the app's logs | `app/src/calmframes/timingLog.ts` comment quoting the device's own suppression line, commit `b31a5d7` |
| 13 release builds strip `console.log` | `eval/vvd_smoke.py` docstring, CLAUDE.md, commit `f192962` |
| 14 no frame of what the app drew | `app/src/calmframes/uiCapture.ts` header, DECISIONS "stop trying to record the virtual device's screen", commit `c520e85` |
| 15 no crypto API | `app/src/calmframes/ed25519.ts` and `sha512.ts` headers, `canonicalJson.ts` for the third part, commit `c520e85` |
| 16 the build rewrites `manifest.toml` | `app/test/calmframes/manifest.test.ts` header, the 30 `[[needs.module]]` entries in `app/manifest.toml`, commits `3230b7e` and `9da186f` |
| 17 plain MP4 never starts | commit `b31a5d7`, and the root cause in docs/OPEN_SOURCE_PR.md |
| 18 a 200 instead of a 206 | `eval/vvd_timing_run.py` `send_head`, commit `b31a5d7` |
| 19 video-only stream pauses | `eval/marker_clip.py` comment on the silent track, commit `b31a5d7` |
| 20 listeners attached before the player existed | `app/src/calmframes/useCoverHarness.ts` `ready` flag and its comment, commit `b31a5d7` |
| 21 the device backgrounds an idle app | `eval/vvd_timing_run.py` keepalive, commit `b31a5d7` |
| 22 playback is not steady | GATES.md milestone notes, `results/vvd_layering_rehearsal.json`, `results/stick_day/gate1.json`, commits `0aaa9b6` and `46d8e2b` |
| 23 Shaka build needs a JDK | docs/ENVIRONMENT.md, CLAUDE.md, `.github/workflows/ci.yml` comment |
| 24 `jest --ci` exits 1 on a clean checkout | commit `e09c36f`, re-measured Sep 17 against a pristine upstream checkout |
| 25 208 gitleaks findings | commit `606d0c1` |
| 26 position reporting is undocumented | `results/vvd_timeupdate_stats.json`, `app/src/calmframes/timingLog.ts` and `mediaClock.ts`, GATES.md |
| 27 `setNativeProps` throws on 0.83 | docs/BUILD_PROMPT.md line 114, the three ESLint rules in `app/package.json`, `app/test/calmframes/dayOneGuards.test.ts`, commit `3230b7e`. A rule adopted, not a crash seen |
| 28 z-order and one captions view | docs/BUILD_PROMPT.md line 184, `app/src/calmframes/CoverLayer.tsx`, `app/src/screens/PlayerScreen.tsx`, `results/vvd_layering_rehearsal.json`. Also adopted rather than hit |
| 29 Theora empty packets | `flashmap/src/flashmap/decode.py` header, `flashmap/tests/test_theora.py`, commit `e654b74` |
| 30 Theora decodes wider than declared | `flashmap/src/flashmap/decode.py` around the declared size |
| 31 re-encode moves the rectangle | `flashmap/src/flashmap/analyze.py` `carried_picture`, `picture.py`, commit `d89b063` |
| 32 re-encode renumbers the first timestamp | `pipeline/verify.py` `compare_rendition_to_source`, docs/SIDECAR_SPEC.md, commit `4436eda` |
| 33 ffmpeg photosensitivity filter | `eval/baselines/run_all.py`, commit `daec5b7` |

Keep adding here as things happen. It is easier to write one down at the time than to find it again afterwards.
