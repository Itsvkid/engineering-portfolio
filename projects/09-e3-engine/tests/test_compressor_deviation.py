"""C1 unit 4: Carter's rule (SP-36 eq 270, Fig 160) against the deviation
Table XXI prints for all 240 HPC streamline points. Bands in
solvers/meanline/STEP0.md unit 4."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from meanline.compressor import carter_deviation, carter_m, deviation_checks  # noqa: E402

CHECKS = deviation_checks()
BY_ROW = {}
for c in CHECKS:
    BY_ROW.setdefault(c.row, []).append(c)


def test_every_row_has_twelve_points():
    assert len(CHECKS) == 240
    assert len(BY_ROW) == 20
    assert all(len(v) == 12 for v in BY_ROW.values())


def test_carter_m_matches_fig160():
    assert abs(carter_m(0) - 0.216) < 0.01
    assert abs(carter_m(30) - 0.269) < 0.01
    assert abs(carter_m(60) - 0.369) < 0.01
    assert carter_m(30, "parabolic_arc") < carter_m(30)


def test_mean_bias_is_small():
    d = [c.dev_carter - c.dev_printed for c in CHECKS]
    assert abs(sum(d) / len(d)) < 1.0


@pytest.mark.xfail(strict=True, reason="unit 4 finding 11: rms 2.58 deg, 0.08 outside the band, and it is a pattern not scatter -- rear rotors under-predicted 1.4-2.9 deg, front stators over-predicted 1.5-2.3")
def test_rms_within_band():
    d = [c.dev_carter - c.dev_printed for c in CHECKS]
    assert math.sqrt(sum(x * x for x in d) / len(d)) < 2.5


def test_rms_is_pinned():
    d = [c.dev_carter - c.dev_printed for c in CHECKS]
    assert 2.4 < math.sqrt(sum(x * x for x in d) / len(d)) < 2.8


def test_rear_rotors_are_systematically_under_predicted():
    """finding 11: the deficit rises monotonically through the rear rotors"""
    means = {}
    for row, cs in BY_ROW.items():
        means[row] = sum(c.dev_carter - c.dev_printed for c in cs) / len(cs)
    rear = [means[f"R{n}"] for n in (6, 7, 8, 9, 10)]
    assert all(-3.0 < m < -1.0 for m in rear), rear
    assert rear[-1] < rear[0]
    front = [means[f"R{n}"] for n in (1, 2, 3, 4, 5)]
    assert all(abs(m) < 1.0 for m in front), front


def test_front_stators_are_systematically_over_predicted():
    means = {row: sum(c.dev_carter - c.dev_printed for c in cs) / len(cs) for row, cs in BY_ROW.items()}
    assert all(1.0 < means[f"S{n}"] < 2.5 for n in (1, 2, 3, 4))


def test_circular_arc_beats_parabolic_on_this_compressor():
    dc = [c.dev_carter - c.dev_printed for c in CHECKS]
    dp = [c.dev_parabolic - c.dev_printed for c in CHECKS]
    assert abs(sum(dc) / len(dc)) < abs(sum(dp) / len(dp))
    assert sum(dp) / len(dp) < -1.5


def test_deviation_rises_with_camber_and_falls_with_solidity():
    base = carter_deviation(30.0, 40.0, 0.75)
    assert carter_deviation(60.0, 40.0, 0.75) > 1.9 * base
    assert carter_deviation(30.0, 40.0, 0.50) < base
