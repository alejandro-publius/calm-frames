# Calm Frames: code-verified architecture facts

Checked against source `612545932ea46f4547f594f58b2cf2b83f9134b3` on October 18, 2026. These are implementation facts for report writing, not an independent safety certification or a live cloud audit.

## Current local path

1. **Browser intake:** `pipeline/local_intake.html` is HTML, CSS and plain JavaScript connected to the Python backend in `pipeline/local_intake.py`. The backend uses the standard-library `ThreadingHTTPServer` on loopback, accepts MP4 uploads, exposes job status and runs explicit analysis, preparation, verification, export and delivery-review actions. It does not serve the uploaded original as a browser preview.
2. **Local persistence:** `IntakeStore` keeps an immutable original copy, `job.json` and per-attempt run directories in a private operator workspace. File/process locks, cancellation and a bounded worker deadline protect job execution. The local catalog is JSON (`local-library.json`), not a SQL database. Intake allows eight retained jobs and one active job. This version accepts at most 64 MiB, 60 seconds, 1280×720, constant 1 to 60 fps, 8-bit H.264/yuv420p with AAC audio. HDR, variable frame rate and embedded subtitles are refused.
3. **Analysis:** `review_analysis` invokes `FlashmapAdapter` and the `flashmap` CLI. PyAV decodes video; NumPy performs numeric image/timeline analysis. It runs WCAG and broadcast profiles over the complete timeline and checks source hash, decoded frame count and final timestamp. The local app plan uses the configured 85-inch/four-foot room geometry and derives three playback presets. This is numeric flash analysis, not an LLM or AI-vision service. Known detector limitations remain; no detector or threshold changed in this delivery pass.
4. **Preparation and proof:** the existing Python ingest/preparation and verification modules use FFmpeg/ffprobe, produce prepared MP4 renditions and verification reports, and sign map sidecars with Ed25519. Source, rendition and report identities remain distinct. A passing analysis or signature alone does not authorize TV membership.
5. **Export:** package-v1 manifests contain `version`, `assetRoot`, `bundleId`, `publicKeyBase64`, `titles` and `files`. The bundle ID hashes the canonical manifest body; the file inventory binds paths to SHA-256 digests. Title entries bind source and rendition identity, duration/offset metadata, three profile maps and report references. Original reports are content-addressed. Existing limits include 16 titles and 64 MiB combined delivery.
6. **Delivery review:** `pipeline/package_delivery.py` provides inspect/stage/check/cancel. It revalidates complete package bytes and original reports, then writes a revocable review receipt outside the package. Exact approval matches bundle ID, catalog SHA-256 and public-key fingerprint. Even `approved_for_build` has `can_watch: false` and `installed_by_staging: false`; staging cannot install or turn on Watch. New catalogs under a familiar signer still require exact approval.
7. **TV membership:** `app/config/approved-prepared-libraries.json` is reviewed build input. A Node generator creates `approvedPreparedCatalogs.ts` from those exact approved bytes. The strict build gate checks approved identities, file inventory, signatures, reports and packaged assets. The current consumer list contains only the existing Acadia approval. Prairie remains outside it.
8. **TV runtime:** TypeScript/TSX React Native for Vega renders `KidModeScreen`, Details, Parents and `PlayerScreen`. `packagedLibrary.ts` supplies consumer titles from compiled approved catalogs and matches complete routes before selecting an allowed key. `titleStatus.ts`, `verifyFlashMap` and `useFlashGuard` authenticate maps, bind metadata/source identity and control covers and guarded seeks. The native player opens packaged prepared MP4 files. Build-time byte verification must not be described as a runtime rehash of every MP4. `householdStorage.ts` uses AsyncStorage for household settings. No on-device arbitrary-file import was added.

## Versions and language boundaries

| Area | Verified version or declaration |
| --- | --- |
| Active local tools | Python 3.12.13; Node 22.23.2; FFmpeg/ffprobe 9.0.1; Vega SDK 0.24.9914 / CLI 1.3.4 |
| Analyzer package | `flashmap` 1.0.0; Python >=3.12; PyAV 18.1.0; NumPy 2.5.3; cryptography 50.0.1 |
| TV app declarations | React 19.2.0; React Native 0.83.0; TypeScript 5.8.3; Vega React Native package ~4.0.0+rn0.83.0; W3C media package ~2.3.2 |
| Verification tools | pytest 9.1.1; Hypothesis 6.168.0; Ruff 0.17.0; Jest ^29.7.0; ESLint ^8.57.1 |
| Main languages/formats | Python; TypeScript/TSX; JavaScript/MJS; HTML/CSS; JSON catalogs, maps and receipts |

Application package declarations are ranges where shown, not claims that every inherited sample dependency is used by Calm Frames. The manifest includes unrelated sample SDK integrations; their presence does not establish an active product feature.

## Optional/historical cloud infrastructure

`pipeline/infra/calm_frames_stack.py` contains AWS CDK infrastructure for private source/delivery S3 buckets, CloudFront origin access control, a DynamoDB catalog, ECR, an ARM64 ECS/Fargate ingest task and an S3-triggered Lambda. The stack explicitly omits Step Functions and EventBridge. It uses a VPC without NAT gateways and includes deployment/cost-control definitions. Repository documentation records an earlier deployment; current live AWS state was not inspected here.

The current local intake, staging and packaged-TV workflow does not require that cloud path. No AWS deployment, credential, signer, trust, network or cost configuration changed. No runtime LLM service is established by the inspected entrypoints. AI-assisted development should be described separately from the application's numeric analyzer.

## Evidence boundary

The integration passed 146 focused tests, TypeScript, focused ESLint/Ruff and the strict built-package gate. The accompanying integration handoff records the single native install and text-log smoke. Logs can establish selected package identity, dispatched routes, focus identifiers and player events. They do not establish pixels, audible quality, clinical safety, comprehensive detector accuracy or resolution of the previously observed simulator slowdown.
