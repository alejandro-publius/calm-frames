"""Break each guard on purpose and confirm the test that guards it goes red.

A green new test proves nothing on its own. Run this and every guard in flashmap has been seen
to fail:

    python flashmap/tools/mutate.py

For each entry below it edits one line of the source, runs only the tests that are supposed to
catch that edit, and expects them to fail. Then it puts the file back and checks the whole tree
is byte for byte what it was.

Two things this harness learned the hard way, both of which would have made it lie:

* A mutation that keeps the file the same length can be hidden by a cached .pyc, because the
  cache is keyed on the source mtime in whole seconds and its size. Every run clears every
  __pycache__ first and sets PYTHONDONTWRITEBYTECODE, so the mutated source has to be compiled
  fresh, and the caches are cleared again at the end so a later plain pytest run is clean too.
* A mutation that is never imported is not a mutation. The canary check confirms the mutated
  text is in the file the interpreter actually loads before any test is run.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "flashmap"
PY = sys.executable

# (label, file, old, new, tests that must go red)
MUTATIONS = [
    ("relative luminance weights", "color.py",
     "LUMA_R = 0.2126", "LUMA_R = 0.5000",
     ["tests/test_color.py::test_relative_luminance_weights_are_the_published_ones"]),
    ("srgb break point", "color.py",
     "SRGB_LINEAR_BREAK = 0.04045", "SRGB_LINEAR_BREAK = 0.5",
     ["tests/test_color.py::test_srgb_break_point_uses_the_linear_segment"]),
    ("srgb exponent", "color.py",
     "SRGB_EXPONENT = 2.4", "SRGB_EXPONENT = 2.2",
     ["tests/test_color.py::test_srgb_above_the_break_point_uses_the_power_segment",
      "tests/test_color.py::test_black_and_white_relative_luminance"]),
    ("bt1886 gamma", "color.py",
     "BT1886_GAMMA = 2.4", "BT1886_GAMMA = 2.2",
     ["tests/test_bt1702_table.py::test_curve_reproduces_every_printed_sdr_row"]),
    ("ucs u prime numerator", "color.py",
     "u = np.where(denom > 0.0, np.float32(4.0) * big_x / safe, np.float32(0.0))",
     "u = np.where(denom > 0.0, np.float32(5.0) * big_x / safe, np.float32(0.0))",
     ["tests/test_color.py::test_ucs_matches_the_published_formula_for_a_sample_colour",
      "tests/test_color.py::test_xyz_of_white_is_d65_and_y_is_one"]),
    ("srgb to xyz matrix", "color.py",
     "[0.2126729, 0.7151522, 0.0721750],", "[0.3126729, 0.6151522, 0.0721750],",
     ["tests/test_flash_tracker.py::test_every_coefficient_of_the_srgb_to_xyz_matrix"]),

    ("general flash 10 percent", "profiles.py",
     "        min_delta=0.10,\n        dark_image_below=0.80,",
     "        min_delta=0.01,\n        dark_image_below=0.80,",
     ["tests/test_general_flash.py::test_a_swing_under_ten_percent_is_not_a_flash"]),
    ("darker image below 0.80", "profiles.py",
     "        min_delta=0.10,\n        dark_image_below=0.80,",
     "        min_delta=0.10,\n        dark_image_below=1.01,",
     ["tests/test_general_flash.py::test_flashing_between_two_bright_images_is_not_a_general_flash"]),
    ("three flashes a second", "profiles.py",
     "    flash_limit_per_second=3,\n    window_ms=1000,\n    area_fraction_limit=0.25,\n    area_window_mode=\"ten-degree-field\",",
     "    flash_limit_per_second=2,\n    window_ms=1000,\n    area_fraction_limit=0.25,\n    area_window_mode=\"ten-degree-field\",",
     ["tests/test_general_flash.py::test_three_flashes_a_second_passes",
      "tests/test_red_flash.py::test_three_red_flashes_a_second_passes"]),
    ("25 percent area limit", "profiles.py",
     "    flash_limit_per_second=3,\n    window_ms=1000,\n    area_fraction_limit=0.25,\n    area_window_mode=\"ten-degree-field\",",
     "    flash_limit_per_second=3,\n    window_ms=1000,\n    area_fraction_limit=0.05,\n    area_window_mode=\"ten-degree-field\",",
     ["tests/test_overlays.py::test_a_subtitle_popping_in_and_out_every_frame_does_not_trigger",
      "tests/test_overlays.py::test_a_small_blinking_icon_does_not_trigger",
      "tests/test_area.py::test_a_band_that_fills_a_fifth_of_the_field_passes"]),
    ("saturated red ratio", "profiles.py",
     "        saturated_red_ratio=0.8,\n        min_ucs_distance=0.2,\n        source=\"WCAG 2.2 thresholds",
     "        saturated_red_ratio=0.3,\n        min_ucs_distance=0.2,\n        source=\"WCAG 2.2 thresholds",
     ["tests/test_flash_tracker.py::test_the_profile_thresholds_are_the_ones_the_tracker_boundaries_use",
      "tests/test_sidecar.py::test_the_map_records_the_profile_numbers_that_were_applied"]),
    ("red ucs distance", "profiles.py",
     "        saturated_red_ratio=0.8,\n        min_ucs_distance=0.2,\n        source=\"WCAG 2.2 thresholds",
     "        saturated_red_ratio=0.8,\n        min_ucs_distance=0.9,\n        source=\"WCAG 2.2 thresholds",
     ["tests/test_red_flash.py::test_red_to_gray_at_ten_hertz_is_a_red_flash"]),
    ("one second window", "profiles.py",
     "    flash_limit_per_second=3,\n    window_ms=1000,\n    area_fraction_limit=0.25,\n    area_window_mode=\"ten-degree-field\",",
     "    flash_limit_per_second=3,\n    window_ms=3000,\n    area_fraction_limit=0.25,\n    area_window_mode=\"ten-degree-field\",",
     ["tests/test_general_flash.py::test_three_flashes_a_second_passes"]),

    ("ten degree field height", "area.py",
     "WCAG_FIELD_HEIGHT_FRACTION = 256.0 / 768.0", "WCAG_FIELD_HEIGHT_FRACTION = 1.0",
     ["tests/test_area.py::test_the_reference_window_is_the_published_fraction_of_the_picture",
      "tests/test_area.py::test_a_band_that_fills_more_than_a_quarter_of_the_field_fails"]),
    ("sliding window takes the max", "area.py",
     "    return float(sums.max()) / float(win_h * win_w)",
     "    return float(sums.mean()) / float(win_h * win_w)",
     ["tests/test_area.py::test_the_window_slides_to_the_busiest_place_not_the_average",
      "tests/test_area.py::test_a_band_that_fills_more_than_a_quarter_of_the_field_fails"]),
    ("best window takes the largest", "area.py",
     "        if best is None or value > best_value:",
     "        if best is None or value < best_value:",
     ["tests/test_flash_tracker.py::test_best_window_returns_the_window_with_the_largest_coverage"]),

    ("untagged hd cutoff", "decode.py",
     "    hd_min_height: int = 720", "    hd_min_height: int = 1",
     ["tests/test_decode_color.py::test_untagged_sd_is_bt601",
      "tests/test_decode_color.py::test_untagged_sd_clip_is_read_as_bt601"]),
    ("yuvj means full range", "decode.py",
     '    if pixel_format.startswith("yuvj"):\n        color_range, range_source = "full", "pixel-format-yuvj"',
     '    if pixel_format.startswith("NEVERMATCH"):\n        color_range, range_source = "full", "pixel-format-yuvj"',
     ["tests/test_decode_color.py::test_yuvj_is_full_range_even_when_the_range_tag_says_limited",
      "tests/test_decode_color.py::test_full_range_clip_is_decoded_full_range"]),
    ("hdr is refused", "decode.py",
     "    if not policy.allow_hdr and transfer_tag in (_AVCOL_TRC_SMPTE2084, _AVCOL_TRC_ARIB_STD_B67):",
     "    if False and transfer_tag in (_AVCOL_TRC_SMPTE2084, _AVCOL_TRC_ARIB_STD_B67):",
     ["tests/test_decode_color.py::test_hdr_is_refused_rather_than_measured_with_the_sdr_curve"]),
    ("real timestamps not an assumed rate", "decode.py",
     "            pts_ms = float(stamp * time_base) * 1000.0",
     "            pts_ms = index * 1000.0 / 20.0",
     ["tests/test_vfr.py::test_timestamps_come_from_the_container",
      "tests/test_vfr.py::test_the_same_pixels_spread_out_in_time_are_not",
      "tests/test_vfr.py::test_a_variable_rate_clip_is_reported_as_variable"]),
    ("limited range luma normalisation", "decode.py",
     "                level = (level - np.float32(16.0)) / np.float32(219.0)",
     "                level = level / np.float32(255.0)",
     ["tests/test_decode_color.py::test_limited_range_luma_is_normalised_from_16_to_235"]),

    ("letterbox detection", "picture.py",
     "    top = _leading_run(dark_rows)", "    top = 0",
     ["tests/test_picture.py::test_detect_picture_finds_top_and_bottom_bars",
      "tests/test_picture.py::test_a_letterboxed_clip_is_measured_on_the_picture"]),
    ("pillarbox detection", "picture.py",
     "    left = _leading_run(dark_cols)", "    left = 0",
     ["tests/test_picture.py::test_detect_picture_finds_left_and_right_bars",
      "tests/test_picture.py::test_a_pillarboxed_clip_is_measured_on_the_picture"]),
    ("bars judged over every sampled frame", "picture.py",
     "    stack = np.maximum.reduce([np.asarray(frame, dtype=np.float32) for frame in luminances])",
     "    stack = np.minimum.reduce([np.asarray(frame, dtype=np.float32) for frame in luminances])",
     ["tests/test_picture.py::test_bars_are_judged_over_every_sampled_frame_not_just_one"]),
    ("red needs to cross into or out of the saturated state", "flash.py",
     "        confirmed = (is_red != anchor_red) & (distance > np.float32(self.min_distance))",
     "        confirmed = (distance > np.float32(self.min_distance))",
     ["tests/test_flash_tracker.py::test_a_colour_change_that_does_not_involve_red_is_not_a_transition"]),

    ("transition state machine can reverse", "flash.py",
     "        reversing = ((direction > 0) & (values < extreme)) | (\n            (direction < 0) & (values > extreme)\n        )",
     "        reversing = np.zeros(values.shape, dtype=bool)",
     ["tests/test_general_flash.py::test_the_segment_covers_the_flashing_and_starts_before_it"]),
    ("flashes are pairs of opposing transitions", "flash.py",
     "        flashed = confirmed & (pending != 0) & (pending != sign)\n        pending = np.where(\n            flashed, np.int8(0), np.where(confirmed, sign, pending)\n        ).astype(np.int8)\n        anchor = np.where(confirmed, extreme, anchor).astype(np.float32)",
     "        flashed = confirmed\n        pending = np.where(\n            flashed, np.int8(0), np.where(confirmed, sign, pending)\n        ).astype(np.int8)\n        anchor = np.where(confirmed, extreme, anchor).astype(np.float32)",
     ["tests/test_general_flash.py::test_three_flashes_a_second_passes",
      "tests/test_general_flash.py::test_a_slow_ramp_is_not_flashing"]),

    ("area window sized from the picture not the coded frame", "analyze.py",
     "        windows = [wcag_reference_window(picture.width, picture.height)]",
     "        windows = [wcag_reference_window(picture.frame_width, picture.frame_height)]",
     ["tests/test_picture.py::test_a_letterboxed_clip_is_measured_on_the_picture",
      "tests/test_picture.py::test_a_pillarboxed_clip_is_measured_on_the_picture"]),
    ("room window is added not swapped in", "analyze.py",
     "    if room is not None:\n        windows.append(",
     "    if room is not None:\n        windows.clear()\n        windows.append(",
     ["tests/test_room.py::test_the_room_window_is_added_to_the_profile_window_not_swapped_for_it",
      "tests/test_room.py::test_no_room_setting_can_make_the_output_weaker_than_wcag"]),
    ("chunk overlap is deduplicated", "analyze.py",
     "            if self._last_pts is not None and frame.pts_ms <= self._last_pts:\n                continue",
     "            if False:\n                continue",
     ["tests/test_chunking.py::test_chunked_equals_whole_file",
      "tests/test_chunking.py::test_chunking_through_the_public_entry_point_matches"]),
    ("segment covers the failing window", "analyze.py",
     "        start = max(0.0, pts_ms - window_ms)", "        start = pts_ms",
     ["tests/test_sidecar.py::test_segment_fields"]),
    ("variable frame rate is reported", "analyze.py",
     '        variable = bool(stats["max"] - stats["min"] > 1.0)',
     '        variable = False',
     ["tests/test_vfr.py::test_a_variable_rate_clip_is_reported_as_variable"]),

    ("ucs v prime numerator", "color.py",
     "    v = np.where(denom > 0.0, np.float32(9.0) * big_y / safe, np.float32(0.0))",
     "    v = np.where(denom > 0.0, np.float32(8.0) * big_y / safe, np.float32(0.0))",
     ["tests/test_color.py::test_ucs_matches_the_published_formula_for_a_sample_colour",
      "tests/test_flash_tracker.py::test_the_ucs_of_pure_red_is_where_the_srgb_primary_sits"]),
    ("flash pairing is non overlapping", "flash.py",
     "        flashed = confirmed & (pending != 0) & (pending != sign)\n        pending = np.where(\n            flashed, np.int8(0), np.where(confirmed, sign, pending)\n        ).astype(np.int8)\n        anchor = np.where(confirmed, extreme, anchor).astype(np.float32)",
     "        flashed = confirmed & (pending != 0) & (pending != sign)\n        pending = np.where(\n            False, np.int8(0), np.where(confirmed, sign, pending)\n        ).astype(np.int8)\n        anchor = np.where(confirmed, extreme, anchor).astype(np.float32)",
     ["tests/test_flash_tracker.py::test_a_square_wave_gives_one_flash_per_cycle"]),
    ("red anchor moves only on a confirmed transition", "flash.py",
     "        self._is_red = np.where(confirmed, is_red, anchor_red)",
     "        self._is_red = is_red",
     ["tests/test_flash_tracker.py::test_a_redness_flip_with_no_chromaticity_move_does_not_shift_the_reference_state"]),

    ("room window follows the seat distance", "room.py",
     "        return 2.0 * self.seat_distance_in * math.tan(math.radians(FIELD_DEGREES / 2.0))",
     "        return 16.798",
     ["tests/test_room.py::test_sitting_closer_makes_the_window_smaller_and_so_the_test_stricter",
      "tests/test_room.py::test_a_close_seat_adds_a_hide_that_wcag_alone_does_not_ask_for"]),

    ("signature covers the map body", "sidecar.py",
     '    payload = {key: value for key, value in document.items() if key != "signature"}',
     "    payload = {\"constant\": 1}",
     ["tests/test_sidecar.py::test_changing_one_segment_breaks_the_signature",
      "tests/test_sidecar.py::test_removing_every_segment_breaks_the_signature"]),
    ("map is bound to the file hash", "sidecar.py",
     "                source_hash_matches = actual == expected_hash",
     "                source_hash_matches = True",
     ["tests/test_sidecar.py::test_a_map_for_a_different_file_does_not_verify",
      "tests/test_cli.py::test_verify_rejects_a_map_made_for_another_file"]),
    ("unsigned maps are refused", "sidecar.py",
     "        if require_signature:\n            problems.append(\"map is not signed\")",
     "        if False:\n            problems.append(\"map is not signed\")",
     ["tests/test_sidecar.py::test_an_unsigned_map_is_refused_unless_you_ask_for_it",
      "tests/test_cli.py::test_verify_rejects_an_unsigned_map_unless_told_not_to"]),
    ("map version is checked", "sidecar.py",
     "    if document.get(\"version\") != SIDECAR_VERSION:",
     "    if False:",
     ["tests/test_sidecar.py::test_a_map_with_the_wrong_version_is_refused"]),

    ("the action fails a bad file", "ci.py",
     "    if failed:\n        print(\n            f\"\\nflashmap: {len(failed)} file(s) break WCAG 2.2 Success Criterion 2.3.1.\",",
     "    if False:\n        print(\n            f\"\\nflashmap: {len(failed)} file(s) break WCAG 2.2 Success Criterion 2.3.1.\",",
     ["tests/test_ci_action.py::test_a_flashing_image_fails_the_check",
      "tests/test_ci_action.py::test_one_bad_file_among_good_ones_still_fails"]),
    ("media files are picked out of a diff", "ci.py",
     "        if path.suffix.lower() not in MEDIA_SUFFIXES:",
     "        if path.suffix.lower() in MEDIA_SUFFIXES:",
     ["tests/test_ci_action.py::test_media_files_are_selected_and_source_files_are_not"]),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clear_bytecode() -> None:
    """A mutation that keeps the file the same size can be masked by a cached .pyc whose
    stored mtime second and size still match. Remove every cache before every run, and turn
    writing them off, so the mutated source has to be compiled fresh."""
    for cache in ROOT.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


def run(tests: list[str]) -> tuple[int, str]:
    clear_bytecode()
    proc = subprocess.run(
        [PY, "-m", "pytest", "-q", *tests],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    return proc.returncode, proc.stdout[-800:] + proc.stderr[-400:]


def canary(module: str, needle: str) -> bool:
    """Prove the mutated text is in the module the interpreter actually loads."""
    code = (
        f"import flashmap.{module} as m, pathlib, sys;"
        f"src = pathlib.Path(m.__file__).read_text();"
        f"sys.exit(0 if {needle!r} in src else 3)"
    )
    clear_bytecode()
    return subprocess.run([PY, "-c", code], cwd=ROOT, env=ENV, capture_output=True).returncode == 0


def main() -> int:
    before = {path: digest(path) for path in sorted(SRC.glob("*.py"))}

    baseline_code, baseline_out = run(["tests/", "-m", "not slow"])
    if baseline_code != 0:
        print("BASELINE IS ALREADY RED, stopping")
        print(baseline_out)
        return 2
    print(f"baseline green: {baseline_out.strip().splitlines()[-1]}\n")

    survived: list[str] = []
    for label, filename, old, new, tests in MUTATIONS:
        path = SRC / filename
        original = path.read_text()
        if old not in original:
            print(f"!! {label}: the text to mutate is not in {filename}")
            survived.append(label + " (not applied)")
            continue
        if original.count(old) != 1:
            print(f"!! {label}: {original.count(old)} matches in {filename}, expected 1")
            survived.append(label + " (ambiguous)")
            continue

        path.write_text(original.replace(old, new))
        assert digest(path) != before[path], "the file on disk did not change"
        if not canary(filename[:-3], new.strip().splitlines()[0]):
            path.write_text(original)
            print(f"!! {label}: the mutated source is not what gets imported")
            survived.append(label + " (canary failed)")
            continue
        try:
            code, output = run(tests)
        finally:
            path.write_text(original)
            assert digest(path) == before[path], "restore failed"

        last = output.strip().splitlines()[-1] if output.strip() else ""
        if code == 0:
            print(f"SURVIVED  {label:52s} {last}")
            survived.append(label)
        else:
            print(f"killed    {label:52s} {last}")

    after = {path: digest(path) for path in sorted(SRC.glob("*.py"))}
    assert after == before, "the tree was not restored"
    print("\ntree restored byte for byte")

    clear_bytecode()
    final_code, final_out = run(["tests/"])
    clear_bytecode()
    print(f"final full run: {final_out.strip().splitlines()[-1]}")

    if survived:
        print(f"\n{len(survived)} MUTATION(S) SURVIVED:")
        for label in survived:
            print(f"  - {label}")
        return 1
    print(f"\nall {len(MUTATIONS)} mutations killed")
    return 0 if final_code == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
