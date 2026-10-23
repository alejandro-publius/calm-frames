# Mac acceptance checklist

For the branch tip of `claude/eager-goldberg-1s5eb4` (code at `12125b2970342b5376b0bc7964383e547b407376`). The
cloud session that wrote this has no Vega simulator, so everything below is
unobserved until someone runs it here. Keep the PIN, Kid, Kid 2 and every saved
position. No uninstall, reset, cleared storage or new PIN. Pause any capture
before a PIN screen.

## 1. Get the branch, beside the existing worktrees

```sh
TASK=/Users/alexvintera/Documents/Codex/2026-10-20/task
git -C "$TASK/calm-frames-combined-review" fetch origin claude/eager-goldberg-1s5eb4
git -C "$TASK/calm-frames-combined-review" worktree add --track \
  -b claude/eager-goldberg-1s5eb4 "$TASK/calm-frames-integration-2026-10-23" \
  origin/claude/eager-goldberg-1s5eb4
cd "$TASK/calm-frames-integration-2026-10-23" && git rev-parse HEAD
```

## 2. Hosted CI on that exact commit

The cloud session's GitHub app cannot start workflows, so start it here:

```sh
gh workflow run ci.yml --repo alejandro-publius/calm-frames --ref claude/eager-goldberg-1s5eb4
gh run list --repo alejandro-publius/calm-frames --branch claude/eager-goldberg-1s5eb4 --limit 1
gh run watch --repo alejandro-publius/calm-frames <run id>
```

Pass: every job green and the run's head SHA equals step 1's `git rev-parse HEAD`.

## 3. Build and install, package scoped

Node 22 (`eval "$(fnm env)" && fnm use`), `JAVA_HOME=/opt/homebrew/opt/openjdk@21`
for the Shaka player build, the existing Vega SDK (`source ~/vega/env`). A new
worktree has no built player, because its output is not in Git, so build it once.

```sh
cd app && npm ci --ignore-scripts && npm run setup:player && cd ..
# The new worktree has no .venv, and the system python3 (3.9) cannot run the script.
RELEASE_PYTHON="$TASK/calm-frames-combined-review/.venv/bin/python" \
  make release RELEASE_ARGS="--tag integration-2026-10-23"
shasum -a 256 build/release/integration-2026-10-23/calm-frames-0.1.0-aarch64-debug.vpkg
vega device is-connected --device VirtualDevice
vega device install-app --device VirtualDevice --buildType Debug \
  --packagePath build/release/integration-2026-10-23/calm-frames-0.1.0-aarch64-debug.vpkg
vega device run-cmd --device VirtualDevice --command 'vmsgr send pkg://io.github.alejandropublius.calmframes.main'
```

Record the package size and SHA-256 next to the commit before testing.

## 4. What to check, in this order

| # | Check | Pass looks like |
|---|---|---|
| 1 | Profile picker (fix `bde35e9`) | Opening it puts the ring on the active profile only. Choosing Kid 2 closes it once the save is done and the ring lands on the profile button. Back from the picker does the same. Focus is never lost |
| 2 | Labels (`2403d8f`, `9f8c612`) | The main button says Watch for Acadia, Sea otters, Forest and McWay. How it works ends with the approved sentence. On the paired coast cards, "Still scene" and "5 min" are readable and not cut off |
| 3 | Uninterrupted ambient playback | McWay plays its five minutes at natural speed with no stall, the final frame holds, Back returns Home with focus on the card that opened it, and the next Watch starts fresh |
| 4 | Stricter profile after recovery | In Parental controls (enter the PIN privately), set Kid 2 one preset stricter than Kid. Acadia's details for Kid 2 should show more covered time than for Kid. Start Acadia as Kid 2, press Back partway, reopen, Resume: the stricter cover plan still applies. Set it back afterwards through the same screen. If Everyone is already the strictest preset, note that and skip |
| 5 | Cover before seek | With the practice demo or Acadia, use Skip and a seek into a covered part while capturing the app window. The cover shows before the new position plays. If the capture cannot show the order, write down what it did show and decide whether the release accepts that gap |
| 6 | Onboarding footer | Only with an isolated first-run fixture that leaves the household alone. Otherwise leave it marked unobserved |
| 7 | One human watch and listen | The owner watches a minute of McWay with sound at a normal level, and says whether the pace, audio and colours are comfortable |

## 5. Rollback, if anything above fails

Install one of these packages the same package-scoped way, never by uninstalling:

- Nearest: `$TASK/calm-frames-combined-review/build/release/native-coastal-polish-20261023/calm-frames-0.1.0-aarch64-debug.vpkg`
  (source `bd55e47`, SHA-256 `4d229b6fd9c2a1ab61aa22eb996a673243da367db66035cb7f640bf70214e8a7`)
- Earlier: `$TASK/calm-frames-combined-review/build/release/native-onboarding-footer-20261023/calm-frames-0.1.0-aarch64-debug.vpkg`
  (source `4b04877`, SHA-256 `2bfac62fe2bd992186dd5d948a18b47dc5392f5e003c1cc49280be2476963101`)
- Submitted era: `$TASK/mac-readiness-2026-10-21/release-validation-2026-10-22/rollback/calm-frames-60c3bbb-aarch64-debug.vpkg`
  (SHA-256 `207898aa14d8659760348a716b825fabab83afd8e3b9431f9387202cc10e7163`)

## 6. A demo under three minutes, if the owner wants a new one

Same rules as the [October 22 run of show](../submission/REPLACEMENT_DEMO_RUN_OF_SHOW.md):
app window and app audio only, natural speed, no pause during playback, approved
titles only, a title card wherever time is cut, and never the Retry harness.

| Time | Picture |
|---|---|
| 0:00 to 0:12 | Home, the profile button, Who is watching, choose Kid, the ring returns to the button |
| 0:12 to 0:20 | McWay Falls details, then Watch |
| 0:20 to 1:30 | McWay plays uncut at natural speed |
| 1:30 to 1:45 | Back, reopen, "Resume at" and Resume |
| 1:45 to 2:25 | Acadia: Details, More info and the proof stages, Back to Home |
| 2:25 to 2:40 | Title card, then the last seconds of a full McWay take and its held final frame |
| 2:40 to 2:55 | Credits |

Publishing the cut or editing the Devpost entry needs the owner's word, before
12:00 PT on October 23.
