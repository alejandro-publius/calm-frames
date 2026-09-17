# Gates, checkpoints and kill rules

Every gate result and every kill rule that fires is logged here with the date and evidence.

## Status board

| Item | Due | Status |
|---|---|---|
| HUMAN CHECKPOINT A: supported machine | Thu Sep 17 (kill if none by Sat Sep 19) | **Passed** Sep 17: macOS 15.1.1 on Apple M1 |
| HUMAN CHECKPOINT F: outreach emails drafted and sent | Fri Sep 18 | Blocked: `docs/outreach-kit.md` not provided yet |
| VVD plays the renamed sample | Sat Sep 19 | SDK installed Sep 17; app not built yet |
| HUMAN CHECKPOINT B: stick on Vega OS 1.2, developer mode, USB | Mon Sep 21 (SDK 0.23 fallback after) | Waiting on the stick |
| Layering test (1.5) | When the stick is ready | Not started |
| GATE 1: overlay timing, 48 of 50 covered 150 ms early (HUMAN CHECKPOINT E1) | Wed Sep 23 (Fri Sep 25 latest) | Not started |
| HUMAN CHECKPOINT C: self-filmed flashing footage | Thu Sep 24 | Waiting |
| GATE 2: 15 real flagged segments from 4 sources | Fri Sep 25 | Not started |
| HUMAN CHECKPOINT D: AWS Paid plan, $20 alarm, credits requested | Before the first deploy | Waiting |
| GATE 3: end to end on the stick | Fri Oct 2 | Not started |
| Upstream pull request opened | Mon Oct 12 | Not started |
| HUMAN CHECKPOINT E2: 200 screen-level events | Oct 8 to 13 | Not started |
| Outreach validation in docs/VALIDATION.md | Fri Oct 16 | Not started |
| Feature freeze | Sun Oct 18 | |
| Final checks | Wed Oct 21 | |
| HUMAN CHECKPOINT G: submit | Thu Oct 22 | |

## Log

### 2026-09-17: HUMAN CHECKPOINT A passed
Detected macOS 15.1.1 (24B91) on an Apple M1 (arm64) with 16 GB memory and 1.2 TiB free disk. Vega SDK 0.24 supports macOS on Apple silicon. Vega CLI 1.3.4 and SDK 0.24.9914 installed cleanly the same morning. Details in docs/ENVIRONMENT.md.
