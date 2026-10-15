# Watch first, October 15, 2026

The owner rejected the report-like viewing screens after inspecting the running
app. This pass changes presentation and navigation only. The prepared media,
catalogs, public keys, detector, maps, cover schedule and player are unchanged.

## Exact copy changes

| Location | Before | After |
| --- | --- | --- |
| Home main action | View analysis | Watch, first and focused on launch |
| Home second action | Play | Details |
| Home runtime | 20 sec · Prepared video | 20 sec |
| Harbor runtime | 20 sec · No flashing found | 20 sec |
| Details large card | No scenes flagged | Removed |
| Details large card | Analyzed before playback · Extra cautious | Removed from viewing page |
| Details large card | This prepared video has no scheduled hidden scenes. | Removed |
| Details main action | Play | Watch |
| Details second action | Try the demo | More info |
| Details supporting line | The video plays normally. | Removed |
| Details lower action | Analysis and settings ↓ | Removed; More info opens its own page |
| Details report | Analysis record | Only under More info > Technical details |
| Acadia description | NPS Video, Acadia National Park. No NPS endorsement is implied. The artwork is decorative, not a video frame. | Waves along the coast of Acadia National Park. |
| Demo runtime | Practice version · 20 sec · 2 picture pauses | Simulated demo · 20 sec |
| Demo description | The picture pauses twice while sound and captions continue. This demo contains no flashing. | A simulated demonstration with two picture pauses. No flashing. |
| Demo action | Play demo | Watch demo |
| Identity-mismatch error | Analysis record unavailable | This video is unavailable |
| Identity-mismatch explanation | This video does not match the prepared library in this build. The picture stays hidden. | This version cannot play in Calm Frames. The picture stays hidden. |

## Remaining everyday text

Home: Calm Frames; the saved profile name; How it works; Parents; Choose a video;
Harbor; 20 sec; Watch; Details; More to watch; Acadia coastal scenery;
National Park Service. Other title and empty/offline states still reflect their
actual availability. Errors have not been converted into successful results.

Harbor Details: Back; Harbor; 20 sec; Watch; More info. No description is added.
Acadia Details: Back; Acadia coastal scenery; 38 sec; Waves along the coast of
Acadia National Park.; Watch; More info. Runtime is rounded from the catalog.

Demo Details: Back; Harbor; Simulated demo · 20 sec; A simulated demonstration
with two picture pauses. No flashing.; Watch demo; More info.

More info: Back; More info; the title name; the following feature explanation;
Detection can miss flashing; the unchanged approved safety sentence; Watch demo
where offered; Technical details; Back. It contains no IDs or results table.

Feature explanation: "Calm Frames replaces flashing scenes with a still picture
while sound and captions continue. It only works with videos in this app."

Acadia also says: "A still picture replaces brief parts of this video. Sound and
captions continue." Its attribution is here: "Video: National Park Service,
Acadia National Park. Public domain. No NPS endorsement is implied. The artwork
is an illustration."

The demo's More info also says: "This is a simulated demonstration. The pauses
were added to show how the feature works, not because flashing was detected."

How it works: "Calm Frames replaces flashing scenes with a still picture. Sound
and captions continue." Then: "Videos are checked before they are added. This
only works with videos in Calm Frames, not other apps or live TV." Then: "The
demo has two simulated picture pauses and no flashing." Actions: Watch demo;
About the demo; Check playback; Back. The detection limitation and unchanged
approved safety sentence remain visible here.

Technical details retains the source/rendition/report identifiers, analysis
resolution and findings, limitations and viewing settings. It has its own plain
background. There is no zero-change timeline, even here. A nonempty timeline is
in normal layout flow beneath its summary, separate from the viewing hero.
The viewing title and controls have an opaque ivory reading area, so decorative
art cannot show through their text. Fraunces, Source Sans 3, coastal artwork,
colors and controls are retained. No new screenshot was taken, so actual visual
quality remains an owner observation rather than a test claim.

## Remote route

Home Watch opens playback; Back returns focus to Watch. Home Details opens a
brief viewing page with Watch focused. More info replaces that page, so its
hidden controls cannot receive focus. Technical details opens one level deeper.
Back returns to Technical details, then More info, then Home Details, restoring
the control that opened each step. More info > Watch demo opens the explicitly
simulated demo page. Playback Back returns to that page, then Back returns to
More info with Watch demo focused. Parents cancellation still returns to Parents.

The existing storage, first-run, Parents and playback warning/error text was
reviewed. Those surfaces retain meaningful settings, setup instructions and
failure reasons. Playback transport retains conventional Play/Pause semantics.
