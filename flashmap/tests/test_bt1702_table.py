"""The broadcast profile's signal to luminance curve, against the published table.

BT.1702-3 never prints an exponent. It prints Table 1, and points at BT.1886. This test is the
evidence that 2.4 with a zero black level is the curve the table was drawn from. If this test
goes red, the broadcast profile must not ship. See flashmap/docs/SPEC_SOURCES.md section 5.

Table 1, "Three types of luminance level", SDR column only, transcribed from
https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1702-3-202311-I!!PDF-E.pdf
"""

from __future__ import annotations

import numpy as np
import pytest

from flashmap import color

# (10-bit code value, SDR screen luminance in cd/m2)
TABLE_1_SDR = [
    (64, 0.00), (80, 0.01), (100, 0.09), (120, 0.27), (140, 0.57),
    (160, 0.99), (180, 1.56), (200, 2.29), (220, 3.18), (240, 4.25),
    (260, 5.50), (280, 6.95), (300, 8.59), (320, 10.44), (340, 12.51),
    (360, 14.80), (380, 17.31), (400, 20.06), (420, 23.04), (440, 26.27),
    (460, 29.75), (480, 33.48), (500, 37.48), (520, 41.74), (540, 46.27),
    (560, 51.07), (580, 56.15), (600, 61.52), (620, 67.17), (640, 73.12),
    (660, 79.36), (680, 85.90), (700, 92.75), (720, 99.91), (740, 107.37),
    (760, 115.15), (780, 123.26), (800, 131.68), (820, 140.43), (840, 149.52),
    (860, 158.93), (880, 168.69), (900, 178.78), (920, 189.22), (940, 200.00),
]

# "For content mastered per Rec. ITU-R BT.709 10-bit digital code values (D) map to V as per
# the following equation: V = (D-64)/876."
PEAK_NITS = 200.0
PRINTED_PRECISION = 0.005


def test_curve_reproduces_every_printed_sdr_row():
    codes = np.array([code for code, _ in TABLE_1_SDR], dtype=np.float64)
    published = np.array([nits for _, nits in TABLE_1_SDR], dtype=np.float64)
    levels = (codes - 64.0) / 876.0
    predicted = color.bt1886_nits(levels, PEAK_NITS).astype(np.float64)
    errors = np.abs(predicted - published)
    worst = float(errors.max())
    assert worst <= PRINTED_PRECISION, (
        f"the signal to luminance curve is off by {worst:.4f} cd/m2 at code "
        f"{int(codes[int(errors.argmax())])}, which is more than the table's own rounding"
    )


def test_peak_white_is_the_assumed_two_hundred_nits():
    assert color.bt1886_nits(np.array([1.0]), PEAK_NITS).item() == 200.0


def test_the_160_nit_boundary_lands_where_the_recommendation_says_it_does():
    # "NOTE 2 - A luminance signal level with the 10-bit code value of 863 results in screen
    # luminance of 160.4 cd/m2 for SDR".
    level = (863.0 - 64.0) / 876.0
    assert color.bt1886_nits(np.array([level]), PEAK_NITS).item() == pytest.approx(160.4, abs=0.05)


def test_the_20_nit_boundary_lands_where_the_recommendation_says_it_does():
    # "NOTE 1 - A luminance signal level with the 10-bit code value of 400 results in screen
    # luminance of 20.1 cd/m2 for SDR".
    level = (400.0 - 64.0) / 876.0
    assert color.bt1886_nits(np.array([level]), PEAK_NITS).item() == pytest.approx(20.1, abs=0.05)
