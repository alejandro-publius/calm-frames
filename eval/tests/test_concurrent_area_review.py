"""Headless characterization, not conformance certification or a detector replacement."""
import pytest

from eval.concurrent_area_review import GEOMETRIES, SCENARIOS, fixture


@pytest.mark.parametrize('geometry', GEOMETRIES)
@pytest.mark.parametrize('scenario', SCENARIOS)
def test_characterizes_current_pooling_with_independent_rectangular_schedules(geometry, scenario):
    result = fixture(geometry, scenario)
    expected_flag = scenario in ('separate-bursts', 'simultaneous', 'overlap-offset')
    assert bool(result['segments']) == expected_flag
    patch = result['patch_rows'] / result['window']['height_px']
    # Rectangles have the full window width. Their area is rows / height,
    # independently of the production summed-area implementation.
    assert result['patch_area_fraction'] == patch
    assert patch < .25 < 2 * patch
    overlap = scenario in ('simultaneous', 'overlap-offset')
    assert result['max_active_area_from_schedule'] == pytest.approx((2 if overlap else 1) * patch)
    if scenario == 'separate-bursts':
        assert result['peak_pooled_observation']['pooled_area'] == pytest.approx(2 * patch)
        assert result['peak_pooled_observation']['pts_ms'] == 800
        assert result['peak_pooled_observation']['max_per_pixel_count'] == 4
        # Even if a flash starts one frame before its leading edge,
        # the complete bursts are separated by 160 ms.
        first, second = result['bright_intervals_ms']
        assert first[-1][1] < second[0][0] - result['frame_step_ms']


@pytest.mark.parametrize('geometry', GEOMETRIES)
def test_same_completion_frame_is_not_a_valid_concurrency_repair(geometry):
    result = fixture(geometry, 'overlap-offset')
    # These flashes overlap in duration, but their completion frames differ.
    assert result['max_active_area_from_schedule'] > .25
    assert result['max_same_frame_repeated_area'] < .25
    assert result['segments']


@pytest.mark.parametrize('geometry', GEOMETRIES)
@pytest.mark.xfail(strict=True, reason='Known mismatch: separate sub-threshold bursts are pooled as one area')
def test_separated_small_bursts_are_not_a_concurrent_area_violation(geometry):
    result = fixture(geometry, 'separate-bursts')
    assert result['max_active_area_from_schedule'] < .25
    assert result['segments'] == []
