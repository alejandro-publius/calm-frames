# Keep build tools out of native assets

Checked code: `95096125a9092aefca0571ee2b453229f6dc5f65`, based on the verified
Claude handoff `15ef46c6e23c8ba627492da23b1b147000031aa4`. This completes the
source-side packaging correction within items 12 and 19. A new native package
has not been built or installed in this cloud environment.

Claude's native inventory recorded developer scripts inside the installed
package's assets. The same files were present under `app/assets`, which the
native build copies. They now live outside that tree:

| Tool | New source location | Existing output retained |
|---|---|---|
| Logo generator | `app/tools/brand/make_logo.py` | `app/assets/brand/*.svg` |
| Brand renderer | `app/tools/brand/render.sh`, `render_qt.cpp` | Existing brand PNG and launcher-icon locations |
| Menu sound generator | `app/tools/sound/generate_menu_select.py` | `app/assets/raw/sound/menu-select.mp3` |

The generators resolve output paths independently of the caller's working
directory. The renderer still reads SVGs and fonts from their original asset
locations. Live commands, source references and existing lint paths were
updated; the recorded credit and media hashes remain intact.

## What prevents a recurrence

The existing prepared-library gate now checks the runtime asset tree before a
build and checks native archive member names after a build. Python, shell and
C/C++ build-source extensions are refused anywhere beneath `assets`, including
normalized aliases and case variants. Source-tree symlinks are refused. Runtime
catalog TypeScript remains valid and is still checked against its exact bytes.

This uses the gate already called by the app's prebuild/postbuild commands and
CI, so no workflow or dependency change is needed. The prior gate accepted a
synthetic archive containing `assets/brand/make_logo.py`; the new regression
was observed failing before the correction. Removing either the exclusion or
source-link refusal made its regression fail again. Both guards were restored.

The [check receipt](../../results/overnight-2026-10-25/packaging/receipt.json)
records commands, results and the inherited security-test failure described
below. The [asset inventory](../../results/overnight-2026-10-25/packaging/asset-preservation.json)
confirms unchanged SHA-256 for
<!--n results/overnight-2026-10-25/packaging/asset-preservation.json:file_count -->153<!--/n-->
runtime media, font, generated-artwork and metadata files. Generator tests
intercept file writes and the encoder; no artwork or audio was regenerated.

## Limits and integration note

Focused source/archive, generator-path, design, attribution and release-gate
checks pass. The selected-target release tests also pass under pinned Node
22.23.2. Qt rendering, a new Vega package and its installed inventory still
require the supported native toolchain. Existing native-package hashes remain
identities of the earlier package, which still contains the old build scripts.

Putting pinned Gitleaks on PATH exposed an inherited failure in
`test_secret_scan_manifest.py`: the current `PinKeypad.tsx` digest is not accepted
by the exact source-digest rule. Those two files are unchanged in this lane;
both planted-credential refusals pass. The issue is sent to the privacy lane
for a narrow correction, not waived. Staged scanning of this packaging change
passes. The full integrated run must retain the negative cases.

No dependency exceptions, application behavior, approved media, signing, trust,
household data or submission material changed. Nothing was pushed or published.

## Portability correction after review

A review reproduced a false rejection when a normal asset directory sat below
a linked parent, as with the system temporary-directory aliases on macOS. The
root check now inspects the root itself with `lstat`; parent aliases are allowed.
Directly linked asset roots, including a path with a trailing separator, and
linked descendants remain refused. No asset bytes changed.

The new ordinary-parent regression failed before the correction. The complete
package-gate suite then passed both normally and with `TMPDIR` pointing through
an owned directory alias. The [portability receipt](../../results/overnight-2026-10-25/packaging/portability.json)
records exact source hashes, commands and results. This reproduces the filesystem
condition in Linux; it does not claim a Mac or native-package build.
