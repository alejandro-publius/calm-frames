# Releasing

> **Historical September procedure.** This file is not a published release or an accepted build. For the exact public October source and its matching build instructions, start with the [README](../README.md#start-here). No public downloadable release for the latest local repairs is verified.

Two things get released: the app, as three `.vpkg` files on a GitHub Release,
and flashmap, as a package on PyPI. Neither has been released yet.

## The app

    make release                             build all three, then stop
    make release RELEASE_ARGS="--skip-build" assemble from what is in app/build
    make release RELEASE_ARGS="--pin 1234"   put the demo PIN in the notes

`make release` builds armv7, aarch64 and x86_64, copies the release packages
into `build/release/<tag>/`, writes `SHA256SUMS` and `NOTES.md`, prints the
`gh release create` command it would run, and stops without running it.

It stops on purpose. Once the judged release tag exists it can never move, so
creating it is a person's decision, made after reading the notes.

To publish, when the time comes:

1. `make release` and read `build/release/<tag>/NOTES.md` end to end;
2. check the demo PIN is in there and is the PIN the app really uses;
3. run the `gh release create` line the script printed;
4. install from the release on a real stick before telling anyone about it:
   `vega run-app calm-frames-<version>-armv7.vpkg`.

What the notes carry: which file is for which device, the install steps, the
package id, the Vega OS version the packages declare, and how to check the
downloads against `SHA256SUMS`.

Two things that will bite otherwise:

- the packages are release builds, which strip `console.log`. Measurement runs
  need the debug build from `app/build/<arch>-debug/`.
- `make release` warns when `app/src` is newer than the packages. Do not
  publish through that warning.

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
