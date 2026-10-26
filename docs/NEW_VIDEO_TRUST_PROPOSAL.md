# Exact new-video trust proposal

Status: verified local package awaiting the separately promised owner approval. No TV trust, app source, installation or native playback change has occurred. This is a developer-assisted local import and packaging path; automatic TV delivery is not implemented.

## Proposed title

**Prairie Creek and Redwood (480p)**, the complete 50.5-second official NPS video, 854x480 H.264 at 30 fps, 1515 frames, AAC stereo. Credit: NPS: G Litten. [NPS source and usage statement](https://www.nps.gov/media/video/view.htm?id=F2E1744E-F295-B2E5-52AF33C2205A8C9E) identifies NPS-credited material without a copyright symbol as public domain. Its [park B-roll page](https://www.nps.gov/redw/learn/photosmultimedia/broll.htm) also permits reuse. No endorsement is implied. The owner authorized an official permitted sample when no personal intake selection existed.

The full file was downloaded and analyzed locally, never autoplayed or displayed. Its SHA-256 is `30137444a4f7cd8507a0c5d37fa7180e0b8b6215713d14f6d8c131a2f73b5494`. The [provenance record](../results/new-video-package-2026-10-18/480p-provenance.json) includes the exact official download URL and probe. This is a different source and title from the earlier Acadia fixture.

## Exact identities to approve

| Item | Exact value |
|---|---|
| Bundle | `568e563a99b3fd21acccdfce7aac061570681e8e31a1587b900616a19b692a32` |
| Catalog SHA-256 | `27fce9c0cf6400bf0f288d4891956d6948a39bd2135307fe9f5c54cfb0c5303a` |
| Public key fingerprint | `sha256:00c1bd272c4f3068626ddf6a828ae3f52ca32eae76dab35308d5d6687270b881` |
| Original verification report SHA-256 | `be91dad71e6835de997e9472c53adb49bcc37d9995afcb8e0e63b0cf2e064652` |
| Verification outcome | cover proven drawn, 51 of 51 checks passed |

The public fingerprint is SHA-256 of the raw 32-byte Ed25519 public key. One project-specific pair was created under the owner's explicit authorization, stored in `/Users/alexvintera/.local/share/calm-frames/signing/2026-10-18/`. The directory is 0700 and private file 0600, with restrictive creation permissions. No private material was printed, uploaded, committed or placed in the intake workspace. No external credential access was configured. [Public-only signer receipt](../results/new-video-package-2026-10-18/signer-public-receipt.json).

## What the viewer would experience

| Preset | Covered interval | Total covered time |
|---|---|---|
| Standard | 15.867 to 48.467 seconds |32.600 seconds |
| Broadcast |15.867 to 48.467 seconds |32.600 seconds |
| Extra cautious |15.367 to 48.967 seconds |33.600 seconds |

This covers roughly two-thirds of the clip. It demonstrates the full intake/preparation path but is a poor unobtrusive viewing sample. It must not be advertised as uninterrupted or medically safe. The detector reads the complete temporal file at 192px working width, with existing WCAG/broadcast rules and app-v1 room 85in at 4ft. Guard times remain 500ms for Standard/Broadcast and 1000ms for Extra cautious. No thresholds or trust rules were relaxed. Raw findings and padded intervals are in the [analysis review](../results/new-video-package-2026-10-18/480p-analysis-review.json).

## Delivery scope and size

The isolated final package is 23,098,484bytes. A separate copy of every existing bundled title plus the new bundle passes the app's JavaScript exact-byte/report gate at 51,579,411bytes, below 67,108,864bytes (64MiB). All five reports are present. This validates prospective asset delivery without changing production files or granting trust. [Combined delivery check](../results/new-video-package-2026-10-18/480p-delivery-gate.json).

The initially prepared 720p version also passed verification but would exceed the combined bound by 2,239,455bytes if added with all retained titles. It is retained only as a local verified artifact and is not the proposed TV bundle. The complete official 480p version resolves that bound without removing existing titles, cropping the video, or increasing limits.

## Concrete approval requested

Approve only the bundle, catalog hash and public key fingerprint above for inclusion alongside Acadia. After approval, the developer may copy its immutable bundle and original report into the app's prepared assets, compile the exact catalog text into a dedicated module, enforce its exact bundle/catalog/key identities in the runtime and pre/post build gates, and expose its verified title through the title selection flow. Keep the current titles and 64 MiB bound. New routes must still match title/source/rendition/map/preset identity; no route-supplied key, arbitrary catalog URL or blanket trust of later packages is proposed.

The subsequent source checks, one native build/install and bounded non-capture remote checks would verify Home/title selection to Details, playback, Back, and Parents cancellation. Those steps have not occurred. The existing app remains unchanged from installed source 3fab9998b0790c8345c2a3f82452e91a05ef4ba6; its previous verified resting state was Home Watch. Owner visual/audio approval remains separate from text logs. Guarded resume is still deferred until delivery is integrated.

## Evidence and local access

- Local review page: <http://127.0.0.1:8766/>. It now has the authorized local signer configured; it serves no original or prepared media.
- [Machine-readable exact proposal](../results/new-video-package-2026-10-18/proposal.json), [catalog](../results/new-video-package-2026-10-18/proposed-catalog.json), [original report](../results/new-video-package-2026-10-18/verification-report.json).
- [Negative checks](../results/new-video-package-2026-10-18/480p-package-negatives.json) refuse wrong source identity, altered media, an unsigned map after manifest rehashing, a wrong public key after rehashing, and a missing report. All mutations were in disposable copies; the original package still verifies.
- [Independent review](../results/new-video-package-2026-10-18/independent-review.md) verified the final package and report. The focused suite passed 42 tests, independently rerun. Local UI now shows verified public package identities and clears stale signer errors; JavaScript syntax and Ruff checks pass. No rendered-browser usability claim is made.

Exact local package directory:

`/Users/alexvintera/Documents/Codex/2026-10-15/task/intake-development/real-jobs/9a5fc47a866b4c60b548a9d88ac612b4/runs/7385ec182a6a4fa78bb75504e8839810/package`

Only public metadata, reports, provenance, code and test evidence enter the repository. Media stays local outside it. No push, publication, recording, new app trust, release tag, AWS change or edits to Claude's three reserved submission documents occurred. The only upload hiccup was the Python test client's single large socket send; bounded 64KiB sends worked without system changes.
