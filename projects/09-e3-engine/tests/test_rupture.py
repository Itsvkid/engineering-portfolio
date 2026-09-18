"""Unit E10 -- HPT blade rupture life from CR-167955 Fig 84.

Bands written into solvers/mechanical/STEP0.md before the module ran.
Band 3 is E1's own closure and it MISSES; it is pinned as a strict xfail
with its size recorded, not widened.
"""
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solvers"))

from mechanical import rupture as R      # noqa: E402


def test_band1_fig84_and_fig35_are_the_same_section():
    b = R.band1_same_section()
    assert b["dmin"] <= 25 and b["dmax"] <= 25


def test_band1_finding_245_the_cold_point_is_an_interior_node():
    """against SURFACE nodes alone the cold end misses by 47 K; the point is
    inside the wall. If this ever passes on the surface set, the finding is
    wrong and the note in STEP0 must go."""
    b = R.band1_same_section()
    assert b["dmin_surface_only"] > 25
    assert b["dmin"] <= 2


@pytest.mark.parametrize("stage", ["stage1", "stage2"])
def test_band2_mission_mix_closes_on_itself(stage):
    d = R.band2_mission_mix()[stage]
    assert abs(d["share_sum"] - 100.0) <= 0.2       # printed 100.1, rounding
    assert d["margin"] >= 1.0                        # each blade makes its life


def test_band2_finding_246_the_two_blades_agree_about_climb():
    m = R.band2_mission_mix()
    a, b = m["stage1"]["life_ratio_climb"], m["stage2"]["life_ratio_climb"]
    assert abs(a / b - 1.0) < 0.10
    # and disagree more about cruise, which carries the least damage
    c, d = m["stage1"]["life_ratio_cruise"], m["stage2"]["life_ratio_cruise"]
    assert abs(c / d - 1.0) > abs(a / b - 1.0)


@pytest.mark.xfail(strict=True, reason=(
    "E1's second half. A same-stress Larson-Miller transfer gives 109 h "
    "against a published 264, a factor of 2.43 outside the factor of 2. "
    "The miss is a STRESS, not a creep model: the two blades' pitch-section "
    "areas were never published (finding 247)."))
def test_band3_stage1_rupture_life_within_a_factor_of_two():
    b = R.band3_same_stress_transfer()
    assert b["factor_vs_table_xx"] < 2.0


def test_band3_the_size_of_the_miss_is_pinned():
    b = R.band3_same_stress_transfer()
    assert 2.3 < b["factor_vs_table_xx"] < 2.6
    assert 100 < b["predicted_hours"] < 120


def test_band3_the_implied_stress_ratio_is_below_one_and_sane():
    """the stage-1 blade must be the LESS stressed of the two, and not
    absurdly so, over the whole handbook range of the rupture exponent"""
    for n in (8.0, 10.0, 15.0):
        assert 0.85 < R.implied_stress_ratio(n) < 1.0


def test_band4_the_residual_is_ordered_by_position():
    """the two hottest points carry the two largest positive residuals --
    they are hot because they are thin, and thin means lightly loaded"""
    _, rows = R.band4_constant_stress_residuals()
    hottest = sorted(rows, key=lambda r: -r["C"])[:2]
    assert {r["where"] for r in hottest} == {r["where"] for r in rows[:2]}
    assert rows[0]["dlog"] > 1.0


def test_band4_the_eleven_points_are_not_one_creep_curve():
    """if they collapsed, Fig 84 would be a creep curve; it is a stress map"""
    _, rows = R.band4_constant_stress_residuals()
    assert max(r["dlog"] for r in rows) - min(r["dlog"] for r in rows) > 1.5


@pytest.mark.xfail(strict=True, reason=(
    "band 5 was stated as +-20 percent of the standing 10x rule and the "
    "answer is 20.2 percent low -- a miss by a hair, recorded rather than "
    "widened. On the E3's own numbers 50 C of metal temperature is worth "
    "8x, not 10x (finding 248)."))
def test_band5_fifty_degrees_is_within_twenty_percent_of_ten():
    assert abs(R.band5_fifty_degrees() / 10.0 - 1.0) <= 0.20


def test_band5_the_number_is_pinned():
    assert 7.9 < R.band5_fifty_degrees() < 8.1


def test_the_larson_miller_constant_is_labelled_an_assumption():
    src = (ROOT / "solvers" / "mechanical" / "rupture.py").read_text()
    assert "ASSUMPTION" in src
    assert R.C_LARSON_MILLER == 20.0
