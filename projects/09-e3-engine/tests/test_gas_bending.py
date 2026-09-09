"""Stage E unit E8: gas bending and the stacking tilt
(solvers/mechanical/STEP0.md unit E8)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from mechanical.gas_bending import (  # noqa: E402
    BAND_PCT, bending, comparison, euler_check, gas_loads, published,
    root_section_properties, summary, the_tilt_cancels,
)

C = comparison()
P = published()


# --- the published decomposition -----------------------------------------

def test_table_viii_is_carried_with_all_three_parts():
    assert len(P) == 5
    for p in P:
        assert p["centrifugal_root"] > 0
        assert p["gas_bending_root"] > 0
        assert p["resultant_root"] > 0


def test_gas_bending_grows_towards_the_back_of_the_turbine():
    """longer blades, more load"""
    gb = [p["gas_bending_root"] for p in P]
    assert gb == sorted(gb)


# --- the Euler guard: finding 176 ----------------------------------------

def test_euler_work_agrees_with_the_sum_convention():
    """dh = U x delta_c_theta is an identity, so this is the check that
    catches a misread sign -- and did"""
    for r in euler_check():
        assert abs(r["err_pct"]) < 5.0, r


def test_the_difference_convention_is_wrong_by_a_lot():
    """kept as a test because it is what the first draft used: the stage
    exit is counter-swirled and alpha3 is stored as a magnitude, so the
    swirl CHANGE is the sum"""
    for r in euler_check():
        ratio = r["dct_from_work"] / r["difference_convention"]
        assert ratio > 1.3, r
        assert r["sum_convention"] > r["difference_convention"]


def test_the_loads_use_the_sum():
    from meanline.lpt import run
    st = [x for x in run() if isinstance(x, list)][0]
    loads = gas_loads()
    for s, ld in zip(st, loads):
        ct2 = s.cx2 * math.tan(math.radians(s.alpha2))
        ct3 = s.cx3 * math.tan(math.radians(s.alpha3))
        assert ld["f_theta"] == pytest.approx(ld["m_blade"] * (ct2 + ct3))


# --- the sections ---------------------------------------------------------

def test_every_root_section_has_two_distinct_principal_moments():
    for n in range(1, 6):
        p = root_section_properties(n)
        assert p["i_max"] > p["i_min"] > 0
        assert p["area"] > 0
        assert p["c_min"] > 0 and p["c_max"] > 0


def test_the_root_section_is_the_lowest_published_one():
    """a stated approximation: the 10 % section stands for the root"""
    src = (pathlib.Path(__file__).resolve().parents[1]
           / "solvers/mechanical/gas_bending.py").read_text()
    assert "lowest published; it stands for the root" in src
    assert 'load_section(f"R{stage}", 10)' in src


# --- the closure ----------------------------------------------------------

def test_gas_bending_reproduces_on_all_five_stages():
    worst = max(abs(r["err_pct"]) for r in C)
    assert worst <= BAND_PCT, [(r["stage"], round(r["err_pct"], 1)) for r in C]
    assert worst == pytest.approx(17.7, abs=0.6)


def test_every_stage_is_inside_the_band_not_just_the_mean():
    for r in C:
        assert abs(r["err_pct"]) <= BAND_PCT, r


def test_the_predictions_are_not_all_low_or_all_high():
    """a one-sided error would mean a missing term rather than scatter"""
    signs = {r["err_pct"] > 0 for r in C}
    assert signs == {True, False}


# --- the report's own sentence, as an inequality -------------------------

def test_the_stacking_tilt_cancels_on_every_stage():
    t = the_tilt_cancels()
    assert t["all_hold"] is True
    for r in t["rows"]:
        assert r["resultant"] < r["uncorrected"]
        assert 0 < r["cancelled_pct"] < 100


def test_the_cancellation_is_substantial_not_marginal():
    t = the_tilt_cancels()
    assert t["mean_cancelled_pct"] > 40


def test_the_tilt_angle_itself_is_not_claimed():
    """Table X's own note records tilt as omitted; the LPT table never
    prints it. The cancellation is checked, not reproduced."""
    src = (pathlib.Path(__file__).resolve().parents[1]
           / "solvers/mechanical/gas_bending.py").read_text()
    assert "does not do is reproduce the tilt angle" in src
    assert "inequality" in src


def test_the_summary_reports_both_halves():
    s = summary()
    assert "INSIDE" in s
    assert "the tilt cancels" in s
    assert "holds on all five: True" in s
