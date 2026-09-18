# Flash map sidecar, version 1

This is the contract between flashmap and everything that reads its output: the Vega app, the
pipeline, the verifier and the GitHub Action. It is a JSON object in one file, written next to
the video it describes.

Producer: `python -m flashmap analyze VIDEO --out MAP.json --key team_key.pem`.
Reader of last resort: `python -m flashmap verify MAP.json VIDEO --pub team_key.pub.pem`.

Thresholds are not defined here. They live in `flashmap/docs/SPEC_SOURCES.md` with the quoted
spec text they came from, and the map repeats the ones it used so a reader never has to guess.

## The rules a reader must follow

1. **Fail closed.** A map that is missing, unparseable, the wrong version, unsigned, signed by
   a key you do not hold, or bound to a different file is not a map. Keep the picture hidden.
2. **Check the binding.** `source.sha256` is the SHA-256 of the video file the map describes.
   Hash the file you are about to play and compare. A map that verifies against a different
   file tells you nothing about this one.
3. **Check the signature against a key you already hold.** The map carries a copy of the public
   key so it can be self checked, but a self check only proves the map is internally consistent.
   Trust comes from the key you shipped, not from the key in the file.
4. **Hide `[start_ms, end_ms]`, not `[flash_first_ms, flash_last_ms]`.** The first pair is the
   interval to cover. The second is the tight span of the offending flashes and is there for
   people reading the map, not for the player.
5. **A reader may hide more. It may never hide less.** Room settings, guard bands and the
   pre-covered rendition are all allowed to add. Nothing is allowed to subtract.
6. **Unknown fields are ignored, not rejected.** Version 1 may grow new optional keys. A reader
   that fails on an unknown key will break on the next minor release.

## Versioning

`version` is an integer. This document describes `version: 1`. A reader must refuse any other
value rather than guess. New optional keys can appear inside version 1. Anything that changes
the meaning of an existing key, removes a key, or changes how segments are computed gets a new
version number.

`schema` is a stable identifier string for this document. It is not fetched at runtime.

## Top level

| Key | Type | Notes |
| --- | --- | --- |
| `schema` | string | `https://calm-frames.github.io/schemas/flashmap-map-v1.json` |
| `version` | integer | `1` |
| `generator` | object | `{"name": "flashmap", "version": "1.0.0"}` |
| `created_utc` | string | RFC 3339 in UTC, seconds precision, for example `2026-09-17T22:00:00Z` |
| `source` | object | which file this map is for, see below |
| `picture` | object | where the picture is inside the coded frame, see below |
| `color` | object | how the file was decoded, see below |
| `profile` | object | the rules that were applied, see below |
| `segments` | array | the intervals to hide, see below |
| `summary` | object | counts, for reports |
| `signature` | object or absent | see below |

## `source`

| Key | Type | Notes |
| --- | --- | --- |
| `path` | string | the file's base name only, never a full path |
| `sha256` | string | 64 lowercase hex characters, of the whole file. **This is the binding.** |
| `size_bytes` | integer | |
| `coded_width`, `coded_height` | integer | the frame size the file declares, bars included. Some decoders hand back a frame a few columns wider, because the codec pads to its block size; the size here is the one the file says and the one a re-encode of it gets made at. |
| `container_frame_rate` | string or null | `"30000/1001"` style. Informational. flashmap never uses it for timing and neither should you. |
| `duration_ms` | number or null | from the container, may be absent |
| `frame_count` | integer | frames actually analysed |
| `first_pts_ms`, `last_pts_ms` | number or null | real presentation timestamps of the first and last analysed frame |
| `last_coded_pts_ms` | number or null | the timestamp of the last frame that carried a picture of its own. It sits before `last_pts_ms` when the file ends on repeated frames, which is what an empty packet means in Ogg Theora. Anything that re-encodes the file drops those repeats and ends early, so a tool building a rendition holds the last picture for the difference. |
| `variable_frame_rate` | boolean | true when the measured frame intervals are not all the same |
| `frame_interval_ms` | object | `min`, `max`, `median` of the measured intervals |
| `timestamp_source` | string | `container-pts` in version 1 |

## `picture`

Area fractions are measured on the picture, not on the coded frame. Letterbox and pillarbox bars
are found and removed first, because counting them would make every area fraction look smaller
than it is.

| Key | Type | Notes |
| --- | --- | --- |
| `measured_on` | string | always `"picture"` in version 1 |
| `left`, `top`, `width`, `height` | integer | the picture rectangle, in analysis pixels |
| `frame_width`, `frame_height` | integer | the analysis frame the rectangle sits in |
| `letterbox`, `pillarbox` | boolean | whether bars were found on that axis |
| `coded` | object | the same rectangle in the file's own coded pixels, `{left, top, width, height}`. **This is the one to carry.** |
| `source` | string | `detected` or `carried`, see below |
| `detected` | object or absent | present only when `source` is `carried`, see below |
| `note` | string | plain language restatement of the above, for humans |

To map the analysis pixel rectangle back to the source frame, scale by
`source.coded_width / picture.frame_width`. `picture.coded` is that already done, and it is
what a reader should use, because the analysis width is a setting and the coded frame is the
file.

### Carrying the rectangle across a re-encode

**Always analyze the source file. Never analyze a re-encode and call the answer the title's
map.** Re-encoding nudges the outermost rows and columns. One row of picture crushed dark
enough to read as a letterbox bar is enough to shrink the rectangle, and because every area
fraction is measured against the rectangle, a smaller rectangle lifts every fraction. A real
title was blocked this way: a rendition whose picture was detected as 192 by 106 analysis
pixels where the source was 192 by 108, which lifted spans over the 25 percent line that the
source never broke.

So a re-encode is measured on the rectangle from the source's map, not on one found in the
re-encode:

```
python -m flashmap analyze RENDITION.mp4 --profile wcag --out CHECK.json \
    --picture-from SOURCE_MAP.json
```

The rectangle is read from `picture.coded` of that map, and it is refused outright if the
coded frame size it came from is not the coded frame size of the file being measured. A
rectangle from a different frame size does not describe this file.

| `picture.source` | Meaning |
| --- | --- |
| `detected` | the detector found this rectangle in this file. Every map of a source file says this. |
| `carried` | the rectangle came from another file's map, because this file is a re-encode of that one |

When `source` is `carried`, `picture.detected` holds what this file's own detector found, as
`left`, `top`, `width`, `height`, `letterbox`, `pillarbox` and `coded`. It is there so the two
can be compared without analysing the file again, and it is reporting only: nothing was
measured on it.

`pipeline/verify.py` uses this. It measures the kid safe rendition on the source's rectangle,
and it separately refuses to publish a title whose rendition does not have the source's coded
frame size, the source's picture rectangle, the source's frame count, a span that has not
stretched by as much as half a frame and a start that has not moved by as much as a whole
frame. The start is judged more loosely because a re-encode routinely renumbers the first
presentation timestamp to zero while leaving every picture where it was.

### Why this is still version 1

`picture.coded`, `picture.source`, `picture.detected` and `source.last_coded_pts_ms` are new
optional keys. They do not change the meaning of any
key that was already here, none is removed, and nothing about how segments are computed has
changed for a file measured the ordinary way. The versioning rule above allows exactly that
inside version 1, and a reader that ignores all three still reads every map correctly. A map
with `picture.source` set to `carried` is the one case where the rectangle is not this file's
own, and a reader that cares has the field to look at.

## `color`

| Key | Type | Notes |
| --- | --- | --- |
| `matrix` | string | `bt709`, `bt601`, `fcc`, `smpte240m`, `bt2020ncl` or `rgb` |
| `matrix_source` | string | `stream-tag`, `inferred-hd-bt709`, `inferred-sd-bt601` or `rgb-stream-no-matrix`. Anything starting with `inferred` means the file did not say and flashmap guessed. |
| `range` | string | `limited` or `full` |
| `range_source` | string | `stream-tag`, `pixel-format-yuvj` or `default-limited` |
| `pixel_format` | string | the decoder's pixel format name |
| `transfer_tag` | string | the raw libavutil transfer characteristic value |
| `luminance_model` | string | `wcag-relative-luminance-srgb` in version 1 |
| `analysis_width`, `analysis_height` | integer | the working size frames were scaled to |

## `profile`

Everything the rules did, written out. The threshold numbers are repeated here so a reader can
see what was applied without opening the source.

| Key | Type | Notes |
| --- | --- | --- |
| `name` | string | `wcag` or `broadcast` |
| `title` | string | the human name of the rule set |
| `flash_limit_per_second` | integer | `3` |
| `window_ms` | integer | `1000` |
| `area_fraction_limit` | number | `0.25` |
| `area_window_mode` | string | `ten-degree-field` or `whole-picture` |
| `peak_nits` | number or null | only for the broadcast profile |
| `general_flash` | object | `metric`, `min_delta`, `dark_image_below`, `source` |
| `red_flash` | object | `saturated_red_ratio`, `min_ucs_distance`, `source` |
| `area_windows` | array | every window the area was measured in, see below |
| `room` | object or null | the household setting, see below |
| `transition_pairing` | string | how transitions were paired into flashes |
| `transition_rule` | string | when a transition was declared |
| `window_placement` | string | where the one-second window was placed |
| `red_opposing_rule` | string | what "opposing" means for a colour transition |
| `rules_not_implemented` | array of string | parts of the spec this build does not apply |
| `exceptions_not_implemented` | array of string | exceptions that would have let content pass and were not applied |
| `spec_sources` | string | where the quoted spec text lives |

The four `*_rule` and `*_pairing` strings exist because the specs leave those points open. They
are recorded so two maps made by different builds can be compared fairly.

### `profile.area_windows[]`

| Key | Type | Notes |
| --- | --- | --- |
| `name` | string | `wcag-10deg`, `bt1702-screen` or `room-10deg` |
| `width_px`, `height_px` | integer | the window size in analysis pixels, on the picture |
| `source` | string | where the size came from |
| `room` | object | present only on `room-10deg` |

### `profile.room`

| Key | Type | Notes |
| --- | --- | --- |
| `tv_diagonal_in`, `seat_distance_in` | number | inches |
| `display_aspect` | string | for example `16:9` |
| `display_width_in`, `display_height_in` | number | derived |
| `field_degrees` | number | `10.0` |
| `field_inches` | number | `2 * seat_distance_in * tan(5 degrees)` |

## `segments[]`

One entry per interval that broke the thresholds. Segments with different `reason` values can
overlap. A player hides the union.

| Key | Type | Notes |
| --- | --- | --- |
| `start_ms` | integer | **hide from here.** Milliseconds from the start of the media timeline, as presentation timestamps, not frame numbers. |
| `end_ms` | integer | **hide up to here**, inclusive of the last offending frame |
| `flash_first_ms` | integer | timestamp of the first offending flash. For reporting, not for hiding. |
| `flash_last_ms` | integer | timestamp of the last offending flash. For reporting, not for hiding. |
| `reason` | string | `general` or `red` |
| `area_fraction` | number | 0 to 1, the largest share of an area window the flashing filled. Measured on the picture. |
| `area_window` | string | the name of the window `area_fraction` was measured in |
| `triggered_by` | array of string | the names of every area window that went over the limit |
| `breaks_baseline` | boolean | true when the profile's own window failed. False means only the room window failed, so this hide exists because of the household setting. |
| `max_flashes_in_window` | integer | the largest per pixel flash count seen in a one-second window inside this segment |

`start_ms` is the beginning of the failing one-second period, so it can be up to one second
earlier than `flash_first_ms`, and `end_ms` can run up to one second past `flash_last_ms`. That
is on purpose: the interval always contains the flashing and always starts before it.

## `summary`

| Key | Type | Notes |
| --- | --- | --- |
| `pass` | boolean | true when `segments` is empty |
| `segment_count` | integer | |
| `hidden_ms` | integer | total length of the merged segments |
| `general_segment_count`, `red_segment_count` | integer | |
| `area_measured_on` | string | `"picture"` |

## `signature`

Absent on an unsigned map. A reader that requires signatures treats absence as a failure.

| Key | Type | Notes |
| --- | --- | --- |
| `algorithm` | string | `ed25519` |
| `key_id` | string | `sha256:` plus the hex SHA-256 of the 32 raw public key bytes |
| `public_key` | string | base64 of the 32 raw public key bytes |
| `payload_sha256` | string | hex SHA-256 of the signed bytes, for debugging |
| `value` | string | base64 of the 64 byte Ed25519 signature |

### The exact bytes that are signed

1. Take the whole map object.
2. Remove the `signature` key. Nothing else changes.
3. Serialise with JSON: keys sorted, separators `,` and `:` with no spaces, UTF-8, no NaN or
   infinity.
4. Those bytes are the message. Ed25519 signs them directly, with no pre-hash.

In Python that is:

```python
json.dumps(
    {k: v for k, v in document.items() if k != "signature"},
    sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
).encode("utf-8")
```

A verifier rebuilds those bytes from the file it was handed, so changing one character anywhere
in the map breaks the signature. The pretty printed form on disk is not what is signed, so a
reader must re-serialise rather than hash the file.

## Worked example

```json
{
  "schema": "https://calm-frames.github.io/schemas/flashmap-map-v1.json",
  "version": 1,
  "generator": { "name": "flashmap", "version": "1.0.0" },
  "created_utc": "2026-09-17T22:00:00Z",
  "source": {
    "path": "clip.mkv",
    "sha256": "b304e1da964543740468dfe1ffb7b381d3070a2ae4e9644ffef7a43c2f40aa01",
    "size_bytes": 5797,
    "coded_width": 64, "coded_height": 48,
    "container_frame_rate": "20/1",
    "duration_ms": null,
    "frame_count": 30,
    "first_pts_ms": 0.0, "last_pts_ms": 1450.0, "last_coded_pts_ms": 1450.0,
    "variable_frame_rate": false,
    "frame_interval_ms": { "min": 50.0, "max": 50.0, "median": 50.0 },
    "timestamp_source": "container-pts"
  },
  "picture": {
    "measured_on": "picture",
    "left": 0, "top": 0, "width": 64, "height": 48,
    "frame_width": 64, "frame_height": 48,
    "letterbox": false, "pillarbox": false,
    "coded": { "left": 0, "top": 0, "width": 64, "height": 48 },
    "source": "detected",
    "note": "Area fractions in this map were measured on the picture rectangle above, not on the full coded frame. Letterbox and pillarbox bars were removed first."
  },
  "color": {
    "matrix": "bt709", "matrix_source": "stream-tag",
    "range": "limited", "range_source": "stream-tag",
    "pixel_format": "yuv444p", "transfer_tag": "2",
    "luminance_model": "wcag-relative-luminance-srgb",
    "analysis_width": 64, "analysis_height": 48
  },
  "profile": {
    "name": "wcag",
    "title": "WCAG 2.2 Success Criterion 2.3.1, general and red flash thresholds",
    "flash_limit_per_second": 3,
    "window_ms": 1000,
    "area_fraction_limit": 0.25,
    "area_window_mode": "ten-degree-field",
    "peak_nits": null,
    "general_flash": { "metric": "wcag-relative-luminance", "min_delta": 0.1, "dark_image_below": 0.8, "source": "WCAG 2.2 general flash and red flash thresholds (SPEC_SOURCES section 2)" },
    "red_flash": { "saturated_red_ratio": 0.8, "min_ucs_distance": 0.2, "source": "WCAG 2.2 thresholds Note 3 and Understanding 2.3.1 (SPEC_SOURCES sections 2, 4)" },
    "area_windows": [
      { "name": "wcag-10deg", "width_px": 21, "height_px": 16, "source": "WCAG 2.2 general flash and red flash thresholds, Note 1 (341/1024 by 256/768)" }
    ],
    "room": null,
    "transition_pairing": "non-overlapping",
    "transition_rule": "declared-on-first-frame-meeting-threshold",
    "window_placement": "trailing-closed-window-at-every-frame",
    "red_opposing_rule": "enter-saturated-red-paired-with-leave",
    "rules_not_implemented": ["the fine balanced pattern exception", "any HDR rule"],
    "exceptions_not_implemented": ["WCAG fine balanced pattern exception (white noise, checkerboards under 0.1 degree). Content the exception would excuse is still reported."],
    "spec_sources": "flashmap/docs/SPEC_SOURCES.md"
  },
  "segments": [
    {
      "start_ms": 0, "end_ms": 1450,
      "flash_first_ms": 100, "flash_last_ms": 1400,
      "reason": "general",
      "area_fraction": 1.0,
      "area_window": "wcag-10deg",
      "triggered_by": ["wcag-10deg"],
      "breaks_baseline": true,
      "max_flashes_in_window": 11
    }
  ],
  "summary": {
    "pass": false, "segment_count": 1, "hidden_ms": 1450,
    "general_segment_count": 1, "red_segment_count": 0,
    "area_measured_on": "picture"
  },
  "signature": {
    "algorithm": "ed25519",
    "key_id": "sha256:5a9e13c66b86fabcefd0261f462b878d58bb5289f577d40ca2f92643054568ae",
    "public_key": "RKH7ONac1sAt16sGl2aPnLwvZs/GZ6Ja1kgkxuOiSsI=",
    "payload_sha256": "a865de2d6e019ad62b775da8ec4b20299350ed2f7cb9bc0417101b4470cb9962",
    "value": "YEsmbKrIo57hFcmmAsPpXnQBQl5b3nbxwf0HhK6L7bfi1dzTeKstgxy4pNsPs8av5sChevVpwjmPNld9SizYDg=="
  }
}
```

## What this map does not say

- It does not say the content is safe. It says which parts went over the published thresholds
  that flashmap measured, on the picture, with the rules named in `profile`.
- It carries no HDR analysis. HLG and PQ files are refused rather than measured.
- It does not apply the WCAG fine balanced pattern exception, so some content it flags would be
  excused by a reading that did.
- It is not a medical device output.
