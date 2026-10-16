"""Numeric-only characterization of flash area pooling. Never writes or displays media.

The fixtures use known rectangular pulses and an independent timing schedule.
This is review instrumentation, not a replacement detector or conformance oracle.
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from flashmap.analyze import StreamingAnalyzer, build_area_windows
from flashmap.area import max_coverage
from flashmap.decode import AnalysisFrame
from flashmap.picture import PictureRect
from flashmap.profiles import BROADCAST_SDR, WCAG
from flashmap.room import RoomSetting

GEOMETRIES = ('wcag-reference', 'wcag-room', 'broadcast-screen')
SCENARIOS = ('separate-bursts', 'one-patch', 'simultaneous', 'three-each',
             'expired-history', 'below-delta', 'overlap-offset')


class ObservedAnalyzer(StreamingAnalyzer):
    """Observe the unmodified accumulator's input and history."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.observations = []

    def _record(self, kind, pts_ms, mask):
        super()._record(kind, pts_ms, mask)
        if kind != 'general':
            return
        window = self.area_windows[0]
        counts = sum((older.astype(np.int16) for _, older in self._events[kind]),
                     np.zeros(mask.shape, dtype=np.int16))
        repeated = counts > self.profile.flash_limit_per_second
        self.observations.append({
            'pts_ms': pts_ms,
            'completed_area': max_coverage(mask, window.height_px, window.width_px),
            'pooled_area': max_coverage(repeated, window.height_px, window.width_px),
            'same_frame_repeated_area': max_coverage(repeated & mask, window.height_px, window.width_px),
            'max_per_pixel_count': int(counts.max()),
            'completed_pixels': int(mask.sum()),
        })


def fixture(geometry, scenario):
    picture = PictureRect(0, 0, 192, 108, False, False, 192, 108)
    profile = WCAG if geometry != 'broadcast-screen' else replace(BROADCAST_SDR, pattern=None)
    room = RoomSetting(85, 48) if geometry == 'wcag-room' else None
    window = build_area_windows(profile, picture, room)[-1]
    rows = window.height_px // 5
    patches = []
    for index in range(2):
        mask = np.zeros((108, 192), dtype=bool)
        mask[index * rows:(index + 1) * rows, :window.width_px] = True
        patches.append(mask)
    first = [40, 120, 200, 280]
    second = [520, 600, 680, 760]
    width = 40
    high = .8
    if scenario == 'one-patch': second = []
    if scenario == 'simultaneous': second = first
    if scenario == 'three-each': first, second = first[:3], second[:3]
    if scenario == 'expired-history': second = [1320, 1400, 1480, 1560]
    if scenario == 'below-delta': high = .21
    if scenario == 'overlap-offset':
        first, second, width = [40, 240, 440, 640], [80, 280, 480, 680], 120
    schedules = [first, second]
    analyzer = ObservedAnalyzer(profile, picture, [window])
    max_active_area = 0.0
    for index, stamp in enumerate(range(0, 2001, 40)):
        active = np.zeros((108, 192), dtype=bool)
        for mask, starts in zip(patches, schedules):
            if any(start <= stamp < start + width for start in starts): active |= mask
        max_active_area = max(max_active_area, max_coverage(active, window.height_px, window.width_px))
        level = np.full((108, 192), .2, dtype=np.float32)
        level[active] = high
        rgb = np.repeat(level[..., None], 3, axis=2)
        analyzer.push([AnalysisFrame(index, float(stamp), rgb, level)])
    segments = [segment.as_dict() for segment in analyzer.segments()]
    peak = max(analyzer.observations, key=lambda row: row['pooled_area'])
    return {
        'geometry': geometry, 'scenario': scenario, 'window': window.as_dict(),
        'patch_rows': rows, 'patch_area_fraction': rows / window.height_px,
        'bright_intervals_ms': [[[start, start + width] for start in starts] for starts in schedules],
        'input_gray_levels': [.2, high], 'frame_step_ms': 40,
        'max_active_area_from_schedule': max_active_area,
        'max_completed_area': max(row['completed_area'] for row in analyzer.observations),
        'max_same_frame_repeated_area': max(row['same_frame_repeated_area'] for row in analyzer.observations),
        'peak_pooled_observation': peak,
        'segments': segments,
    }


def main():
    results = [fixture(geometry, scenario) for geometry in GEOMETRIES for scenario in SCENARIOS]
    path = Path('results/detector-area-review-2026-10-16/fixtures.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'numeric_only': True, 'production_changed': False,
                               'broadcast_pattern_rule': 'excluded to isolate flash rule',
                               'results': results}, indent=2) + '\n')
    for row in results:
        print(row['geometry'], row['scenario'], 'active=', round(row['max_active_area_from_schedule'], 6),
              'pooled=', round(row['peak_pooled_observation']['pooled_area'], 6), 'segments=', len(row['segments']))


if __name__ == '__main__':
    main()
