"""C3 unit 13: the LPT's transcribed coordinates against R&M 2974's
outlet-angle rule and Table III's Zweifel (solvers/blading/STEP0.md unit 13)."""
import math
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from blading.lpt_sections import ROWS, SPANS, analyse  # noqa: E402

RES = analyse()


def test_every_section_was_read():
    assert len(RES) == len(ROWS) * len(SPANS) == 30
    assert {r.row for r in RES} == set(ROWS)


def test_throat_to_pitch_is_a_turbine_throat():
    o = [r.o_over_s for r in RES]
    assert 0.35 < min(o) and max(o) < 0.75
    for r in RES:
        assert 40 < r.acos_o_s_deg < 70


def test_outlet_angle_from_fig5_alone():
    """finding 46: three independent sources agreeing"""
    d = [r.alpha2_rule - r.alpha2_printed for r in RES]
    assert max(abs(x) for x in d) < 3.0
    assert math.sqrt(sum(x * x for x in d) / len(d)) < 2.0


def test_fig5_alone_leaves_a_systematic_bias():
    """finding 47: all the predicted angles are slightly too shallow"""
    d = [r.alpha2_rule - r.alpha2_printed for r in RES]
    assert -1.2 < statistics.mean(d) < -0.4


def test_the_curvature_term_closes_the_bias():
    d1 = [r.alpha2_rule - r.alpha2_printed for r in RES]
    d2 = [r.alpha2_full_rule - r.alpha2_printed for r in RES]
    assert abs(statistics.mean(d2)) < abs(statistics.mean(d1))
    assert abs(statistics.mean(d2)) < 0.5
    assert max(abs(x) for x in d2) < 3.5


def test_the_curvature_fit_succeeds_everywhere():
    """the bug that failed on exactly the stators is fixed"""
    assert all(r.s_over_e > 0 for r in RES)
    se = [r.s_over_e for r in RES]
    assert 0.10 < min(se) and max(se) < 0.45
    assert 0.18 < statistics.median(se) < 0.36


def test_zweifel_from_the_coordinates_matches_table_iii():
    """finding 48"""
    d = [r.zweifel - r.zweifel_printed for r in RES if r.span == 50]
    assert len(d) == 10
    assert max(abs(x) for x in d) < 0.15
    assert math.sqrt(sum(x * x for x in d) / len(d)) < 0.10


def test_blade_counts_and_pitches_are_consistent():
    for r in RES:
        assert abs(r.pitch_m - 2 * math.pi * r.radius_m / r.count) < 1e-9
        assert 0.01 < r.pitch_m < 0.05
