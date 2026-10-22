# User impact and differentiation

## A specific need, with a bounded claim

The intended audience is families where a child has photosensitive epilepsy, and developers preparing a small, approved library for those families. The Epilepsy Foundation describes flashing-light and visual-pattern triggers for some people with epilepsy. W3C defines general and red-flash thresholds in its web accessibility guidance. These primary sources support taking flashing seriously; neither establishes that this prototype prevents seizures, is comfortable for a particular person or has clinical efficacy. [Primary-source register](PRIMARY_SOURCES.md).

Calm Frames reduces exposure to flashing above published limits in the videos it plays; not a medical device. Its current playback scope is the compiled, approved library. It does not protect viewing in other apps, all streaming services or arbitrary unreviewed files.

## Intended benefit, implementation, evidence still needed

| Person or task | Intended benefit | What exists at `d96c088` | What has not been established |
|---|---|---|---|
| A household choosing a scene | Understand what will open and how it ends before choosing Watch. | Home/Details, explicit playback and ending behavior; existing native captures with their source labels. | Whether families find this understandable, desirable or comfortable. No interview or usability result is supplied. |
| A parent inspecting an edition | See the measured source, checked prepared output and selected identity without playing the original hazardous source. | Playback Proof and a remote-reachable analysis record. | Whether the explanation improves comprehension or trust calibration for real parents. |
| A developer preparing content | Inspect exact bytes, signed maps and refusal reasons; resume interrupted work without accepting damaged output. | Verification and exact-catalog gates; recorded recovery scenarios and guard mutations. | General resilience on other filesystems, power-loss survival, performance at scale and newer benchmark results. |
| A developer integrating Vega media | Reuse lessons on packaged URIs, first-frame readiness, focus and error reporting. | Code and historical issue receipts connected in the friction draft. | Vendor acceptance or resolution of SDK suggestions; broad portability. |

These are design hypotheses supported by implementation, not measured user outcomes. The [outreach record](evidence/outreach-status.md) contains no collected external feedback. Do not turn the earlier composite persona into a participant, quotation or customer.

## What distinguishes this implementation

The case is the combination: offline source analysis; prepared output that must pass verification; signatures and hashes tied to an exact edition; guarded native playback; and a readable Source/Prepared/Selection record. The [architecture](ARCHITECTURE.md) links these to code. Recovery adds an engineering property to preparation, not a new medical claim or new detector result.

This is a positive description of the project. It is not evidence that another analyzer, accessibility feature or player lacks those capabilities. No competitor study, exclusive-invention claim, market-share claim or “first of its kind” claim is made. The reusable analyzer and hook offer a possible developer path beyond the prototype; adoption and supported integrations have not been demonstrated here.

## A credible next validation step, still only a plan

After owner approval, ask consenting parents or accessibility practitioners to review the static wording and ordinary navigation, without hazardous clips. Check whether they can distinguish a prepared edition from its source, identify missing evidence and explain what the app does not cover. Record consent and withdrawals. Do not request or infer medical outcomes. A separate native review can examine device interaction, captions and audio. Neither activity happened in this package.

The immediate useful result is inspectability: a reviewer can trace an important statement to a file, source commit and limitation. That is demonstrated by this package. Demand, sustained use and health benefit remain unmeasured.
