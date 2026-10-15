# Earlier positive-video evidence recovered

The historical checkpoint is `7110893`, with the Sept 17 summary in
`results/verify_pool.json` and source ledger in `media/LICENSES.csv`. The
current retained workspace at `/Users/alexvintera/calm-frames-work` reproduces
its catalog totals: 30 analyzed, seven cover-proven, 14 with no flagged
segments and nine failed. Three directories lack entries and one is pending.
These outcomes must not be collapsed into a claim that 21 titles proved
covering. They are historical pipeline outcomes, not current app inventory.

[The recovery receipt](../../results/earlier-positive-2026-10-15/inventory.json)
records the historical commit, ledger hash, exact paths, report hashes and
local presence. The normal project media folder retains all 35 media sources
listed with hashes. The ledger also includes an app chime, resolved from the
project root. Only the seven positive source files were freshly hashed in
this pass; all seven match. Other rows are existence/size inventory only.
No original source was displayed or opened in a player.

| Retained positive case | Source SHA prefix | Duration in historical entry |
|---|---|---|
| DVIDS illumination flares | `edace50b` | 73.5735 s |
| Jezioro Cisie panorama | `fafb7339` | 30 s |
| Rieti fireworks | `6dcfb11d` | 15.066516 s |
| Lightning blackout | `a139990f` | 15.02 s |
| Lightning at 240 fps | `cfc9677f` | 11.266 s |
| Irminger waves | `fdb4340e` | 8.708 s |
| DVIDS fireworks safety | `ce20d71c` | 87.3873 s |

## One additional reproducible case

Irminger waves was selected because its original bytes and all prepared
artifacts were already local, it is short, and its ledger records a public
domain source. That is a dated licence record, not a new legal clearance.
No sourcing, download, paid asset, account, credential or new key was needed.

[The headless recheck](../../results/earlier-positive-2026-10-15/recheck.json)
uses current analyzer source and the retained artifacts. Fresh WCAG analysis
returns exit 1, the expected positive result, and the same three segment
records as the historical map. It does not treat exit 1 as a pipeline failure
or suppress the findings. The source is never played.

Numeric full-resolution RGB decoding checks every covered frame against the
retained neutral still. WCAG and Extra cautious each cover all 261 decoded
frames; broadcast covers 105 of 261. All match the still exactly as decoded,
represented by the script's finite 999 sentinel for infinite PSNR, above the
existing 30 dB comparison floor. Source, rendition, map, plan, still and report
hashes are retained. This is a comparison with the stored cover plan, not
independent detector validation or new approval to distribute or play it.

Reproduce without writing to the old source or preparation workspace:

```sh
PYTHONPATH="$PWD/flashmap/src:$PWD" .venv/bin/python scripts/recheck_historical_positive.py \
  --media /Users/alexvintera/calm-frames/media \
  --work /Users/alexvintera/calm-frames-work \
  --out build/earlier-positive-recheck
```

Use the project's Python 3.12 environment with PyAV and NumPy. The script
writes JSON and text only, performs no player/capture/signing operation, and
changes no catalog or app trust. Historical signatures were not freshly
verified in this bounded recheck. No new bundle or native integration is
created. The installed app remains restricted to Harbor and approved Acadia.

## Separate Claude review

Claude's `3af32e47c569cc0c1d2a182c09c901487853e183` changes only a detector test
file and audit receipts. The [read-only assessment](../../results/earlier-positive-2026-10-15/claude-review-assessment.json)
records its paths, hashes and claimed runs. Exact working-pixel area boundaries,
red/general tally separation and temporal intervals are tested; mutation
controls are reported by Claude. No production detector or media artifact
changed. It was subsequently integrated under explicit follow-up authorization;
[the integration receipt](../../results/detector-review/integration.json) records
22 passing focused tests and unchanged installed app inputs. The read-only
assessment linked above remains the historical pre-integration record.

The review exposes limits rather than certifying the product: reduced working
resolution, display assumptions, unsupported exceptions, HDR and loop seams.
Its delayed end-of-playback return is supported by source code but not by the
current native driver, which presses Back before that delay. The audit is not
independent detector or clinical validation. Broadcast source text was not
re-fetched for that audit.
