"""C3 unit 14: the HPT's blading from Table IV and Fig 3, with no
coordinates (solvers/blading/STEP0.md unit 14)."""
import math
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from blading.hpt_sections import ROWS, analyse  # noqa: E402

RES, ANGLES = analyse()
BY = {r.row: r for r in RES}


def test_all_four_rows():
    assert len(RES) == 4 and {r.row for r in RES} == set(ROWS)


def test_throat_recovered_from_the_aspect_ratio():
    """finding 49: h/d0 is height over throat"""
    for r in RES:
        assert abs(r.throat_m - r.height_m / r.aspect_ratio) < 1e-12
        assert 0.010 < r.throat_m < 0.017
        assert 0.24 < r.o_over_s < 0.50


def test_outlet_angles_agree_with_the_independent_mean_line():
    d = [r.alpha2_rule - ANGLES[r.row][1] for r in RES]
    assert max(abs(x) for x in d) < 3.0
    assert math.sqrt(sum(x * x for x in d) / len(d)) < 2.5


def test_the_bias_is_the_same_sign_and_size_as_the_lpt_unit():
    """finding 50: the missing -4(s/e) term, which the LPT measured at
    0.14-0.39 -- a correction of 0.6 to 1.5 degrees, bracketing this"""
    d = [r.alpha2_rule - ANGLES[r.row][1] for r in RES]
    m = statistics.mean(d)
    assert -2.5 < m < -0.5
    assert 0.6 < abs(m) < 1.5 + 1.0


def test_zweifel_three_of_four_rows():
    good = [r for r in RES if r.row != "stage2_vane"]
    for r in good:
        assert abs(r.zweifel - r.zweifel_printed) < 0.05, (r.row, r.zweifel)


def test_the_stage2_vane_is_the_outlier_again():
    """finding 51: the same row unit 3 flagged"""
    r = BY["stage2_vane"]
    assert r.zweifel < r.zweifel_printed - 0.10
    others = [abs(x.zweifel - x.zweifel_printed) for x in RES if x.row != "stage2_vane"]
    assert abs(r.zweifel - r.zweifel_printed) > 3 * max(others)


def test_zweifel_overall_is_in_band():
    d = [r.zweifel - r.zweifel_printed for r in RES]
    assert max(abs(x) for x in d) < 0.15
    assert math.sqrt(sum(x * x for x in d) / len(d)) < 0.10


def test_geometry_is_self_consistent():
    for r in RES:
        assert abs(r.pitch_m - 2 * math.pi * r.r_pitch_m / r.count) < 1e-12
        assert abs(r.axial_width_m - r.solidity * r.pitch_m) < 1e-12
        assert 0.02 < r.axial_width_m < 0.06
