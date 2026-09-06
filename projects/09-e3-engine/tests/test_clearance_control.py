"""Stage D unit D4: active clearance control
(solvers/thermal/STEP0.md unit D4)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from thermal.clearance import (  # noqa: E402
    blade_heights_cm, cruise_clearance_two_routes, payoff_rows, transient,
)

ROWS, PAYOFF = payoff_rows()
TWO_ROUTES = cruise_clearance_two_routes()
TR, DC = transient()
D4_BAND_PCT_SPAN = 0.2


@pytest.mark.parametrize("i", range(3))
def test_each_payoff_row_recomputes(i):
    """finding 67: d_eta = clearance reduction x sensitivity"""
    r = ROWS[i]
    assert abs(r.d_eta_recomputed_pct - r.d_eta_printed_pct) < 0.02


def test_the_payoff_total_recomputes():
    total = sum(r.d_eta_recomputed_pct for r in ROWS)
    assert abs(total - PAYOFF["d_eta_total_pct"]) < 0.02


def test_the_sfc_line_closes_exactly():
    assert abs(PAYOFF["d_sfc_from_eta_pct"] + PAYOFF["d_sfc_fan_air_pct"]
               - PAYOFF["d_sfc_net_pct"]) < 1e-9
    assert PAYOFF["d_sfc_net_pct"] < -1.0
    assert PAYOFF["fan_air_pct_w25"] < 0.2


def test_acc_is_worth_more_than_a_point_of_sfc_for_a_sixth_of_a_percent_of_flow():
    assert abs(PAYOFF["d_sfc_net_pct"]) > 1.0
    assert PAYOFF["fan_air_pct_w25"] <= 0.15


@pytest.mark.parametrize("i", (0, 1))
def test_the_cruise_clearance_closes_by_two_routes(i):
    """finding 68: Table III's percent of span against section 4's cm"""
    r = TWO_ROUTES[i]
    assert abs(r["difference_pct_of_span"]) < D4_BAND_PCT_SPAN
    assert abs(r["difference_pct_of_span"]) < 0.05      # met with 4x to spare


def test_the_two_routes_come_from_different_chapters():
    for r in TWO_ROUTES:
        assert r["printed_pct_of_span"] in (1.0, 0.6)
        assert abs(r["desired_cm"] - 0.041) < 1e-9
        assert 4.0 < r["height_cm"] < 7.5


def test_blade_heights_come_from_the_dimensioned_figure():
    h = blade_heights_cm()
    assert abs(h["stage1"] - 4.27) < 0.01
    assert abs(h["stage2"] - 6.98) < 0.01


def test_the_transient_has_the_published_shape():
    """finding 69: the pinch is the tightest point, the casing peak the
    widest, and ACC brings cruise below the no-ACC value"""
    s1 = TR["stage1_tip"]
    assert s1["takeoff_pinch"] < s1["max_climb_clearance_no_acc"]
    assert s1["casing_peak_no_acc"] > s1["max_climb_clearance_no_acc"]
    assert s1["cruise_running_clearance_with_acc"] < s1["cruise_clearance_no_acc"]
    assert s1["cruise_running_clearance_with_acc"] < s1["takeoff_pinch"]


def test_the_interstage_seal_rubs_at_takeoff_by_design():
    assert TR["interstage_seal"]["takeoff_rub"] < 0
    assert "rub" in DC["interstage_seal"]


def test_the_takeoff_clearance_misprint_is_recorded():
    assert abs(DC["takeoff_tip_clearance_both_stages_cm"] - 0.064) < 1e-9
    assert "0.64" in DC["as_printed"]
