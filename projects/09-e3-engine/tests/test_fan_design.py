"""Fan and booster design point (CR-165148), checked against itself,
the published engine data and the laws of thermodynamics."""

from __future__ import annotations

import math
import pathlib

import pytest

yaml = pytest.importorskip("yaml")

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"
GAMMA_EXP = 0.2857


@pytest.fixture(scope="module")
def fan():
    return yaml.safe_load((DATA / "fan-design.yaml").read_text())


@pytest.fixture(scope="module")
def pub():
    return yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())


def eta_from_ratios(pr, tr):
    return (pr ** GAMMA_EXP - 1) / (tr - 1)


def test_requirement_tables_convert(fan):
    for eng in ("fps", "growth"):
        r = fan["requirements"][eng]
        for ms, fts in zip(r["corrected_tip_speed_m_s"], r["corrected_tip_speed_ft_s"]):
            assert abs(ms - fts * 0.3048) < 0.2
        for kg, lb in zip(r["corrected_airflow_kg_s"], r["corrected_airflow_lbm_s"]):
            assert abs(kg - lb * 0.45359) < 0.6
        for si, us in zip(r["specific_flow_kg_s_m2"], r["specific_flow_lbm_s_ft2"]):
            assert abs(si - us * 4.8824) < 1.5
        assert r["core_pressure_ratio"] >= r["bypass_pressure_ratio"]
        assert r["corrected_tip_speed_m_s"] == sorted(r["corrected_tip_speed_m_s"], reverse=True)
    g, f = fan["requirements"]["growth"], fan["requirements"]["fps"]
    assert abs(g["corrected_tip_speed_m_s"][0] / f["corrected_tip_speed_m_s"][0] - 1.11) < 0.005
    assert g["bypass_ratio"][0] < f["bypass_ratio"][0]


def test_design_point_matches_the_published_engine(fan, pub):
    s, p = fan["summary"], pub["fan"]
    assert s["fan_blades"] == p["blade_count"] == 32
    assert fan["flowpath"]["blade_counts_in_figure"]["bypass_ogv"] == p["ogv_count"] == 34
    assert s["corrected_tip_speed_m_s"] == p["corrected_tip_speed_m_s"]
    ap = fan["aero_parameters"]
    assert abs(ap["tip_diameter_cm"][0] - ap["tip_diameter_in"][0] * 2.54) < 0.05
    assert abs(ap["tip_diameter_cm"][1] - ap["tip_diameter_in"][1] * 2.54) < 0.05
    assert abs(s["fan_tip_diameter_m"] * 100 - ap["tip_diameter_cm"][0]) < 0.1


def test_table_iv_converts_and_shares_one_angular_velocity(fan):
    ap = fan["aero_parameters"]
    for ms, fts in zip(ap["tip_speed_m_s"], ap["tip_speed_ft_s"]):
        assert abs(ms - fts * 0.3048) < 0.1
    for kg, lb in zip(ap["airflow_kg_s"], ap["airflow_lb_s"]):
        assert abs(kg - lb * 0.45359) < 0.1
    omega = [v / (d / 200) for v, d in zip(ap["tip_speed_m_s"], ap["tip_diameter_cm"])]
    assert abs(omega[0] - omega[1]) / omega[0] < 0.002, omega
    rpm = omega[0] * 60 / (2 * math.pi)
    assert abs(rpm - fan["vector_diagram_rows"]["corrected_speed_rpm"]) / rpm < 0.002, rpm
    assert ap["number_of_blades"] == [32, 56]


def test_corrected_over_physical_speed_gives_the_design_point_inlet_temperature(fan):
    """N_corr / N_phys = 1/sqrt(theta): at Mach 0.8, 10.7 km, ISA+10 the
    fan-face total temperature is about 258 K."""
    n_corr = fan["vector_diagram_rows"]["corrected_speed_rpm"]
    n_phys = fan["cycle_points"]["case_41_flowpath_and_clearance"]["fan_physical_speed_rpm"][0]
    t2 = 288.15 * (n_phys / n_corr) ** 2
    t_amb = 216.65 + 10 + 2.0  # ISA at 10.67 km is 218.8 K before the +10 day; tropopause 216.65 at 11 km
    t_expected = (218.8 + 10) * (1 + 0.2 * 0.8 ** 2)
    assert abs(t2 - t_expected) / t_expected < 0.02, (t2, t_expected)


def test_flow_splits_close_across_the_island(fan):
    r = fan["vector_diagram_rows"]["rows"]
    total = fan["aero_parameters"]["airflow_kg_s"][0]
    under = r["S1_island"]["inlet_corr_flow_kg_s"]
    assert abs(under - r["R2_booster"]["inlet_corr_flow_kg_s"]) < 0.01
    assert abs(under / total * 100 - fan["summary"]["island_split_pct_of_total_flow"]) < 0.1
    back, core = r["S2OUT_island_exit"]["inlet_corr_flow_kg_s"], r["S2IN_inner_ogv"]["inlet_corr_flow_kg_s"]
    assert abs(back + core - under) < 0.01
    assert abs(back / under * 100 - fan["summary"]["booster_flow_returning_to_bypass_pct"]) < 1.0
    assert abs(r["OGV_bypass"]["inlet_corr_flow_kg_s"] + under - total) < 0.1
    fp = fan["flowpath"]
    assert abs(fp["bypass_flow_kg_s"] - r["OGV_bypass"]["inlet_corr_flow_kg_s"]) < 0.1
    assert abs(fp["booster_return_flow_kg_s"] - back) < 0.1 and abs(fp["core_flow_kg_s"] - core) < 0.1
    for kg, lb in ((fp["bypass_flow_kg_s"], fp["bypass_flow_lbm_s"]), (fp["booster_return_flow_kg_s"], fp["booster_return_flow_lbm_s"]), (fp["core_flow_kg_s"], fp["core_flow_lbm_s"])):
        assert abs(kg - lb * 0.45359) < 0.1
    # bypass ratio: everything that is not core, over core -- the island return joins the bypass
    assert abs((total - core) / core - fan["summary"]["bypass_ratio"]) < 0.05
    assert abs(fp["bypass_ratio_local"] - back / core) < 0.02
    assert abs(r["R1_fan"]["inlet_corr_flow_lbm_s"] * 0.45359 - total) < 0.1


def test_every_row_efficiency_recomputes_from_its_pressure_and_temperature_ratio(fan):
    """eta = (PR^0.2857 - 1)/(TR - 1). The printout carries all three; they
    must agree to a point on every row -- and Table IV's fan row too."""
    for name, r in fan["vector_diagram_rows"]["rows"].items():
        eta = eta_from_ratios(r["pressure_ratio"], r["temperature_ratio"])
        assert abs(eta - r["adiabatic_efficiency"]) < 0.01, (name, eta, r["adiabatic_efficiency"])
    ap = fan["aero_parameters"]
    eta_fan = eta_from_ratios(ap["pressure_ratio"][0], ap["temperature_ratio"][0])
    assert abs(eta_fan - fan["flowpath"]["bypass"]["efficiency"]) < 0.01
    eta_booster = eta_from_ratios(ap["pressure_ratio"][1], ap["temperature_ratio"][1])
    assert 0.7 < eta_booster < 0.8  # the lightly loaded quarter-stage on its own


def test_cumulative_ratios_are_the_table_i_stream_values(fan):
    r = fan["vector_diagram_rows"]["rows"]
    f = fan["requirements"]["fps"]
    assert abs(r["S2IN_inner_ogv"]["pressure_ratio"] - f["core_pressure_ratio"][0]) < 0.01
    assert abs(r["OGV_bypass"]["pressure_ratio"] - f["bypass_pressure_ratio"][0]) < 0.01
    assert abs(r["OGV_bypass"]["adiabatic_efficiency"] * 100 - f["bypass_efficiency_pct"][0]) < 0.15
    assert abs(r["S2IN_inner_ogv"]["adiabatic_efficiency"] * 100 - f["core_efficiency_pct"][0]) < 0.5
    assert r["S1_island"]["pressure_ratio"] < r["R2_booster"]["pressure_ratio"]
    assert abs(fan["flowpath"]["pressure_profile"]["booster_exit_flat"] - r["R2_booster"]["pressure_ratio"]) < 0.002


def test_row_blade_counts_are_the_published_booster_rows(fan, pub):
    r = fan["vector_diagram_rows"]["rows"]
    counts = [r["S1_island"]["blades"], r["R2_booster"]["blades"], r["S2IN_inner_ogv"]["blades"]]
    assert counts == [60, 56, 64]
    text = str(pub)
    assert "60" in text and "56" in text and "64" in text
    assert fan["aero_parameters"]["number_of_blades"][1] == r["R2_booster"]["blades"]


def test_cycle_case_speeds_and_overspeed(fan):
    c = fan["cycle_points"]
    for base, over in zip(c["case_72_max_stress"]["fan_physical_speed_rpm"], c["case_72_max_stress"]["at_1_2pct_overspeed_rpm"]):
        assert abs(over / base - 1.012) < 0.001
    lpt = yaml.safe_load((DATA / "lpt-design.yaml").read_text())["design_cycle_points"]
    assert c["case_41_flowpath_and_clearance"]["fan_physical_speed_rpm"] == lpt["case_41_flowpath_and_clearance"]["fan_physical_speed_rpm"]
    assert c["case_72_max_stress"]["fan_physical_speed_rpm"] == lpt["case_72_max_stress"]["rotor_physical_speed_rpm"]


def test_fan_blade_geometry_from_fig15_is_self_consistent(fan):
    g = fan["fan_rotor_airfoil"]["fig15"]
    assert abs(g["r_sa_od_in"] - g["r_sa_id_in"] - g["blade_height_in"]) < 0.001
    height_cm = g["blade_height_in"] * 2.54
    mean_chord = (g["chord_hub_cm"] + g["chord_tip_cm"]) / 2
    assert abs(height_cm / mean_chord - g["aspect_ratio"]) / g["aspect_ratio"] < 0.04
    nb = g["blades"]
    sol_tip = g["chord_tip_cm"] * nb / (2 * math.pi * g["r_sa_od_in"] * 2.54)
    sol_hub = g["chord_hub_cm"] * nb / (2 * math.pi * g["r_sa_id_in"] * 2.54)
    assert abs(sol_tip - g["solidity_tip"]) < 0.06 and abs(sol_hub - g["solidity_hub"]) < 0.1, (sol_tip, sol_hub)
    assert fan["fan_rotor_airfoil"]["shroud"]["thickness_cm"] == pytest.approx(fan["fan_rotor_airfoil"]["shroud"]["thickness_in"] * 2.54, abs=0.01)
    a = fan["fan_rotor_airfoil"]
    assert a["throat_margin_pct"]["od"] > a["throat_margin_pct"]["typical"] and a["throat_margin_pct"]["id"] > a["throat_margin_pct"]["typical"]
    assert a["tip_section"]["m_le"] > a["shroud_section"]["m_le"] > a["hub_section"]["m_le"]
    assert a["tip_section"]["a_throat_over_a_mouth"] < 1 and a["tip_section"]["a_throat_over_a_exit"] < 1


def test_stator_booster_and_inner_ogv_airfoil_facts(fan):
    s1, b, io = fan["stator1_airfoil"], fan["booster_rotor_airfoil"], fan["inner_ogv_airfoil"]
    assert abs(s1["chord_cm"] - s1["chord_in"] * 2.54) < 0.01
    for k in ("tip", "hub"):
        assert abs(b["chord_cm"][k] - b["chord_in"][k] * 2.54) < 0.01
    for k in ("od", "id"):
        assert abs(io["chord_cm"][k] - io["chord_in"][k] * 2.54) < 0.01
    assert s1["vanes"] == 60 and b["blades"] == 56 and io["vanes"] == 64
    rows = fan["vector_diagram_rows"]["rows"]
    assert (s1["vanes"], b["blades"], io["vanes"]) == (rows["S1_island"]["blades"], rows["R2_booster"]["blades"], rows["S2IN_inner_ogv"]["blades"])
    assert abs(b["aspect_ratio_text"] - b["aspect_ratio_table_iv"]) < 0.05  # the recorded pair
    assert abs(b["aspect_ratio_table_iv"] - fan["aero_parameters"]["aspect_ratio"][1]) < 0.001
    assert b["tm_c"]["hub"] > b["tm_c"]["tip"] and s1["od"]["tm_c"] > s1["id"]["tm_c"]
    assert b["chord_cm"]["hub"] > b["chord_cm"]["tip"] and io["chord_cm"]["id"] > io["chord_cm"]["od"]
    # booster hub pressure ratio requirement is the flat 1.683 of Fig.3
    assert abs(b["hub"]["pressure_ratio_required"] - fan["flowpath"]["pressure_profile"]["booster_exit_flat"]) < 0.01
    assert fan["bypass_ogv_vane_frame"]["vanes"] == fan["flowpath"]["blade_counts_in_figure"]["bypass_ogv"]


KSI_TO_KN_CM2 = 0.689476


def kn_ksi_ok(kn, ksi, tol=0.12):
    return abs(kn - ksi * KSI_TO_KN_CM2) < tol


def test_fan_dovetail_and_post_convert_and_sit_under_their_limits(fan):
    d = fan["fan_rotor_mechanical"]["dovetail_and_post"]
    b, p = d["blade"], d["post"]
    for cm, inch in ((b["axial_length_cm"], b["axial_length_in"]), (b["shank_thickness_cm"], b["shank_thickness_in"]), (b["flank_width_cm"], b["flank_width_in"]), (p["minimum_width_cm"], p["minimum_width_in"]), (b["offsets_cm"]["axial"], b["offsets_in"]["axial"]), (b["offsets_cm"]["tangential"], b["offsets_in"]["tangential"])):
        assert abs(cm - inch * 2.54) < 0.05, (cm, inch)  # 16.3 cm is printed to one decimal
    assert kn_ksi_ok(b["crush_stress_kN_cm2"], b["crush_stress_ksi"]) and kn_ksi_ok(b["lcf_limit_kN_cm2"], b["lcf_limit_ksi"]) and kn_ksi_ok(p["lcf_limit_kN_cm2"], p["lcf_limit_ksi"])
    for part in (b, p):
        for k, kn in part["corner_stresses_kN_cm2"].items():
            assert kn_ksi_ok(kn, part["corner_stresses_ksi"][k]), (k, kn)
        assert max(part["corner_stresses_kN_cm2"].values()) < part["lcf_limit_kN_cm2"]
    assert b["lcf_cycles"] == p["lcf_cycles"] == fan["summary"]["life"]["missions"] * fan["summary"]["life"]["stress_cycles_per_mission"]
    assert max(p["corner_stresses_kN_cm2"].values()) < max(b["corner_stresses_kN_cm2"].values())  # the post is the stronger part


def test_fan_blade_campbell_margin_recomputes(fan):
    c = fan["fan_rotor_mechanical"]["campbell"]
    two_per_rev = 2 * c["max_speed_rpm"] / 60
    margin = (c["modes_Hz"]["first_flex"]["at_3653_lowest_in_phase"] / two_per_rev - 1) * 100
    assert abs(margin - c["first_flex_margin_over_2_per_rev_pct"]) < 1.5, margin
    assert c["first_flex_margin_over_2_per_rev_pct"] < c["goal_margin_pct"]  # 14.6 against 15, as printed
    st = fan["fan_rotor_mechanical"]["steady_stress"]
    assert kn_ksi_ok(st["max_effective_kN_cm2"], st["max_effective_ksi"]) and kn_ksi_ok(st["concave_peak_kN_cm2"], st["concave_peak_ksi"])
    sh = fan["fan_rotor_mechanical"]["shroud"]
    assert kn_ksi_ok(sh["fillet_stress_kN_cm2"], sh["fillet_stress_ksi"])
    assert abs(sh["contact_stress_N_cm2"] - sh["contact_stress_psi"] * 0.689476) < 1.0
    assert abs(sh["length_cm"] - sh["length_in"] * 2.54) < 0.01
    for w in ("left_wing", "right_wing"):
        assert abs(sh["tip_deflection_cm"][w] - sh["tip_deflection_in"][w] * 2.54) < 0.002
    assert sh["span_pct"] == fan["summary"]["part_span_shroud_height_pct"]
    assert abs(sh["flexural_displacement_vector_deg"]["first_flex"] - sh["shroud_angle_deg"]) < 2


def test_booster_blade_mechanical_converts(fan):
    b = fan["booster_blade_mechanical"]
    d = b["dovetail"]
    for cm, inch in ((d["length_cm"], d["length_in"]), (d["shank_thickness_cm"], d["shank_thickness_in"]), (d["flank_width_cm"], d["flank_width_in"]), (d["offsets_cm"]["axial"], d["offsets_in"]["axial"]), (d["offsets_cm"]["tangential"], d["offsets_in"]["tangential"])):
        assert abs(cm - inch * 2.54) < 0.006, (cm, inch)
    assert kn_ksi_ok(d["crush_stress_kN_cm2"], d["crush_stress_ksi"])
    for kn, ksi in zip(d["corner_stresses_kN_cm2"], d["corner_stresses_ksi"]):
        assert kn_ksi_ok(kn, ksi)
    fd = fan["fan_rotor_mechanical"]["dovetail_and_post"]["blade"]
    assert d["crush_stress_kN_cm2"] < fd["crush_stress_kN_cm2"]  # the lightly loaded stage
    c = b["campbell"]
    assert c["forcing"]["stator_passing_per_rev"] == fan["stator1_airfoil"]["vanes"] == 60
    f60 = 60 * c["max_speed_rpm"] / 60
    assert c["modes_Hz"]["third_flex"] < f60 < c["modes_Hz"]["third_torsion"]
    assert c["modes_Hz"]["first_flex"]["at_3653"] > 2 * 2 * c["max_speed_rpm"] / 60
    assert b["airfoil_stress"]["rpm"] == 3635 and c["max_speed_rpm"] == 3653  # the recorded pair of speeds
    g = b["geometry"]
    assert g["tm_c_pct"] == sorted(g["tm_c_pct"], reverse=True) and g["camber_deg"] == sorted(g["camber_deg"], reverse=True)
    assert abs(g["chord_in"][0] - fan["booster_rotor_airfoil"]["chord_in"]["hub"]) < 0.01 and abs(g["chord_in"][-1] - fan["booster_rotor_airfoil"]["chord_in"]["tip"]) < 0.01


def test_rotor_structure_pairs_convert_and_the_disk_has_margin(fan):
    r = fan["rotor_structure"]
    fd = r["fan_disk"]
    bad = [(kn, ksi) for kn, ksi in fd["stresses_kN_cm2_ksi"] if not kn_ksi_ok(kn, ksi)]
    assert bad == [], bad
    for cm, inch in fd["deflections_cm_in"]:
        assert abs(cm - inch * 2.54) < 0.0026, (cm, inch)
    assert fd["max_stress_kN_cm2"] == max(kn for kn, _ in fd["stresses_kN_cm2_ksi"])
    assert fd["burst_strength_pct_of_design_speed"] > 120 and fd["max_stress_pct_of_lcf_limit"] < 100
    bs = r["booster_spool"]
    bad = [(kn, ksi) for kn, ksi in bs["stresses_kN_cm2_ksi"] if not kn_ksi_ok(kn, ksi)]
    assert bad == [(11.5, 17)], bad
    for cm, inch in bs["deflections_cm_in"]:
        assert abs(cm - inch * 2.54) < 0.0016, (cm, inch)
    j = r["disk_shaft_joint"]
    assert abs(j["preload_kN_per_bolt"] - j["preload_lb_per_bolt"] * 0.00444822) < 0.05
    assert j["bolts"] == 30 and j["bolt_size_in"] == fan["materials"]["fan_shaft_bolts"]["size_in"]


def test_fps_fan_weight_adds_in_both_units(fan):
    w = fan["fps_weight"]
    assert abs(sum(w["items_kg"].values()) - w["total_kg"]) < 0.05
    assert sum(w["items_lb"].values()) == w["total_lb"]
    for k, kg in w["items_kg"].items():
        assert abs(kg - w["items_lb"][k] * 0.45359) < 0.3, k
    assert abs(w["total_kg"] - w["total_lb"] * 0.45359) < 0.3
    per_fan_blade = w["items_kg"]["fan_blades"] / fan["summary"]["fan_blades"]
    per_booster_blade = w["items_kg"]["booster_blades"] / fan["aero_parameters"]["number_of_blades"][1]
    assert 6 < per_fan_blade < 8.5 and 0.2 < per_booster_blade < 0.4
    assert w["items_kg"]["fan_blades"] / w["total_kg"] > 0.45


def test_stator_geometry_table_vii(fan):
    g = fan["fan_stator"]["geometry"]
    for row in g["rows"]:
        assert abs(row["length_cm"] - row["length_in"] * 2.54) < 0.03, row["stator"]
        assert abs(row["chord_root_cm"] - row["chord_root_in"] * 2.54) < 0.01, row["stator"]
        assert abs(row["chord_tip_cm"] - row["chord_tip_in"] * 2.54) < 0.01, row["stator"]
    s1, io, bp = g["rows"]
    assert (s1["vanes"], io["vanes"], bp["vanes"]) == (60, 64, 34)
    assert abs(s1["length_cm"] / ((s1["chord_root_cm"] + s1["chord_tip_cm"]) / 2) - s1["aspect_ratio"]) < 0.02
    assert abs(s1["chord_root_cm"] - fan["stator1_airfoil"]["chord_cm"]) < 0.05
    assert abs(io["chord_root_cm"] - fan["inner_ogv_airfoil"]["chord_cm"]["id"]) < 0.01 and abs(io["chord_tip_cm"] - fan["inner_ogv_airfoil"]["chord_cm"]["od"]) < 0.01
    assert s1["tm_c_root_as_printed"] == 0.485 and abs(s1["tm_c_root_taken"] - fan["fan_stator"]["fig75_stage1_tm_c"]["root"]) < 0.002
    assert s1["tm_c_tip"] == fan["fan_stator"]["fig75_stage1_tm_c"]["tip"]
    assert fan["fan_stator"]["materials_icls"]["stage1_vanes"] == s1["material_icls"]
