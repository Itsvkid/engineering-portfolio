"""The ICLS as-tested numbers (CR-168211), checked against themselves and
against the design intent in the published file."""

from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"
KG_HN_TO_LB_HLBF = 9.80665  # kg/(h.N) x 9.807 = lbm/(h.lbf)


@pytest.fixture(scope="module")
def icls():
    return yaml.safe_load((DATA / "icls-tested.yaml").read_text())


@pytest.fixture(scope="module")
def pub():
    return yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())


def test_every_sfc_pair_converts(icls):
    m = icls["measured_sfc"]["sls_rated_thrust"]
    for kg, lb in ((m["as_tested_kg_hN"], m["as_tested_lb_hlbf"]), (m["corrected_for_test_faults_kg_hN"], m["corrected_for_test_faults_lb_hlbf"]), (m["fully_corrected_kg_hN"], m["fully_corrected_lb_hlbf"])):
        assert abs(kg * KG_HN_TO_LB_HLBF - lb) < 0.002, (kg, lb)
    c = icls["cycle_characteristics"]
    assert abs(c["sfc_max_cruise_bare_kg_hN"] * KG_HN_TO_LB_HLBF - c["sfc_max_cruise_bare_lb_hlbf"]) < 0.002
    assert abs(c["sfc_max_cruise_installed_kg_hN"] * KG_HN_TO_LB_HLBF - c["sfc_max_cruise_installed_lb_hlbf"]) < 0.002
    x = icls["measured_sfc"]["max_cruise_projected"]
    assert abs(x["uninstalled_kg_hN"] * KG_HN_TO_LB_HLBF - x["uninstalled_lb_hlbf"]) < 0.002
    # mg/(N.s) x 3.6 = g/(N.h) = kg/(h.N) x 1000
    assert abs(m["as_tested_mg_Ns"] * 3.6 / 1000 - m["as_tested_kg_hN"]) < 0.0002
    assert abs(m["fully_corrected_mg_Ns"] * 3.6 / 1000 - m["fully_corrected_kg_hN"]) < 0.0002
    assert abs(x["uninstalled_mg_Ns"] * 3.6 / 1000 - x["uninstalled_kg_hN"]) < 0.0002
    assert abs(m["as_tested_mg_Ns"] / m["predicted_mg_Ns"] - 1 - m["above_prediction_pct"] / 100) < 0.002
    assert m["as_tested_kg_hN"] > m["corrected_for_test_faults_kg_hN"] > m["fully_corrected_kg_hN"]


def test_thrust_converts_and_exceeds_design(icls):
    t = icls["measured_sfc"]["takeoff_thrust"]
    kn = t["achieved_corrected_kg"] * 9.80665 / 1000
    assert abs(kn - t["achieved_corrected_lbf"] * 0.00444822) < 0.3
    design = icls["measured_sfc"]["sls_rated_thrust"]["thrust_kN"]
    assert abs(kn / design - 1 - t["above_design_pct"] / 100) < 0.002
    assert abs(design - icls["measured_sfc"]["sls_rated_thrust"]["thrust_lbf"] * 0.00444822) < 0.1
    assert abs(icls["cycle_characteristics"]["design_thrust_kN"] - design) < 1


def test_sfc_stackup_sums_to_the_measured_excess(icls):
    s = icls["sfc_stackup_at_takeoff"]
    assert abs(sum(s["sfc_pct"]) - s["total_pct"]) < 0.001
    assert s["total_pct"] == icls["measured_sfc"]["sls_rated_thrust"]["above_prediction_pct"]
    assert max(s["sfc_pct"]) == 1.0 and s["component"][s["sfc_pct"].index(1.0)] == "exhaust"


def test_cruise_improvement_arithmetic(icls):
    x = icls["measured_sfc"]["max_cruise_projected"]
    assert x["improvement_over_cf6_50c_installed_pct"] - x["objective_pct"] == pytest.approx(x["objective_exceeded_by_pct"], abs=0.01)
    assert x["improvement_over_cf6_50c_installed_pct"] > x["improvement_over_cf6_50c_uninstalled_pct"] > x["objective_pct"]
    cf6 = x["uninstalled_mg_Ns"] / (1 - x["improvement_over_cf6_50c_uninstalled_pct"] / 100)
    assert 17 < cf6 < 18.5  # a CF6-50C at 0.62-0.65 lb/h/lbf


def test_measured_against_design_intent(icls, pub):
    c = icls["cycle_characteristics"]
    assert abs(c["cycle_pressure_ratio_max_climb"] - pub["cycle"]["max_climb"]["overall_pressure_ratio"]) < 0.5 if "cycle" in pub else True
    comp = icls["component_results"]
    # the ICLS's measured fan and HPC efficiencies sit within a point of the FPS requirements in the published file
    fan_goal = pub["fan"]["efficiency"]["bypass"]["max_cruise"]
    assert abs(comp["fan"]["bypass_efficiency"] - fan_goal) < 0.012
    assert abs(comp["fan"]["hub_and_booster_efficiency"] - pub["fan"]["efficiency"]["hub_and_booster"]["max_cruise"]) < 0.012
    assert comp["compressor"]["pressure_ratio"] == pub["hpc"]["design_pressure_ratio_operating_line"]
    assert comp["compressor"]["stages"] == pub["hpc"]["stages"]
    assert comp["hp_turbine"]["efficiency"] - comp["hp_turbine"]["goal"] == pytest.approx(comp["hp_turbine"]["over_goal_pct"] / 100, abs=0.0005)
    assert abs(c["t41_sls_warm_day_takeoff_F"] - (c["t41_sls_warm_day_takeoff_C"] * 1.8 + 32)) < 1
    assert c["bypass_ratio_max_climb"] == 6.8 and c["fan_pressure_ratio_max_climb"] == 1.65
    # the FPS cycle's own installed cruise sfc is the ICLS-technology number, not the FPS goal
    assert c["sfc_max_cruise_installed_kg_hN"] > pub["cycle"]["max_cruise"]["sfc_kg_per_N_hr"] if "cycle" in pub else True


def test_lpt_deficit_and_the_two_disagreements_are_recorded(icls):
    lpt = icls["component_results"]["lp_turbine"]
    assert lpt["efficiency_vs_goal_pct"] < 0 and min(lpt["efficiency_vs_rig_points"]) < lpt["efficiency_vs_goal_pct"]
    assert "unexplained" in lpt["verdict"]
    assert icls["component_results"]["fan"]["hub_over_goal_pct_summary"] != icls["component_results"]["fan"]["hub_over_goal_pct_conclusions"]
    assert icls["component_results"]["mixer"]["effectiveness_over_model_summary_pct"] == 8
    assert "0.332" in icls["measured_sfc"]["sls_rated_thrust"]["as_printed"]


def test_performance_curves_are_monotonic_where_physics_says_so(icls):
    p = icls["performance_curves"]
    assert p["epr_vs_fan_speed"]["epr"] == sorted(p["epr_vs_fan_speed"]["epr"])
    assert p["bpr_vs_fan_speed"]["bpr"] == sorted(p["bpr_vs_fan_speed"]["bpr"], reverse=True)
    assert p["core_vs_fan_speed"]["core_speed_pct"] == sorted(p["core_vs_fan_speed"]["core_speed_pct"])
    assert p["core_pumping"]["pressure_ratio"] == sorted(p["core_pumping"]["pressure_ratio"])
    assert p["compressor_efficiency"]["efficiency"] == sorted(p["compressor_efficiency"]["efficiency"])
    s = p["sfc_vs_thrust"]
    i_min = s["sfc_mg_Ns"].index(min(s["sfc_mg_Ns"]))
    assert 50 < s["thrust_kN"][i_min] < 100  # the bucket
    assert abs(s["sfc_mg_Ns"][-1] - icls["measured_sfc"]["sls_rated_thrust"]["as_tested_mg_Ns"]) < 0.1
    # BPR 7.3 at the top of the fan speed range on the stand vs 6.8 at the max-climb design point in flight
    assert p["bpr_vs_fan_speed"]["bpr"][-1] > icls["cycle_characteristics"]["bypass_ratio_max_climb"]
