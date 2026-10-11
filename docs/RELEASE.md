# Releasing

The current hackathon entry uses the Vega Virtual Device. Prepare an Apple
Silicon aarch64 Debug package by default. Other architectures, Release builds
and PyPI publication are separate choices, not simulator-demo prerequisites.
No final release or Devpost entry has been published.

## The app

```sh
make release RELEASE_ARGS="--tag review-polish"
make release RELEASE_ARGS="--tag review-polish-recheck --skip-build --receipt app/build/aarch64-debug/release-build-receipt.json"
```

The script builds the selected target, checks its prepared library and package
identity, then writes the package, `SHA256SUMS`, `PREPARATION.json` and `NOTES.md`
into a new `build/release/<tag>/` directory. Existing directories are preserved.
Use another tag for another preparation. The default package filename is
`calm-frames-<version>-aarch64-debug.vpkg`.

`--skip-build` requires a receipt with matching package and complete app input
hashes, including artwork, fonts, manifests, dependencies and generated runtime
files. Old native receipts without that inventory cannot establish a current
build. Rebuild instead. Preparation does not establish native execution.

Use repeatable `--arch` options to choose targets, `--build-type Release` for
Release packages, or `--all-architectures` when that broader scope is needed.
Release package names omit the `-debug` suffix. Release builds strip
`console.log`; measurement runs need Debug packages.

Follow [MAC_FINISH.md](MAC_FINISH.md) to install the exact prepared package,
check the native journeys and record a new demo. Fresh installs choose their
own household PIN. An optional `--pin` only describes an already configured
demo simulator in the notes; it does not embed a PIN in the package.

After package, recording, security and license review, request Alex's final
publication approval with concrete hashes, notes and the reviewed demo. Only
then run the printed `gh release create` command, which pins the prepared source
commit. If app inputs are uncommitted, the script withholds that command; commit
them and recheck the matching package receipt under a new tag. The script never publishes.
Once the judged release tag exists, it must not move.

## flashmap on PyPI

flashmap publishes with trusted publishing, so there is no API token to create,
store or rotate. PyPI accepts the upload because GitHub vouches for one workflow
in one repository.

The workflow is `.github/workflows/publish-flashmap.yml` and it is ready. It
cannot publish by accident: it only runs when someone starts it by hand from the
Actions tab and types `publish` in the box, and then the `pypi` environment
holds it for a review.

### Alex's steps, once

Only these three, and nothing else is waiting on them.

1. **A PyPI account.** Sign up at pypi.org and turn on two factor
   authentication. Trusted publishing will not work on an account without it.

2. **A pending publisher**, which is how a project that does not exist yet can
   still be claimed by a workflow. On pypi.org: your account menu > Publishing >
   "Add a new pending publisher", GitHub tab, then:

   | Field | Value |
   |---|---|
   | PyPI project name | `flashmap` |
   | Owner | `alejandro-publius` |
   | Repository name | `calm-frames` |
   | Workflow name | `publish-flashmap.yml` |
   | Environment name | `pypi` |

   Every field has to match exactly, including the environment name. The first
   successful publish turns the pending publisher into a real one and creates
   the project.

3. **The environment.** In this repository: Settings > Environments > New
   environment, called `pypi`. Add yourself under "Required reviewers". That is
   the second lock: even a run that someone started and confirmed waits for a
   click.

### Then, to publish

1. Actions > Publish flashmap to PyPI > Run workflow, leaving the box at
   `dry-run`. It builds the sdist and the wheel, runs `twine check --strict`,
   and prints the file names and hashes in the job summary. Nothing is uploaded.
2. Read that summary. The version comes from `flashmap/pyproject.toml` and PyPI
   will not let the same version be uploaded twice, so the version number is the
   one thing worth checking twice.
3. Run it again with `publish` in the box, and approve the environment.

### If it fails

- `invalid-publisher` means one of the five fields does not match. The error
  names what GitHub claimed; compare it with the pending publisher field by
  field.
- `File already exists` means that version is on PyPI already. Bump the version
  in `flashmap/pyproject.toml`. A released version cannot be replaced, only
  yanked.
- Nothing about either failure needs a token, because there is no token.

## What is not covered here

The Vega hook for npm, which the plan lists as "if time allows". Nothing is
prepared for it, and it needs an npm account with two factor authentication plus
its own trusted publishing setup.
