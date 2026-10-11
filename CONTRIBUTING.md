# Contributing to Calm Frames

Thank you for looking. Calm Frames is an offline video analyzer, a checked
rendition pipeline and a Vega player for families affected by photosensitivity.
It reduces exposure to flashing above published limits in the videos it plays;
not a medical device. A few of its rules exist to keep people safe while they
work on it, and they come before everything else on this page. Read
[docs/SAFETY.md](docs/SAFETY.md) before you run anything.

The full rules are in [CLAUDE.md](CLAUDE.md), which every working session
follows. This page is the short version, with links to the long one.

**The project is in a feature freeze until the hackathon submission.** Changes
to presentation, documents, tooling and checks are welcome, and so is a fix for
a failing acceptance check. New app behaviour waits until after the judged
release.

## Set up

| You need | For | Notes |
|---|---|---|
| Python 3.12 | flashmap, the pipeline and the evaluation scripts | In a `.venv` at the repository root, which the `make` targets and the scripts look for |
| Node 22 | the Vega app's tests, lint and the hook | `.nvmrc` says 22. The `make` targets use fnm when it is installed and the `node` on PATH otherwise |
| ffmpeg and ffprobe | the pipeline, the conformance generator and every measurement script | The Python suite passes on both builds the README names; the published numbers came off the one in [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) |
| gitleaks | the pre-commit hook | `make hooks` installs the hook |
| The Vega SDK, the Vega CLI and JDK 21 | building the app and running it on the Vega Virtual Device only | The pinned versions and the install steps are in the README's [Install and run](README.md#install-and-run) |

The Python setup, with [uv](https://docs.astral.sh/uv/), from the repository
root:

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e "./flashmap[dev]"
uv pip install --python .venv/bin/python matplotlib    # the eval plot tests import it
```

`flashmap[dev]` brings pytest, hypothesis and pyyaml at pinned versions, and
`.github/workflows/ci.yml` pins the matplotlib CI installs. `make synth` also
needs `pipeline/infra/requirements.txt` in the same `.venv`.
For the app's tests, `cd app && npm ci --ignore-scripts` is enough: it skips
the Shaka Player build, which the tests mock. A device package needs the full
`npm install` with the JDK.

`app/CONTRIBUTING.md` is the guide that came with Amazon's sample app. It is
for contributions to that sample upstream, not to this repository.

## Run the checks

These are the commands CI runs, from the README's
[Run the checks](README.md#run-the-checks) block:

```sh
cd app && npm ci --ignore-scripts && npm run typecheck && npm run lint && npx jest --ci --colors=false && cd ..
.venv/bin/python -m pytest flashmap pipeline eval -q -m "not slow"
.venv/bin/python eval/readme_sync.py --check    # every published number against results/
.venv/bin/python eval/style_check.py            # no dashes, none of the three words
```

`make help` lists every target. `make ci` runs everything CI and the Audit
workflow run, in their order, and is the thing to run before you push. It
reaches the public advisory databases and the npm registry, so it is slow.

Three more that catch people out:

- If `app/package-lock.json` changed, run `make sbom` under the npm the hosted
  runner has (CLAUDE.md names it), because the app's bill of materials records
  the npm that wrote it and the Audit workflow compares bytes.
- If you change an engine file in `app/src/calmframes/` that the hook mirrors,
  run `node hook/tools/sync.mjs`; `app/test/calmframes/hookMirror.test.ts`
  fails while the two differ.
- If you change `media/LICENSES.csv`, run `.venv/bin/python eval/attribution.py`
  to rewrite NOTICE and the app's credits screen, which are generated from it;
  the eval tests fail while they differ.

## The rules, in short

Each of these is in CLAUDE.md in full. The first group overrides everything.

**Safety** ([docs/SAFETY.md](docs/SAFETY.md))

- Nobody watches strobes at full speed. A hazard file carries the `HAZARD_`
  prefix, lives under `media/` (which git ignores), never autoplays, and is
  inspected only as a plot (`eval/plots.py`) or as slowed, dimmed playback.
- Generated conformance clips are hazardous by design: generate, analyze and
  delete them in the same job, and never open one.
- Never play real flashing content with the filter off, for any test. Compute
  the exposure the filter prevented from the flash map instead.
- Never commit hazardous media. Only `media/LICENSES.csv` and hashes are
  committed.
- Use the approved wording, word for word: "reduces exposure to flashing above
  published limits in the videos it plays; not a medical device." Never
  "prevents seizures" and never "seizure-proof".

**Truth**

- Every published number comes from a file in `results/`, written as a marker,
  `<!--n results/file.json:key -->value<!--/n-->`, which
  `eval/readme_sync.py --check` holds to the file. Run `eval/readme_sync.py`
  without `--check` to rewrite them.
- When a number has a worse sibling, publish both, or say in the same sentence
  why the worse one is not the honest measure.
- Thresholds come only from
  [`flashmap/docs/SPEC_SOURCES.md`](flashmap/docs/SPEC_SOURCES.md), with the
  quoted spec text and link there first.
- Nothing mocked is shown as real. Label composites, sham maps and estimates.
- A new guard needs a test that has been seen to fail: break the guard on
  purpose, watch the test go red, restore it, and say in the commit message how
  it failed. A green new test proves nothing on its own.

**Engineering**

- Fail closed: a missing, stale, unsigned, unreadable or wrong-hash map keeps
  the picture hidden.
- Every way of moving the playhead goes through `requestSeek` in
  `app/src/calmframes/useFlashGuard.ts`, which covers before it seeks. A lint
  rule refuses `currentTime =` and `fastSeek(` anywhere else.
- Household and room settings can only add hides; nothing can make Calm Frames
  weaker than WCAG.
- No secrets in the repository. gitleaks runs in CI and in the pre-commit
  hook, and the map signing private key never enters the repository.
- The Vega app rules (no `setNativeProps`, playback only through
  `@amazon-devices/react-native-w3cmedia`, and the rest) are in CLAUDE.md.

**Style**

- No em dashes or en dashes anywhere: documents, interface text, code comments
  and commit messages. None of the three words CLAUDE.md lists under Style.
  `eval/style_check.py` checks the files, and `--staged` checks only what you
  are about to commit.
- Plain, warm writing. A commit message has a sentence-like subject and a body
  saying what changed and why.

## Adding a title

There are two kinds of title, and both start in the licence ledger.

**A clip for screening or evaluation.** Open its source page first and confirm
the licence and the credit line there. Then add a row to
[`media/LICENSES.csv`](media/LICENSES.csv) with the source URL, the licence, the
credit line, the SHA-256, the duration and the resolution, and the date you
checked. The file itself stays under `media/` and is never committed; if it
flashes, its name starts with `HAZARD_`. A few sources carry conditions of
their own (the Tears of Steel credit scroll, the Blender logos, the DVIDS
non-endorsement notice, NASA's credit line guidance), and CLAUDE.md lists them.
Anything marked to verify is verified or dropped. Then run
`eval/attribution.py` so NOTICE and the credits screen carry the new row. Do not
rebuild the labelling pool once a labelling sheet has an answer in it;
`eval/labeling/make_pool.py` refuses.

**A title for the app's library.** The app plays only titles compiled into its
packaged library, and a title reaches kid mode only after verify passes.
Prepare a benign clip with `python -m pipeline.local_library prepare`, export it
with `python -m pipeline.packaged_library export`, check it, and build the app
again. The README's
[A checked local library, without AWS](README.md#a-checked-local-library-without-aws)
has the commands, and
[`pipeline/LOCAL_LIBRARY.md`](pipeline/LOCAL_LIBRARY.md) has the details. A
title of our own gets a ledger row whose note starts "Ours.", which keeps it out
of the labelling pool. A new title means a new build, and so a fresh check on
the Vega Virtual Device.

## Reporting a security problem

Please do not open a public issue. Follow
[docs/SECURITY.md, "Reporting something"](docs/SECURITY.md#reporting-something):
until the repository is public, tell Alex directly; after that, open a private
security advisory on GitHub (the repository's Security tab, then Report a
vulnerability) rather than an issue. Do not attach media. A clip that shows a
problem with flash detection is a hazard file, and docs/SAFETY.md applies to it:
describe it, give its source page and SHA-256, and do not watch it to
reproduce the problem.

## Conduct

Everyone taking part is expected to follow the
[code of conduct](CODE_OF_CONDUCT.md).
