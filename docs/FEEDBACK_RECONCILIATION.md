# Feedback and judge-access reconciliation

Repository draft, checked October 26, 2026. This is not a submitted Devpost answer.
The locked form could not be read, so coverage in the actual submission remains
unverified. This review reuses existing records; it adds no new product test or
personal experience.

## Existing coverage

The September feedback and friction files on main have the requested field
structure but are stale. Use these pinned public October records for review:

- [Product feedback](https://github.com/alejandro-publius/calm-frames/blob/37d10c2db57fc0868499adc133cff7560600d5cc/docs/FEEDBACK.md): every numbered tool section
  includes purpose, successes, shortcomings, onboarding and a reuse decision.
  It covers Vega SDK/CLI, the simulator, video sample, player, media controls,
  captions, accessibility, Kepler UI/focus/filesystem, GitHub Actions and the AWS
  services actually discussed in the deployment record.
- [Friction log](https://github.com/alejandro-publius/calm-frames/blob/37d10c2db57fc0868499adc133cff7560600d5cc/docs/FRICTION_LOG.md): every numbered entry includes
  task, steps, expected and actual behavior, severity, workaround and suggestion.
  Some later dated notes use abbreviated prose and need the same fields if copied
  into individual form entries.

Those numbered sections do not need a wholesale rewrite. Their scope does need
review: September statements that no AWS deployment occurred or no native picture
could be captured were superseded in the October records. Conversely, an old
successful journey or CI run does not prove the latest native repairs or today's
audit status. Reuse decisions are the recorded author's judgments and need owner
confirmation before being presented as current personal answers.

## Draft normalization of dated friction notes

These drafts preserve the observations in the linked October log. They are not
newly reproduced results.

| Field | Watchman access during local tests | Replaced media retained during packaging |
|---|---|---|
| Task | Run final UI source checks. | Package the approved Acadia replacement. |
| Steps | Invoke the local Jest checks; inspect the permission failure; rerun with the documented `--watchman=false` workaround. | Replace the prepared-media bundle, build, then inspect the mandatory package-budget rejection and staged asset tree. |
| Expected | Tests operate within the workspace. | The package contains only the checked source media set. |
| Actual | Watchman tried to change its state permissions outside the writable workspace; tests did not start. | Incremental staging retained the removed bundle and report; the package gate rejected the archive before installation. |
| Severity | That test invocation was blocked. | Build blocked; no installation occurred. |
| Workaround | Use the existing Node/Jest setup with `--watchman=false`; no permission or software change. | Preserve the stale generated media namespace outside the source tree, then rebuild it from checked source assets with the same gates. |
| Actionable suggestion | Document a workspace-bounded CI-style test invocation. | Synchronize removed raw assets during incremental packaging, or document the generated-staging refresh procedure. |

Owner confirmation needed: whether these incidents and their recorded reuse
opinions belong in the final feedback; whether any additional tool was used after
the pinned record; and which answers were actually submitted. Unreported tools
must not be given invented onboarding experiences or favorable opinions.

## Judge source access

The [README](../README.md#start-here) identifies the public snapshot and earlier
demo. To inspect exactly that source in a new checkout:

```sh
git clone https://github.com/alejandro-publius/calm-frames.git calm-frames-review
cd calm-frames-review
git checkout --detach 37d10c2db57fc0868499adc133cff7560600d5cc
```

Then read that checkout's `docs/RELEASE.md` and the warnings in its referenced
handoff documents before preparing a package. Those instructions include a
required SDK/toolchain and original media verification inputs. Older linked
handoffs may themselves be marked superseded: do not advance this pinned
checkout to a different branch merely because a historical procedure says to.
A fresh public clone-to-native-build was not exercised in this documentation
pass, so self-contained runnable access is not certified. No downloadable public
release is available for the latest local repairs. A judge-ready package needs a
separate, exact-source build and media-input availability check, with its hash
and acceptance scope recorded. Do not substitute local-only files or bypass a
missing-input gate.
