# Calm Frames: TV visual refinement

Prepared October 10, 2026. This is a proposed visual direction, not a claim that the native app has been changed.

## Goal

Give Calm Frames the typography, composition, and remote-control clarity expected of a polished television app, while retaining its own monk, halo, deep teal, cream, and saffron identity. The interface should feel warm, composed, and carefully edited.

The companion `index.html` is an interactive visual reference. Its Harbor illustration is proposed artwork, not a captured frame from the existing story. It demonstrates hierarchy and interaction states; native playback remains in the real app.

The user has approved the visual concept and refined its copy direction. Follow `COPY_GUIDE.md`: familiar TV labels, natural sentences, and useful descriptions throughout the app. Keep design and implementation commentary outside the product interface.

## Evidence and scope

The September 20 cloud checkout has no explicit `fontFamily` or `lineHeight` in `app/src/calmframes`. Its shared theme defines sizes but no font faces. The old sample rotator alone references Amazon Ember. Equal bordered cards and a text-only title-details layout leave little visual hierarchy. These findings must be reconciled with the newer Mac branch before implementation.

The Mac task has since fixed focus behavior, built the aarch64 package, and made progress through actual simulator playback. Preserve that work. Apply these refinements to the current Mac checkout; do not replace it with the old cloud tree.

## Typography

1. Inspect the running Vega image and SDK-supported font configuration. Prefer Amazon Ember only if the actual family and required weights are supported and can be used under the relevant terms. A `fontFamily` string alone is not evidence that the intended face rendered.
2. Otherwise use a properly licensed, explicitly bundled family with confirmed native support. The reference uses Inter, bundled locally under the SIL Open Font License. Its browser WOFF2 file demonstrates the design; select a supported native format and configuration for Vega before integration.
3. Define shared family/face, size, line-height, and weight tokens. Apply them through a shared text component or named text styles, rather than scattering font overrides.
4. Use real regular, medium, and semibold faces. Avoid synthetic heavy text. Keep text in sentence case, and retain the current 32-unit floor for actionable and supporting TV text.
5. At a 1920 × 1080 design canvas, begin with the following roles and verify them on the simulator.

| Role | Size / line height | Weight | Use |
| --- | --- | --- | --- |
| Featured story | 80 / 92 | 600 | Harbor hero only |
| Screen title | 64 / 76 | 600 | Parent area and onboarding |
| Section | 42 / 54 | 600 | Library and settings groups |
| Card title | 38 / 48 | 500 | Titles beneath artwork |
| Body | 36 / 48 | 400 | Short readable explanations |
| Control | 36 / 46 | 600 | Actions and navigation |
| Supporting text | 32 / 42 | 400 or 500 | Metadata and helper text |

Keep line lengths short; reduce prose before shrinking type. Test long profile names, PIN errors, the longest title, caption text, and every empty/error state. Ensure text does not clip at the actual density.

## Visual language

Use a deep teal background (`#102F3A`), a subtle second teal (`#12343F`), restrained raised surfaces (`#1A414B`), warm cream text (`#F3E8D3`), and readable secondary text (`#BDD0CF`). Reserve saffron (`#E6A957`) for the primary action and visible focus. Use dark ink on saffron. Check all actual foreground/background pairs before accepting the theme.

Use 96-unit horizontal and 54-unit vertical safe margins. Align the header, hero, shelf, and action rows to one grid. Keep a compact spacing scale (12, 20, 32, 48, 64). Use modest 12 to 20 unit corner radii; avoid turning all content into pills or bordered boxes.

A resting control should be quiet. A focused control gets a stable, clearly visible six-unit outline and a second non-color cue such as an inset outline or focused treatment of the action. Reserve the geometry so focus never moves surrounding content. Verify contrast against both adjacent colors. Do not use bouncing, zooming, pulsing, autoplay previews, animated backgrounds, or animated screen fades.

## Screens

### Library

Use a small monk mark and readable wordmark in the header. Keep top navigation short. Give Harbor a large still illustration and distinct title, a single short description, a primary watch action, and a secondary details action. Put the actual available titles below in an aligned artwork-led shelf. A small real library should look intentional; do not fabricate movies, ratings, watch history, or progress to fill space.

Keep the active profile understandable without a large repeated heading. Preserve all existing profile selection, availability, and offline behavior. The halo is a selective brand motif, not an extra pattern on every surface.

### Title details

Pair the story artwork with a clear title and watch action. Separate the story description from the viewing-plan explanation. Show the relevant prepared plan, captions, and hold information in a compact, legible group. Put technical verification and diagnostic detail in the existing parent-facing locations where it helps a decision.

Keep the Harbor hold demo clearly identified as scheduled example holds in an originally nonflashing story. Do not imply that these are detected hazardous events or that verification guarantees safety. Preserve playback gates and data-derived claims.

### Parent area and onboarding

Use a stable page header and grouped settings rows with a clear primary label, short helper text, and selected-state indicator. Keep PIN entry calm and readable, including Delete, error, saving, and lockout states. Match the library's typography, spacing, focus language, and surfaces. Preserve the existing PIN gate and persistence behavior.

## Implementation order

1. Capture the current native library, title details, PIN entry, and parent settings with Vega in the foreground.
2. Verify the native font and add shared typography tokens.
3. Refine the library and details composition using the actual title assets and catalog.
4. Apply the same design system to controls, onboarding, parent settings, errors, and empty states.
5. Review actual native before/after captures and fix wrapping, optical alignment, clipping, and remote focus issues.
6. Run affected tests, type/lint checks, contrast/focus checks, and UI/image checks. Confirm that the image checks cover any new large artwork and surfaces; palette-only records do not prove actual screenshots are safe.
7. Rebuild the package, repeat the affected native journeys, and record the final demo only from that rebuilt package. Update its commit/package evidence and the completion checklist.

## Acceptance

- The intended font is visibly confirmed on native Vega, including required weights.
- The four core screens look like one product at 1080p and the simulator's actual scale.
- Header, story, body, metadata, and controls are distinguishable without excessive bold text.
- Artwork and spacing carry the visual identity; badges and borders do not overwhelm content.
- Every action works with the remote; focus survives returning from playback, details, and parent flows.
- Existing content filtering, playback checks, PIN behavior, captions, persistence, and reduced-motion behavior still work.
- Claims, availability, settings, and the demonstration remain truthful.

## Short prompt for the local Codex task

```text
Before final demo capture, implement a cohesive TV visual refinement on the current branch.
Use the attached Calm Frames TV reference and IMPLEMENTATION_BRIEF.md.
Verify the actual Vega font; use supported Amazon Ember if available, otherwise a properly licensed bundled font.
Create shared family, weight, size, and line-height tokens.
Refine Harbor artwork, library hierarchy, title details, onboarding, controls, and parent settings consistently.
Preserve the working remote behavior, playback gates, persistence, captions, and motion restrictions.
Show actual simulator before/after captures, run affected checks, then rebuild and record the final package.
Use Claude for an independent typography and UX review after implementation.
```

## Font source

Inter browser font: https://github.com/rsms/inter/blob/master/docs/font-files/InterVariable.woff2

License: `assets/Inter-LICENSE.txt`. The included asset was retrieved October 10, 2026. No Amazon font is redistributed by this reference.
