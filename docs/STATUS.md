# Status

Updated Thu Sep 17, 2026, morning PT.

## Done
- **0.1 Machine check:** macOS 15.1.1 on Apple M1, 16 GB, 1.2 TiB free. Supported by Vega SDK 0.24. HUMAN CHECKPOINT A passed.
- **0.2 Installs:** Vega CLI 1.3.4 and SDK 0.24.9914 (latest), Node 22.23.2 through fnm, Python 3.12.13 venv through uv, watchman, gitleaks 8.30.1. All versions in docs/ENVIRONMENT.md.
- **0.3 Repo:** `~/calm-frames` created, local only (no GitHub remote yet).
- **0.5 License:** Apache-2.0 LICENSE (canonical text) and NOTICE.
- **0.8 Name check:** "Calm Frames" is free on GitHub, Devpost and the web; `flashmap` and `calm-frames` are free on PyPI.
- **Rules check against Devpost (Sep 17):** deadline Oct 23 12:00 PT, judging Nov 9 to 20, winners around Dec 3. Four equally weighted criteria; ties are broken by the first criterion, Tech Implementation. Both AWS credit form links open the same form ($150, closes Oct 21 12:00 PT). Devpost posted a Sep 16 update on the code repository requirement: public with an open-source license at the top, or private and shared with testing@devpost.com and @AmazonAppDev.
- **Docs:** BUILD_PROMPT, CLAUDE.md, ENVIRONMENT, DECISIONS, GATES, SAFETY, PRIOR_WORK, `media/LICENSES.csv` header, 5 friction entries waiting for evkit.

## Paused
- **Lane 4, IRIS baseline image:** Dockerfile, staged vcpkg scripts, Make snippet and README are committed with verified pins, but the image has never finished building. The first attempt ended when its agent stalled. The build waits until the shared colima VM is idle (it now runs another project's DataHub stack with 3.2 GB free) or until CI can build it. It has to finish by about Sep 30.

## Next
1. 1.2: copy vega-video-sample `v0.24-RN83` into `app/` as one untouched commit, then the day-one fixes (package ID, remove tasks and services, setNativeProps lint rule, back-navigation regression test).
2. 1.3: `npm install`, build, start the VVD, play a Blender title. Log every snag.
3. When the kits arrive: 0.4 install and run their tests (97, 51, 120 expected), 0.6 CI from evkit templates, 0.7 move friction entries into evkit, 0.9 outreach drafts.
4. Create the GitHub repo once CI is ready.

## Blocked
- **0.4 kits, 0.6 CI, 0.7 friction tooling:** `day-one-head-start.zip` is not on this Mac, Google Drive or claude.ai artifacts.
- **0.9 outreach drafts (due Fri Sep 18):** `outreach-kit.md` is missing.
- **docs/RUBRIC.md:** `rubric-amazon.md` is missing.

## What I need from you
1. Put `day-one-head-start.zip`, `rubric-amazon.md` and `outreach-kit.md` in `~/calm-frames/headstart/` (or anywhere, and tell me the path).
2. Today's steps: order the stick (Fire TV Stick 4K Select AFTCA002, or Fire TV Stick HD 2026 AFTCL001), join the hackathon on Devpost, sign in to an Amazon Developer account, request AWS credits, move AWS to the Paid plan with a $20 budget alarm, and check 240 fps filming and TV game mode.
