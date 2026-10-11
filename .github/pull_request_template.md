## What changed

<!-- One or two sentences a reviewer can check against the diff. -->

## Why

<!-- The problem it solves or the finding it answers. Link the issue, the DECISIONS.md entry or the review if there is one. -->

## How it was checked

<!-- The commands you ran and what they printed, for example `make ci`, or the lines from the README's "Run the checks" block. For a new or changed guard, say how its test was seen to fail: what you broke, which test went red, and that it went green again once restored. -->

## The rules

- [ ] No em dashes or en dashes, and none of the three words CLAUDE.md lists under Style; `.venv/bin/python eval/style_check.py` passes.
- [ ] Every number from a measurement is a marker into `results/`, and `.venv/bin/python eval/readme_sync.py --check` passes. Where a number has a worse sibling, both are published or the sentence says why not.
- [ ] A new guard has a test that has been seen to fail, and this description says how.
- [ ] No hazardous media in the change, nothing under `media/` but `media/LICENSES.csv` and hashes, and no flashing content was watched to make or check it.
- [ ] Any sentence about what Calm Frames does uses the approved wording: "reduces exposure to flashing above published limits in the videos it plays; not a medical device."
- [ ] Every seek still goes through `requestSeek` in `useFlashGuard.ts`, and a missing or bad map still keeps the picture hidden.
- [ ] No secrets, keys or account identifiers.
