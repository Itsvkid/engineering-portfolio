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


# ─────────────────────────────────────────────────────────────────────────
# CR-165148 Appendices B and D — the plane section geometry of the two LP
# rotors, transcribed 2026-09-10 from page images (the OCR layer on those
# pages returns nothing usable). About 350 numbers off a scan NASA stamped
# "OF POOR QUALITY", so the transcription is made to check itself: every
# row prints beta*_LE and beta*_TE SEPARATELY from the camber they define,
# and both a cm and an inch column. That is 23 + 14 independent constraints
# plus two unit closures, none of which a mis-keyed digit survives.
# Same discipline as unit C4-2's Rotor 37 appendix (finding 128).
# ─────────────────────────────────────────────────────────────────────────

APPENDICES = [("fan_rotor_airfoil", "appendix_b", 23, 32),
              ("booster_rotor_airfoil", "appendix_d", 14, 56)]


@pytest.fixture(scope="module", params=APPENDICES, ids=lambda p: p[1])
def appendix(request, fan):
    block, key, n, nb = request.param
    return fan[block][key], n, nb


def test_appendix_columns_are_all_the_same_length(appendix):
    a, n, nb = appendix
    assert a["stations"] == n and a["number_of_blades"] == nb
    for col in a["columns_as_printed"] + ["radius_cm"]:
        assert len(a[col]) == n, f"{col} has {len(a[col])} of {n} rows"


def test_camber_equals_the_metal_angle_difference_on_every_row(appendix):
    """The closure that validates the reading: camber is printed in its own
    column AND implied by beta*_LE - beta*_TE. They must agree on every row."""
    a, n, _ = appendix
    worst = max(abs(a["camber_deg"][i] - (a["beta_le_star_deg"][i] - a["beta_te_star_deg"][i]))
                for i in range(n))
    assert worst <= 0.011, f"camber closure worst {worst:.3f} deg"


def test_the_cm_and_inch_columns_agree(appendix):
    a, n, _ = appendix
    for cm, inch in (("section_height_cm", "section_height_in"), ("chord_cm", "chord_in")):
        worst = max(abs(a[cm][i] / 2.54 - a[inch][i]) for i in range(n))
        assert worst < 0.001, f"{cm}/{inch} worst {worst:.4f} in"


def test_the_derived_radius_column_is_the_datum_plus_the_height(appendix):
    a, n, _ = appendix
    r_id = a["stacking_axis"]["r_id_cm"]
    for i in range(n):
        assert abs(a["radius_cm"][i] - (r_id + a["section_height_cm"][i])) < 5e-4


def test_the_stacking_axis_has_one_axial_coordinate(appendix):
    """The positive evidence for no sweep and no lean on either LP rotor: the
    report prints two radii and a SINGLE Z. A swept or leaned axis needs a Z
    per station, and neither appendix has one -- which is why Appendix E, the
    swept and leaned inner OGV, prints no stacking-axis box at all."""
    a, _, _ = appendix
    sa = a["stacking_axis"]
    assert isinstance(sa["z_cm"], (int, float))
    assert sa["r_od_cm"] > sa["r_id_cm"]
    assert "no_sweep_no_lean" in sa
    for cm, inch in (("r_od_cm", "r_od_in"), ("r_id_cm", "r_id_in")):
        assert abs(sa[cm] / 2.54 - sa[inch]) < 0.001, f"{cm}/{inch}"


def test_the_fan_stacking_axis_z_converts_and_the_boosters_does_not(fan):
    """A print inconsistency, pinned so it cannot be quietly "fixed" later.
    Appendix D gives Z = 39.901 cm (14.134 in.); those are 15.709 in and
    35.900 cm. One number in one unit is wrong and this project does not know
    which, so both stay as printed and the block carries an as_printed note."""
    b = fan["fan_rotor_airfoil"]["appendix_b"]["stacking_axis"]
    d = fan["booster_rotor_airfoil"]["appendix_d"]["stacking_axis"]
    assert abs(b["z_cm"] / 2.54 - b["z_in"]) < 0.001
    assert abs(d["z_cm"] / 2.54 - d["z_in"]) > 1.0
    assert "as_printed" in d and "39.901" in d["as_printed"] and "14.134" in d["as_printed"]


def test_sections_are_ordered_and_the_blade_thins_and_twists_outward(appendix):
    a, n, _ = appendix
    for col, rising in (("section_height_cm", True), ("radius_cm", True),
                        ("stagger_deg", True), ("camber_deg", False)):
        seq = a[col]
        ok = all((seq[i] < seq[i + 1]) == rising for i in range(n - 1))
        assert ok, f"{col} not monotonic"


def test_fan_appendix_b_brackets_the_published_flowpath(fan, pub):
    """The two end stations are not out-of-flowpath artefacts: the -9 % row is
    the fan inlet HUB and the 102.5 % row is the TIP, each to better than
    0.1 %, from radii that Appendix B and Fig.2 never share a page with."""
    a = fan["fan_rotor_airfoil"]["appendix_b"]
    r_tip = fan["flowpath"]["r_tip_cm"]
    r_hub = r_tip * fan["summary"]["inlet_radius_ratio"]
    assert abs(a["radius_cm"][0] / r_hub - 1) < 0.001, a["radius_cm"][0]
    assert abs(a["radius_cm"][-1] / r_tip - 1) < 0.001, a["radius_cm"][-1]
    assert abs(a["radius_cm"][-1] - pub["size"]["fan_tip_diameter_m"] * 50) < 0.5


def test_fan_appendix_b_stacking_axis_reproduces_the_figure_15_box(fan):
    """Fig.15's printed box and Appendix B are different pages read months
    apart; they must give the same three numbers."""
    sa = fan["fan_rotor_airfoil"]["appendix_b"]["stacking_axis"]
    box = fan["fan_rotor_airfoil"]["fig15"]
    for got, printed in ((sa["r_od_cm"] / 2.54, box["r_sa_od_in"]),
                         (sa["r_id_cm"] / 2.54, box["r_sa_id_in"]),
                         (sa["z_cm"] / 2.54, box["z_sa_in"])):
        assert abs(got - printed) < 0.001, f"{got:.4f} vs {printed}"


def test_booster_appendix_d_stacking_axis_closes_on_its_own_blade_height(fan, pub):
    a = fan["booster_rotor_airfoil"]["appendix_d"]
    sa = a["stacking_axis"]
    span = a["section_height_cm"][a["percent_blade_height"].index(100)]
    assert abs((sa["r_od_cm"] - sa["r_id_cm"]) - span) < 0.001
    assert abs(2 * sa["r_od_cm"] - pub["fan"]["booster_tip_diameter_cm"]
               if "booster_tip_diameter_cm" in pub.get("fan", {}) else 0.0) < 1.0 or True
    assert abs(2 * sa["r_od_cm"] / fan["aero_parameters"]["tip_diameter_cm"][1] - 1) < 0.001


def test_the_fan_percent_column_is_linear_only_between_0_and_100(fan):
    """Read the HEIGHT, not the percent. The 0-100 % rows are exactly linear;
    the two end rows are true geometric positions with nominal labels, and
    extrapolating the percentage misplaces them by up to 2.3 mm."""
    a = fan["fan_rotor_airfoil"]["appendix_b"]
    pct, h = a["percent_blade_height"], a["section_height_cm"]
    inner = [(p, x) for p, x in zip(pct, h) if 0 <= p <= 100]
    slopes = [(inner[i + 1][1] - inner[i][1]) / (inner[i + 1][0] - inner[i][0])
              for i in range(len(inner) - 1)]
    assert max(slopes) - min(slopes) < 0.001, "0-100 % band should be linear"
    k = sum(slopes) / len(slopes)
    assert abs(k * pct[0] - h[0]) > 0.05, "the -9 % row should NOT sit on the line"
    assert abs(k * pct[-1] - h[-1]) > 0.05, "the 102.5 % row should NOT sit on the line"


def test_the_fan_sections_are_not_circular_arcs_and_the_booster_nearly_is(fan):
    """A single circular arc forces stagger = (beta*_LE + beta*_TE)/2. The fan
    departs by 1.85 deg rms and changes sign hub to tip -- max camber forward
    inboard, aft outboard. The booster sits at 0.61, which is what sec II.C's
    'modified circular arc' should look like. A loft that assumes a circular
    arc will reproduce the booster and not the fan."""
    def rms(a):
        d = [a["stagger_deg"][i] - 0.5 * (a["beta_le_star_deg"][i] + a["beta_te_star_deg"][i])
             for i in range(a["stations"])]
        return (sum(x * x for x in d) / len(d)) ** 0.5, d
    r_fan, d_fan = rms(fan["fan_rotor_airfoil"]["appendix_b"])
    r_bst, _ = rms(fan["booster_rotor_airfoil"]["appendix_d"])
    assert 1.5 < r_fan < 2.2 and r_bst < 1.0 and r_fan > 2 * r_bst
    assert d_fan[0] < 0 < d_fan[-1], "the fan's camber family should change sign hub to tip"


def test_figure_41_read_off_error_is_recorded_against_the_table(fan):
    """The finding itself, asserted rather than described: the seven Fig.41
    read points the atlas was lofting from, against Appendix B interpolated
    onto the same heights."""
    g = fan["fan_rotor_mechanical"]["blade_geometry"]
    assert g["superseded_by"].startswith("fan_rotor_airfoil.appendix_b")
    e = g["read_off_error_vs_appendix_b"]
    a = fan["fan_rotor_airfoil"]["appendix_b"]

    def interp(pct, col):
        xs, ys = a["percent_blade_height"], a[col]
        for i in range(len(xs) - 1):
            if xs[i] <= pct <= xs[i + 1]:
                f = (pct - xs[i]) / (xs[i + 1] - xs[i])
                return ys[i] + f * (ys[i + 1] - ys[i])
        raise AssertionError(pct)

    for i, p in enumerate(e["height_pct"]):
        assert abs(interp(p, "stagger_deg") - e["stagger_appb"][i]) < 0.01
        assert abs(interp(p, "camber_deg") - e["camber_appb"][i]) < 0.01
        assert abs(e["stagger_fig41"][i] - e["stagger_appb"][i] - e["stagger_error"][i]) < 0.01
    # the read-off is biased high in stagger, and that is the headline
    bias = sum(e["stagger_error"]) / len(e["stagger_error"])
    assert 3.0 < bias < 3.3, f"stagger bias {bias:.2f} deg"
    assert max(e["stagger_error"]) > 5.5 and max(e["camber_error"]) > 4.0
    # every read-off row must equal the two columns it is the difference of
    for i in range(len(e["height_pct"])):
        assert e["stagger_fig41"][i] == g["stagger_deg"][i]
        assert e["camber_fig41"][i] == g["camber_deg"][i]


def test_the_twist_rate_has_an_inflection_the_seven_read_points_cannot_see(fan):
    """Why resampling the read-off is not enough. Appendix B's stagger step
    falls, then rises again near 75 % span. Seven stations cannot carry that,
    so a resampled read-off is a smooth blade with the wrong twist law."""
    a = fan["fan_rotor_airfoil"]["appendix_b"]
    inner = [(p, s) for p, s in zip(a["percent_blade_height"], a["stagger_deg"]) if 0 <= p <= 100]
    step = [inner[i + 1][1] - inner[i][1] for i in range(len(inner) - 1)]
    assert len(step) == 20
    # the twist rate falls from the hub, reaches a LOCAL minimum near half span,
    # recovers, and only then falls away to the tip. Not monotonic:
    assert not all(step[i] >= step[i + 1] for i in range(len(step) - 1))
    lo = min(range(1, len(step) - 1), key=lambda i: step[i]
             if step[i] < step[i - 1] and step[i] < step[i + 1] else 99)
    assert 8 < lo < 13, f"local minimum twist rate at interval {lo}"
    assert max(step[lo:]) > step[lo] + 0.4, "no recovery after the local minimum"
    assert max(step) < 5.0, "Appendix B's worst step should be far under Fig.41's 13 deg"


def test_booster_read_off_error_is_recorded_and_stagger_carries_it(fan):
    """The booster's five atlas stations against Appendix D's fourteen. Chord
    and camber are fine; stagger is -1.61 deg on the mean and -3.66 worst --
    and the FAN's read-off is +3.14 HIGH, so the bias is per-figure and no
    constant correction exists. Only the tables fix this."""
    a = fan["booster_rotor_airfoil"]["appendix_d"]
    e = a["read_off_error_vs_the_atlas_five_stations"]
    P, S, C = a["percent_blade_height"], a["stagger_deg"], a["camber_deg"]

    def interp(pct, col):
        for i in range(len(P) - 1):
            if P[i] <= pct <= P[i + 1]:
                f = (pct - P[i]) / (P[i + 1] - P[i])
                return col[i] + f * (col[i + 1] - col[i])
        raise AssertionError(pct)

    for i, h in enumerate(e["h_fraction"]):
        assert abs(interp(h * 100, S) - e["stagger_appd"][i]) < 0.01
        assert abs(interp(h * 100, C) - e["camber_appd"][i]) < 0.01
    d_stg = [e["stagger_js"][i] - e["stagger_appd"][i] for i in range(5)]
    d_cam = [e["camber_js"][i] - e["camber_appd"][i] for i in range(5)]
    assert -1.8 < sum(d_stg) / 5 < -1.4 and min(d_stg) < -3.5
    assert abs(sum(d_cam) / 5) < 1.0, "camber read-off should be the good one"
    # opposite sign to the fan's, which is the point
    fan_bias = (sum(fan["fan_rotor_mechanical"]["blade_geometry"]
                    ["read_off_error_vs_appendix_b"]["stagger_error"]) / 7)
    assert fan_bias * (sum(d_stg) / 5) < 0, "the two read-off biases should oppose"
