"""C1 unit 2: the Ainley-Mathieson loss model against R&M 2974's own
worked example (solvers/meanline/STEP0.md, unit 2). Bands from the chart
read-off uncertainty and the report's stated accuracy."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from meanline import losses as L  # noqa: E402

EX = L.AM["worked_example"]
ST, RO = EX["stator"], EX["rotor"]


def test_outlet_angles():
    assert abs(L.alpha2_star(ST["acos_o_over_s_deg"]) - 62.4) < 0.6
    assert abs(L.outlet_angle_low_mach(ST["o_over_s"], ST["s_over_e"]) - 63.5) < 0.6
    assert abs(L.alpha2_star(RO["acos_o_over_s_deg"]) - 47.2) < 0.6
    assert abs(L.outlet_angle_low_mach(RO["o_over_s"], RO["s_over_e"]) - 48.6) < 0.6
    assert abs(L.outlet_angle_with_clearance(48.6, 36.0, RO["k_over_h"]) - 47.3) < 0.6


def test_stator_profile_loss():
    """inside the band, but the largest deviation of the unit: my read of
    Fig 4a at 63.5 deg, s/c 0.739 is 0.0044 above the authors' 0.0288
    (STEP0 unit 2, observation 1)"""
    y = L.yp_nozzle(63.5, ST["s_over_c"])
    assert abs(y - ST["results"]["Yp"]) < 0.005
    assert 0.003 < y - ST["results"]["Yp"] < 0.005


def test_rotor_profile_loss():
    r = RO["results"]
    assert abs(L.yp_nozzle(48.6, RO["s_over_c"]) - r["Yp_beta1_zero"]) < 0.005
    assert abs(L.yp_impulse(48.6, RO["s_over_c"]) - r["Yp_impulse"]) < 0.005
    assert abs(L.yp_zero_incidence(36.0, 48.6, RO["s_over_c"], RO["t_over_c"]) - r["Yp_zero_incidence"]) < 0.005


def test_stalling_incidence():
    assert abs(L.stalling_incidence(36.0, 48.6, RO["s_over_c"]) - RO["results"]["stalling_incidence_deg"]) < 1.5


def test_secondary_factors_at_zero_incidence():
    r = RO["results"]
    ysk, f = L.secondary_and_clearance(36.0, 48.6, 61.85, 61.85, 9.5 / 13, RO["k_over_h"], beta1=36.0)
    assert abs(f["cl_sc"] / 3.65 - 1) < 0.01 and abs(f["geo"] / 0.465 - 1) < 0.01
    assert abs(f["x"] - r["lambda_x"]) < 0.005 and abs(f["lam"] - r["lambda"]) < 0.0008
    assert abs(ysk / RO["results"]["incidence_table"]["Ys_plus_Yk"][3] - 1) < 0.05
    ysk_s, f_s = L.secondary_and_clearance(0.0, 63.5, 61.85, 61.85, 9.5 / 13, 0.0)
    assert abs(f_s["cl_sc"] / 2.83 - 1) < 0.01 and abs(f_s["geo"] / 0.566 - 1) < 0.01
    assert abs(ysk_s / ST["results"]["Ys_plus_Yk"] - 1) < 0.06


@pytest.mark.parametrize("k", range(6))
def test_rotor_total_loss_table(k):
    tab = RO["results"]["incidence_table"]
    r = L.row_total_loss(36.0, 36.0 + tab["i_deg"][k], 48.6, RO["s_over_c"], RO["t_over_c"], RO["te_over_s"], 61.85, 61.85, 9.5 / 13, RO["k_over_h"])
    assert abs(r["yt"] - tab["Yt_corrected"][k]) < 0.015, (tab["i_deg"][k], r["yt"])


def test_te_factor():
    assert abs(L.te_factor(0.01) - RO["results"]["te_factor"]) < 0.02


SC = EX["stage_characteristic"]


@pytest.mark.parametrize("k", range(4))
def test_stage_pressure_ratio(k):
    r = L.worked_example_stage(SC["W_sqrtT_over_P_lb_sqrtK_s_psi"][k])
    assert abs(r["pr"] - SC["P3_over_P1"][k]) < 0.015


@pytest.mark.parametrize("k", range(4))
def test_stage_efficiency(k):
    r = L.worked_example_stage(SC["W_sqrtT_over_P_lb_sqrtK_s_psi"][k])
    assert abs(r["eta"] * 100 - SC["efficiency_pct"][k]) < 2.0, (k, r["eta"], r["i"])


def test_choking_flow():
    assert abs(L.worked_example_choking_flow() / SC["choking_flow"] - 1) < 0.02


def test_euler_and_energy_agree():
    r = L.worked_example_stage(8.0)
    assert abs(r["dt"] / r["euler_dt"] - 1) < 0.01
