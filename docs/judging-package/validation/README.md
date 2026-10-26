# Package validation and factual audit

These checks cover this documentation package. They do not rebuild the application, reproduce native issues, measure a benchmark or establish medical safety or full accessibility conformance.

## Browser checks

[Machine-readable results](checks.json) record the tested browser, viewport widths, link and image checks, computed contrast, keyboard behavior, visible focus, reduced-motion behavior and absence of remote requests or browser errors. A no-JavaScript check confirms that every tour stop remains visible. Native screenshot pixels are historical evidence, not authored web text; they are excluded from the guide's contrast measurement.

The managed cloud browser blocks direct `file:` navigation. The test serves only this package directory on a temporary loopback server, checks the guide, and closes that server. It does not verify current external websites. The guide itself has no network-backed runtime or installation step; opening the files directly remains a Mac acceptance check.

The [desktop](desktop.png), [narrow](narrow.png) and [keyboard-focus](keyboard-focus.png) images are **renders of the web guide**, not native app captures. Desktop and narrow layouts were visually inspected for hierarchy, readable spacing and clipping. The first-screen narrow render is also available [at viewport size](narrow-first-screen.png).

## Factual and privacy review

- The selected release fields and original receipt SHA-256 were checked against `results/release-validation-2026-10-22/validation.json` at `13551e4`. Local historical results retain their skips, deselections and limitations. These are not newly run tests.
- Every asset in [the inventory](../assets.json) matches the original bytes in the pinned Git snapshot. Native images remain unchanged; the diagram is labelled as documentation.
- The submitted `bf2f615` and historical capture source `60c3bbb` have identical `app` and `hook` Git trees. Integration captures are tied to `d96c088`, not silently substituted for that earlier gallery.
- Every bundled code excerpt and its full-source SHA matches the stated file and line interval. Optional pinned source links name files present in the snapshot.
- The [claims ledger](../CLAIMS_LEDGER.md) was reviewed against those sources and the recorded limitations. No interviews, adoption, medical outcome, current hosted CI success, competition score or newer Claude benchmark is inferred.
- Text was reviewed for private host paths, credentials, tokens and account identifiers. None were found by the targeted pattern scan and review. The selected release JSON omits original runtime paths, device/account metadata and raw logs. This is a scoped audit, not proof that every possible secret format can be detected.
- The product-feedback update was independently reviewed for attribution and evidence. It supplements the original per-tool inventory and does not attribute Mac capture or cloud browser policy to Amazon.

The [source-access receipt](../evidence/source-access.json) records the unresolved live Devpost, W3C and Epilepsy Foundation access gap. Historical excerpts do not constitute a fresh verification. The [Mac handoff](../HANDOFF.md) lists the remaining owner/native/video checks.

## Reproduce after documentation changes

Use already available Node, `marked`, Playwright and Chromium for authoring checks. The reader does not need these tools. Do not install or build the app to inspect the package.

```sh
node docs/judging-package/render_reading.cjs
node docs/judging-package/validation/check-guide.cjs
python3 eval/readme_sync.py --check
python3 eval/style_check.py --staged
git diff --cached --check -- docs/judging-package \
  ':!docs/judging-package/assets/LICENSE-Fraunces' \
  ':!docs/judging-package/assets/LICENSE-SourceSans3'
```

The two font notices retain their exact upstream bytes, including an existing trailing space on line 21 of each file. An unrestricted whitespace check reports those two lines. The scoped command excludes only those unchanged notices; authored files pass. Asset hashes verify that the notices have not been rewritten.

The browser script defaults to `/usr/bin/chromium`; `CHROMIUM_PATH` can name an existing local browser. Review any changed source claims separately: a passing link check cannot establish their truth.
