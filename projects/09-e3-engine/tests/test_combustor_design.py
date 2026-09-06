"""E3 combustor design (CR-168301), checked against itself and the rest
of the engine's data."""

from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def cb():
    return yaml.safe_load((DATA / "combustor-design.yaml").read_text())


@pytest.fixture(scope="module")
def pub():
    return yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())


def test_goals_convert_and_are_tighter_than_the_estimate(cb):
    g = cb["goals"]["emissions"]
    for k in ("co", "hc", "nox"):
        assert abs(g[k]["us"] / g[k]["si"] - 2.0) < 0.05, k  # lb/1000 lb-h to kg/kN-h is 1/2.0
    e = cb["emissions_estimate"]
    for k in ("co", "hc", "nox"):
        assert e[k][0] <= e[k][1] <= e[k][2], k
        assert abs(e[k][2] - g[k]["si"]) < 0.001
        for si, us in zip(e[k], e[f"{k}_us"]):
            assert abs(us / si - 2.0) < 0.15 or si < 0.05, (k, si, us)
    assert e["smoke_sn"][2] == g["smoke_sae_number"]
    assert cb["aero_requirements"]["pattern_factor_max"] == cb["goals"]["performance"]["exit_pattern_factor_slto_max"]


def test_life_ladder_matches_the_turbine_reports(cb):
    l = cb["goals"]["life"]
    assert l["hot_parts"]["total"] == 2 * l["hot_parts"]["first_repair"]
    assert l["cold_parts"]["total"] == 2 * l["hot_parts"]["total"]
    m = cb["mechanical_requirements"]
    assert m["to_first_repair"]["cycles"] == l["hot_parts"]["first_repair"]
    assert m["to_first_repair"]["hours"] == m["to_first_repair"]["cycles"] * m["mission_hours"]
    assert m["total_life"]["hours"] == m["total_life"]["cycles"] * m["mission_hours"]
    hpt = yaml.safe_load((DATA / "hpt-mechanical.yaml").read_text())["design_lives"]
    assert hpt["flowpath_components_and_blade_retainers"][1] == l["hot_parts"]["first_repair"]


def test_core_airflow_distribution_sums_to_one_hundred(cb):
    a = cb["airflow_distribution"]
    total = a["pilot_dome_pct"] + a["main_dome_pct"] + sum(a["outer_liner_pct"]) + sum(a["centerbody_pct"]) + sum(a["inner_liner_pct"])
    assert abs(total - a["total_pct"]) < 0.05, total
    assert a["main_dome_pct"] > a["pilot_dome_pct"]  # the lean main dome takes more air
    b = a["baseline"]
    read = b["pilot_dome_pct"] + b["main_dome_pct"] + sum(b["other_labels_pct"])
    assert abs(read - b["sum_as_read_pct"]) < 0.1
    assert b["pilot_dome_pct"] > a["pilot_dome_pct"] and b["main_dome_pct"] > a["main_dome_pct"]


def test_cycle_comparison_converts_and_the_dropped_decimal_is_recorded(cb):
    c = cb["cycle_comparison"]
    for blk in (c["ground_idle_6pct_fn"], c["slto_100pct_fn"]):
        for k, r in zip(blk["t3_K"], blk["t3_R"]):
            assert abs(r / 1.8 - k) < 0.6, (k, r)
        for i, (mpa, psia) in enumerate(zip(blk["p3_MPa"], blk["p3_psia"])):
            if blk is c["ground_idle_6pct_fn"] and i == 1:
                assert abs(mpa * 10 - psia * 0.0068948) < 0.01  # the recorded 0.043 for 0.43
            else:
                assert abs(mpa - psia * 0.0068948) < 0.012, (mpa, psia)
    g = cb["mechanical_requirements"]["growth_max_operating"]
    assert abs(g["t3_R"] / 1.8 - g["t3_K"]) < 0.6 and abs(g["p3_MPa"] - g["p3_psia"] * 0.0068948) < 0.01
    assert g["t3_K"] > max(c["slto_100pct_fn"]["t3_K"]) and g["p3_MPa"] > max(c["slto_100pct_fn"]["p3_MPa"])
    assert g["far"] > max(c["slto_100pct_fn"]["far"])


def test_thirty_of_everything(cb, pub):
    assert cb["fuel_nozzle"]["count"] == cb["general_design"]["support_pins"] == cb["diffuser"]["prediffuser_struts"] == 30
    assert pub["combustor"]["fuel_nozzles"] == 30 if "fuel_nozzles" in pub.get("combustor", {}) else True
    hpt = yaml.safe_load((DATA / "hpt-mechanical.yaml").read_text())
    assert hpt["stage1_blade"]["lcf"]["campbell"]["forcing_per_rev"]["burners"] == cb["fuel_nozzle"]["count"]


def test_fuel_nozzle_and_swirl_cup_numbers_convert(cb):
    fn = cb["fuel_nozzle"]
    assert abs(fn["max_pressure_drop_kPa"] - fn["max_pressure_drop_psid"] * 6.89476) < 2
    assert fn["life_cycles"]["total"] == 3 * fn["life_cycles"]["per_installation"]
    assert fn["spray_angle_deg"]["secondary"] > fn["spray_angle_deg"]["primary"]
    sc = cb["swirl_cup"]
    p, s = sc["primary"], sc["secondary"]
    assert abs(p["effective_area_cm2"] - p["effective_area_in2"] * 6.4516) < 0.01
    assert abs(p["venturi_throat_diameter_cm"] - p["venturi_throat_diameter_in"] * 2.54) < 0.01
    for dome in ("pilot", "main"):
        assert abs(s["vane_height_cm"][dome] - s["vane_height_in"][dome] * 2.54) < 0.01
        assert abs(s["effective_area_cm2"][dome] - s["effective_area_in2"][dome] * 6.4516) < 0.01
    assert s["effective_area_cm2"]["main"] > s["effective_area_cm2"]["pilot"]  # the lean dome breathes more
    assert s["vane_angle_deg"] > p["vane_angle_deg"]
    assert sc["emissions_reduction_sleeve"]["selected_after_test_deg"] > sc["emissions_reduction_sleeve"]["initial_exit_angle_deg"]
    r = sc["recirculation_target"]["fraction_of_cup_flow"]
    # Fig.23's line: 0.11 at 0 deg to 0.22 at 90 -- a 45-degree sleeve gives 0.165, inside the band; 90 gives 0.22, above it
    assert r[0] <= 0.11 + 0.11 * 45 / 90 <= r[1]
    v = sc["venturi_anticarboning"]["e3_point"]
    assert v["aes_over_at"] > 0.35 and v["lt_over_dt"] > 0.6  # right of the carbon boundary


def test_diffuser_and_dilution(cb):
    d = cb["diffuser"]
    assert d["inlet_mach_m3"] > d["passage_mach"]
    assert d["predicted_mass_weighted_total_pressure_loss_pct"] < cb["aero_requirements"]["total_pressure_drop_max_pct"]
    hpc = yaml.safe_load((DATA / "hpc-stagewise.yaml").read_text())
    assert abs(hpc["design_point"]["exit_meridional_mach"]["at_23_to_1_operating_line"] - d["inlet_mach_m3"]) < 0.001  # M3 = 0.30 both reports
    pen = cb["dilution"]["penetration"]
    assert pen["full_dp"] > pen["spent_impingement"]


def test_radial_profile_peaks_where_the_hpt_blade_is_rupture_limited(cb):
    rp = cb["aero_requirements"]["radial_profile"]
    assert rp["design_profile"]["peak_at_pct_height"] == 65
    assert rp["design_profile"]["peak"] < rp["tolerance_limit"]["peak"] < rp["maximum_temperature_limit_pf"]
    assert rp["maximum_temperature_limit_pf"] == cb["aero_requirements"]["pattern_factor_max"]
    hpt = yaml.safe_load((DATA / "hpt-mechanical.yaml").read_text())
    assert hpt["stator"]["stage2_nozzle"]["lcf"]["limiting"]["span_pct"] == 65


def test_staging_schedule_is_ordered(cb):
    st = cb["fuel_nozzle"]["staging"]
    assert st["pilot_secondary_cut_in_pct_nh"] < st["main_stage_on_pct_nh"] < st["approach_pct_nh"] < st["slto_pct_nh"]
    ff = st["fuel_flow_kg_h"]
    assert ff["ground_start"] < ff["idle"] < ff["approach"] < ff["slto"]
    assert cb["fuel_nozzle"]["main_to_pilot_above_secondary_cut_in"].startswith("about 2")


def test_casing_ports_and_support_pin(cb):
    p = cb["casing"]["ports"]
    assert p["fuel_nozzle"] == p["instrumentation"] == p["support_pin_holes"] == 30
    assert p["igniter"]["count"] == 2 and cb["centerbody"]["crossfire_tubes"] == 2
    assert p["borescope"]["fig38"] != p["borescope"]["fig39"]["count"]  # the recorded pair
    sp = cb["casing"]["support_pin"]
    assert abs(sp["diameter_cm"] - sp["diameter_in"] * 2.54) < 0.003
    assert abs(sp["max_load_N"] - sp["max_load_lb"] * 4.44822) < 1
    assert abs(sp["max_bending_stress_MPa"] - sp["max_bending_stress_ksi"] * 6.89476) < 1
    assert abs(sp["yield_avg_minus_3sigma_MPa"] - sp["yield_avg_minus_3sigma_ksi"] * 6.89476) < 1
    assert abs(sp["clearance_to_cowl_strut_cm"] - sp["clearance_to_cowl_strut_in"] * 2.54) < 0.001
    assert sp["max_bending_stress_MPa"] < sp["yield_avg_minus_3sigma_MPa"] / 2
    # 30 pins share the aero load: about 24 kN total
    assert 20000 < sp["count"] * sp["max_load_N"] < 30000


def test_centerbody_tip_frequencies_put_the_core_at_one_speed(cb, pub):
    t = cb["centerbody"]["tip_redesign"]
    rpm_initial = t["initial"]["first_flex_Hz"] * 60 / t["initial"]["per_rev"]
    rpm_chosen = t["chosen"]["first_flex_Hz"] * 60 / t["chosen"]["per_rev"]
    assert abs(rpm_initial - rpm_chosen) < 1
    assert abs(rpm_chosen - 12303) / 12303 < 0.03
    assert t["chosen"]["first_flex_Hz"] > 3 * t["initial"]["first_flex_Hz"]
    assert cb["dome"]["swirl_cups_per_dome"] == cb["centerbody"]["dilution_eyelets_per_dome"] == 30


def test_two_d_calculation_table_converts_with_its_recorded_prints(cb):
    x = cb["heat_transfer"]["two_d_calculations"]
    for k, r in zip(x["t3_K"], x["t3_R"]):
        assert abs(r / 1.8 - k) <= 1.0, (k, r)  # both columns rounded to the degree
    for mpa, psia in zip(x["p3_MPa"], x["p3_psia"]):
        assert abs(mpa - psia * 0.0068948) < 0.012, (mpa, psia)
    bad = [(kg, pps) for kg, pps in zip(x["w_comb_kg_s"], x["w_comb_pps"]) if abs(kg - pps * 0.45359) > 0.1]
    assert bad == [(65.3, 123.8)], bad
    assert x["t3_K"][0] == cb["cycle_comparison"]["slto_100pct_fn"]["t3_K"][2]
    assert x["fuel_air"][2] > x["fuel_air"][0]  # growth hot day runs richer
    assert x["main_fuel_fraction"][1] == 0  # pilot only at approach in this table
    c = x["component_test_point"]
    assert abs(c["w_comb_kg_s"] - c["w_comb_pps"] * 0.45359) < 0.05
    assert len(x["as_printed"]) == 3


def test_liner_temperatures_convert_and_inner_panel_1_is_limiting(cb):
    b = cb["heat_transfer"]["baseline_liner_temperatures"]
    for k, f in zip(b["K"], b["F"]):
        assert abs((f - 32) / 1.8 + 273.15 - k) < 1.0, (k, f)
    assert b["panel"][b["K"].index(max(b["K"]))] == "1_inner"
    assert cb["heat_transfer"]["limiting_panel"].startswith("inner liner panel 1")
    for side in ("outer", "inner"):
        vals = [k for p, k in zip(b["panel"], b["K"]) if p.endswith(side)]
        assert vals == sorted(vals, reverse=True), side  # cooler downstream
    fw = cb["heat_transfer"]["foot_width_study"]
    for k in ("full_foot", "half_foot"):
        assert abs((fw[k]["peak_F"] - 32) / 1.8 + 273.15 - fw[k]["peak_K"]) < 4
        assert abs(fw[k]["foot_cm"] - fw[k]["foot_in"] * 2.54) < 0.006 and abs(fw[k]["slot_cm"] - fw[k]["slot_in"] * 2.54) < 0.006
    assert fw["half_foot"]["peak_K"] < fw["full_foot"]["peak_K"]
    ft = cb["liner_design"]["support_feet"]["e3"]["outer"]
    assert fw["half_foot"]["foot_cm"] < ft["w_cm"] < fw["full_foot"]["foot_cm"]  # the final design sits between
    p1 = cb["heat_transfer"]["panel1_inner_profile"]
    assert max(p1["hot_streak_K"]) > max(p1["average_K"]) and max(p1["hot_streak_K"]) > b["K"][3]


def test_centerbody_and_tip_temperature_tables(cb):
    ct = cb["centerbody_temperatures"]
    for side in ("panel_pilot_side_K", "panel_main_side_K"):
        for split, blk in ct[side].items():
            if not split.startswith("split"):
                continue
            for i in range(len(blk["uncoated_cold"])):
                if side == "panel_main_side_K" and split == "split_40_60" and i == 0:
                    continue  # the recorded 769
                assert blk["tbc_cold"][i] < blk["uncoated_cold"][i] < blk["uncoated_hot"][i], (side, split, i)
    p, m = ct["panel_pilot_side_K"], ct["panel_main_side_K"]
    assert p["split_30_70"]["uncoated_hot"][0] < p["split_50_50"]["uncoated_hot"][0]  # pilot cools as the main takes fuel
    assert m["split_30_70"]["uncoated_hot"][0] > m["split_50_50"]["uncoated_hot"][0]  # the main side heats
    tip = ct["tip_distribution"]
    assert max(tip["main_dome_side_K"]) == tip["max_K"]
    assert abs((tip["max_F"] - 32) / 1.8 + 273.15 - tip["max_K"]) < 1.0
    assert max(tip["pilot_dome_side_K"]) < min(tip["main_dome_side_K"])


def test_fuel_nozzle_thermal_limits_convert(cb):
    fn = cb["fuel_nozzle_thermal"]
    for k, r in zip(fn["carbon_formation_critical_K"], fn["carbon_formation_critical_R"]):
        assert abs(r / 1.8 - k) < 0.6
    assert abs(fn["uninsulated_wall_R"] / 1.8 - fn["uninsulated_wall_K"]) < 0.6
    assert abs(fn["fps_max_fuel_inlet_R"] / 1.8 - fn["fps_max_fuel_inlet_K"]) < 0.6
    assert fn["fps_max_fuel_inlet_K"] < fn["carbon_formation_critical_K"][0] < fn["uninsulated_wall_K"]
    c = fn["fig64_conditions"]
    assert abs(c["p3_MPa"] - c["p3_psia"] * 0.0068948) < 0.01 and abs((c["t3_F"] - 32) / 1.8 + 273.15 - c["t3_K"]) < 1.0
    assert abs(c["w3_kg_s"] - c["w3_lb_s"] * 0.45359) < 0.2 and abs(c["wf_total_kg_h"] - c["wf_total_pph"] * 0.45359) < 15
    assert abs(c["wf_total_kg_h"] / 3600 / c["w3_kg_s"] - 0.0283) < 0.002  # the nozzle-design fuel-air ratio
    il = fn["ignition_lead"]
    assert il["core_cowl_purge_K"] < il["soak_back_peak_K"] < il["teflon_limit_K"]


def test_mission_mix_sums_and_shingle_life_beats_its_goals(cb):
    mm = cb["stress_and_life"]["mission_mix"]
    assert mm["cold_day"]["pct"] + mm["standard_day"]["pct"] + mm["tropical_day"]["pct"] + mm["hot_day"]["pct"] == 100
    sh = cb["stress_and_life"]["shingle"]
    assert abs(sh["pressure_stress"]["end_foot_bending_MPa"] - sh["pressure_stress"]["end_foot_bending_ksi"] * 6.89476) < 1
    assert sh["rupture"]["e3_design"]["rupture_life_h"] > sh["rupture"]["goal_h"]
    assert sh["lcf"]["e3_design_cycles_with_hold_time"] > sh["lcf"]["goal_cycles"] == cb["goals"]["life"]["hot_parts"]["first_repair"]
    pl = sh["predicted_life"]
    for k in ("baseline_x40", "growth_mar_m_509"):
        assert abs((pl[k]["t_max_F"] - 32) / 1.8 + 273.15 - pl[k]["t_max_K"]) < 1.0
        assert pl[k]["rupture_h"] > pl["goal"]["rupture_h"]
    assert pl["baseline_x40"]["lcf_cycles_taken"] == 100000 and pl["baseline_x40"]["lcf_cycles_as_printed"] == 105
    assert pl["growth_mar_m_509"]["lcf_cycles"] > pl["goal"]["lcf_cycles"]
    assert abs(sh["rupture"]["e3_design"]["w_over_s"] - cb["liner_design"]["support_feet"]["e3"]["outer"]["w_over_s"]) < 0.1


def test_support_liner_buckling_margin(cb):
    sl = cb["stress_and_life"]["support_liners"]
    assert abs(sl["condition"]["p3_MPa"] - sl["condition"]["p3_psia"] * 0.0068948) < 0.01
    assert abs((sl["condition"]["t3_F"] - 32) / 1.8 + 273.15 - sl["condition"]["t3_K"]) < 1.0
    assert abs(sl["yield_0_02pct_at_922K_MPa"] - sl["yield_0_02pct_at_922K_ksi"] * 6.89476) < 2
    assert max(sl["outer_liner_stress_MPa"].values()) < sl["yield_0_02pct_at_922K_MPa"]
    assert max(v for v in sl["inner_liner_stress_MPa"].values() if isinstance(v, (int, float))) < sl["yield_0_02pct_at_922K_MPa"]
    b = sl["buckling"]
    assert abs(b["dp_MPa"] - b["dp_psia"] * 0.0068948) < 0.001
    for n, lb in zip(b["line_loads_N_cm"], b["line_loads_lb_in"]):
        assert abs(n - lb * 1.75127) < 0.1
    assert abs(b["round_shell_1_02mm"]["min_critical_MPa"] - b["round_shell_1_02mm"]["min_critical_psi"] * 0.0068948) < 0.01
    oor = b["out_of_round_design"]
    assert abs(oor["min_yielding_pressure_MPa"] / oor["full_dp_MPa"] - oor["margin"]) < 0.05
    assert oor["margin"] >= 2.0
    assert len(b["as_printed"]) == 3


def test_casing_loads_convert_and_the_aft_plateau_is_recorded(cb):
    c = cb["stress_and_life"]["casing"]
    for k in c["axial_loads_kN"]:
        assert abs(c["axial_loads_kN"][k] - c["axial_loads_lb"][k] * 0.00444822) < 0.2, k
    assert abs(c["conditions"]["pressure_load_MPa"] - c["conditions"]["pressure_load_psi"] * 0.0068948) < 0.01
    assert abs((c["conditions"]["t_case_F"] - 32) / 1.8 + 273.15 - c["conditions"]["t_case_K"]) < 1.0
    assert abs(c["fifty_pct_yield_avg_minus_3sigma_MPa"] - c["fifty_pct_yield_ksi"] * 6.89476) < 2
    assert c["stress_read_off_MPa"]["aft_plateau"] > c["fifty_pct_yield_avg_minus_3sigma_MPa"]  # as read
    assert c["stress_read_off_MPa"]["forward_peak"] < c["fifty_pct_yield_avg_minus_3sigma_MPa"]


def test_centerbody_life_only_the_slotted_coated_tip_meets_the_goal(cb):
    cl = cb["stress_and_life"]["centerbody_life"]
    for i in range(3):
        assert cl["baseline"][i] < cl["with_thermal_barrier"][i] < cl["with_tip_slots"][i] < cl["with_slots_and_barrier"][i]
    assert max(cl["with_tip_slots"]) < cl["goal_cycles"] < min(cl["with_slots_and_barrier"][:2])
    assert cl["with_slots_and_barrier"][2] < cl["goal_cycles"]  # 70 percent main fuel is past the goal
    assert cl["goal_cycles"] == cb["goals"]["life"]["hot_parts"]["first_repair"]


def test_fuel_nozzle_frequency_choice(cb):
    v = cb["fuel_nozzle_vibration"]
    c = v["comparison"]
    rpm = c["first_flex_Hz"][2] * 60 / c["per_rev_at_takeoff"][2]
    assert abs(rpm - v["campbell"]["takeoff_rpm"]["baseline"]) / rpm < 0.01
    assert v["chosen_Hz"] == c["first_flex_Hz"][2] == 750 and v["chosen_Hz"] < v["original_goal_min_Hz"]
    assert v["campbell"]["current_design_Hz"]["at_takeoff"] == v["chosen_Hz"]
    assert abs(v["campbell"]["current_design_Hz"]["at_0"] - 816) < 10
    assert min(c["first_flex_Hz"]) < v["chosen_Hz"] < max(c["first_flex_Hz"])
    assert cb["fuel_nozzle"]["natural_frequency_min_Hz"] == v["original_goal_min_Hz"]


def test_development_test_summary_is_consistent(cb):
    d = cb["development_testing"]
    e = d["emissions_summary"]
    for k in ("co", "hc", "nox"):
        assert e[k][3] == cb["goals"]["emissions"][k]["us"]
    assert e["co"][0] > e["co"][3] and e["hc"][0] > e["hc"][3] and e["nox"][0] < e["nox"][3]  # rig Mod VII: CO and HC over, NOx under
    assert e["co"][2] > e["co"][1] > e["co"][0]
    r = d["results"]
    assert abs(r["baseline"]["epap"]["co"] - e["co"][2]) < 0.05 and abs(r["mod_vii"]["epap"]["co"] - e["co"][0]) < 0.05
    x = d["exit_temperature"]
    for pf, mdd in zip(x["pattern_factor"], x["main_dome"]):
        if pf is not None and mdd == "rich":
            assert pf >= 0.40
    assert x["pattern_factor"][1] == x["goal"]["pattern_factor"] == cb["aero_requirements"]["pattern_factor_max"]
    assert x["profile_factor"][1] < x["goal"]["profile_factor"] == cb["aero_requirements"]["profile_factor_max"]
    assert x["mod_vi_detail"]["pattern_factor_at_0_4"] == x["pattern_factor"][6]
    s = d["subidle_ignition"]
    for far, tgt in zip(s["pilot_far"], s["pilot_target_far"]):
        assert far <= tgt
    for far, tgt in zip(s["main_far"], s["main_target_far"]):
        if far is not None:
            assert far > 2.5 * tgt
    slto = x["mod_vi_detail"]["slto_points"]
    assert abs(slto["w3_kg_s"] - slto["w_bleed_kg_s"] - slto["w_comb_kg_s"]) < 0.01
    for wp, wm in zip(slto["wf_pilot_kg_h"], slto["wf_main_kg_h"]):
        assert abs((wp + wm) / 3600 / slto["w_comb_kg_s"] - slto["fuel_air"]) < 0.0003
    for wp, wm, sp in zip(slto["wf_pilot_kg_h"], slto["wf_main_kg_h"], slto["splits"]):
        assert abs(wp / (wp + wm) - sp) < 0.01
    fp = d["fps_prediction"]
    off = []
    for cond in ("ground_idle_4pct", "ground_idle_6pct"):
        for k in ("co", "hc", "nox"):
            margin = (fp["goal"][k] / fp[cond][k] - 1) * 100
            if abs(margin - fp[cond]["margin_pct"][k]) > 1.5:
                off.append((cond, k, round(margin)))
    assert off == [("ground_idle_6pct", "hc", 264)], off  # the recorded print: 364 for 264
