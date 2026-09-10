"""Stage K unit K2: growth margin on the FPS hardware
(solvers/growth/STEP0.md unit K2)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from growth.margins import (  # noqa: E402
    GROWTH_CLAIM, in_scope, regrown, speed_cross_check, speed_ratios,
    spool_of, summary, verdict,
)


# --- the speed ratio is read, not assumed --------------------------------

def test_the_speed_ratio_comes_from_two_printed_tip_speeds():
    s = speed_ratios()
    assert len(s) == 3
    assert s[0]["fps_m_s"] == 411.5 and s[0]["growth_m_s"] == 457.2
    assert s[0]["speed_ratio"] == pytest.approx(1.1111, abs=0.001)
    assert s[0]["stress_ratio"] == pytest.approx(1.2344, abs=0.001)


def test_two_published_statements_about_the_lp_speed_agree():
    """the tip-speed ratio against the separately printed booster increase"""
    c = speed_cross_check()
    assert c["printed_pct"] == 11
    assert c["agree_within_pct"] < 0.5, c


def test_stress_scales_as_the_square_of_speed():
    for s in speed_ratios():
        assert s["stress_ratio"] == pytest.approx(s["speed_ratio"] ** 2)


def test_every_rating_speeds_the_spool_up():
    for s in speed_ratios():
        assert s["speed_ratio"] > 1.0


# --- scope: six LP parts in, eleven HP parts out -------------------------

def test_the_seventeen_rows_split_six_and_eleven():
    sc = in_scope()
    assert len(sc["lp"]) == 6
    assert len(sc["hp"]) == 11
    assert len(sc["lp"]) + len(sc["hp"]) == 17


def test_the_hp_parts_are_excluded_with_a_reason():
    sc = in_scope()
    assert "no growth HP-spool speed is published" in sc["hp_excluded_because"]


def test_the_hpt_dovetail_at_exactly_one_is_out_of_scope():
    """the most interesting row in F1's table, and this unit cannot touch it"""
    sc = in_scope()
    hpt = [r for r in sc["hp"] if "HPT stage-1 disk dovetail" in r["part"]]
    assert len(hpt) == 1
    assert hpt[0]["margin"] == pytest.approx(1.0)
    assert spool_of("HPT stage-1 disk dovetail") == "hp"


def test_the_fan_and_lpt_are_both_low_spool():
    for p in ("fan disk, max", "LPT blade retainer 3"):
        assert spool_of(p) == "lp"


# --- the result -----------------------------------------------------------

def test_the_fan_parts_keep_margin_at_growth_speed():
    """the parts the claim is actually about"""
    g = regrown(1)
    fan = [r for r in g["rows"] if r["covered_by_claim"]]
    assert len(fan) == 3
    for r in fan:
        assert r["survives"] is True, r["part"]
    assert min(r["growth_margin"] for r in fan) == pytest.approx(1.037, abs=0.01)


def test_the_lpt_retainers_do_not():
    g = regrown(1)
    ret = [r for r in g["rows"] if not r["covered_by_claim"]]
    assert len(ret) == 3
    for r in ret:
        assert r["survives"] is False, r["part"]
    assert max(r["growth_margin"] for r in ret) < 0.85


def test_the_claim_holds_exactly_where_it_applies():
    v = verdict(1)
    assert v["claim_holds_where_it_applies"] is True
    assert v["covered_all_survive"] is True
    assert v["not_covered_all_survive"] is False


def test_the_claim_is_about_hub_radii_not_retainers():
    assert GROWTH_CLAIM["value"] is True
    assert len(GROWTH_CLAIM["covers"]) == 3
    assert all("fan" in p for p in GROWTH_CLAIM["covers"])
    assert all("retainer" in p for p in GROWTH_CLAIM["does_not_cover"])
    assert "not a hub radius" in GROWTH_CLAIM["why"]


def test_the_worst_rating_takes_even_a_fan_part_under():
    """rating 3 has the largest speed ratio, 1.1525"""
    g = regrown(3)
    assert g["stress_ratio"] == pytest.approx(1.3283, abs=0.001)
    failing = [r for r in g["rows"] if not r["survives"]]
    assert len(failing) == 4
    assert any(r["covered_by_claim"] for r in failing)


# --- what the result is NOT ----------------------------------------------

def test_the_result_is_declared_a_bound_not_a_prediction():
    v = verdict(1)
    assert v["is_a_bound"] is True
    assert "centrifugal dominance" in v["bound_note"]
    assert "E8" in v["bound_note"]


def test_stress_margin_is_not_confused_with_life():
    v = verdict(1)
    assert "72,000 cycles" in v["life_caveat"]
    assert "does not mean that life is still met" in v["life_caveat"]


def test_the_summary_reports_both_halves_and_the_exclusion():
    s = summary()
    assert "NOT covered" in s and "covered" in s
    assert "Out of scope" in s
    assert "BOUND, not a prediction" in s
