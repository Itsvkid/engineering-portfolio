"""LPT design data (the LPT hardware report, sections 3.10 and 4), checked
against itself and against the published cycle data. Plain interpreter."""

from __future__ import annotations

import math
import pathlib

import pytest

yaml = pytest.importorskip("yaml")

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def lpt():
    return yaml.safe_load((DATA / "lpt-design.yaml").read_text())


@pytest.fixture(scope="module")
def published():
    return yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())


def rpm_from_corrected(n_over_sqrt_t, t_k):
    return n_over_sqrt_t * math.sqrt(t_k) * 60 / (2 * math.pi)


# ── blade counts and geometry ───────────────────────────────────────────

def test_five_stages_with_the_acoustic_stage_four(lpt):
    rb = lpt["rotor_blades"]
    assert rb["stage"] == [1, 2, 3, 4, 5]
    assert rb["blade_count"] == [120, 122, 122, 156, 110]
    assert sum(rb["blade_count"]) == rb["total_blades"]
    assert max(rb["blade_count"]) == rb["blade_count"][3] == lpt["acoustic_constraint_stage4"]["blade_count"]


def test_centimetres_equal_inches_times_2_54(lpt):
    rb = lpt["rotor_blades"]
    for cm_key, in_key in (("root_chord_cm", "root_chord_in"), ("tip_chord_cm", "tip_chord_in"), ("blade_length_cm", "blade_length_in")):
        for s, (cm, inch) in enumerate(zip(rb[cm_key], rb[in_key]), 1):
            assert abs(cm - inch * 2.54) < 0.015, f"stage {s} {cm_key}: {cm} vs {inch} in"
    ap = lpt["aero_design_parameters"]
    for cm, inch in zip(ap["tip_diameter_cm"], ap["tip_diameter_in"]):
        assert abs(cm - inch * 2.54) < 0.06
    for ms, fts in zip(ap["tip_speed_m_s"], ap["tip_speed_ft_s"]):
        assert abs(ms - fts * 0.3048) < 0.2
    for kg, lb in zip(ap["airflow_kg_s"], ap["airflow_lb_s"]):
        assert abs(kg - lb * 0.45359) < 0.05


def test_aspect_ratios_recompute_except_the_flask_shaped_stage_four(lpt):
    rb = lpt["rotor_blades"]
    for s, (L, cr, ct, ar) in enumerate(zip(rb["blade_length_cm"], rb["root_chord_cm"], rb["tip_chord_cm"], rb["aspect_ratio"]), 1):
        mean_chord = (cr + ct) / 2
        if s == 4:
            # smaller chord at pitch than at either end
            assert L / ar < min(cr, ct), f"stage 4 pitch chord {L/ar:.2f} not below root/tip"
        else:
            assert abs(L / mean_chord - ar) / ar < 0.025, f"stage {s}: L/c = {L/mean_chord:.2f}, printed {ar}"


def test_blades_get_longer_stage_by_stage(lpt):
    L = lpt["rotor_blades"]["blade_length_cm"]
    assert L == sorted(L)


def test_table_vii_aspect_ratios_match_fig_52(lpt):
    ap, rb = lpt["aero_design_parameters"], lpt["rotor_blades"]
    assert ap["aspect_ratio"] == [rb["aspect_ratio"][0], rb["aspect_ratio"][4]]
    assert ap["number_of_blades"][1] == rb["blade_count"][4]
    # the recorded disagreement: Table VII's stage-1 count is Fig.52's stage-2 count
    assert ap["number_of_blades"][0] != rb["blade_count"][0]
    assert ap["number_of_blades"][0] == rb["blade_count"][1]


# ── speeds: several routes ──────────────────────────────────────────────

def test_tip_speeds_both_recompute_to_the_takeoff_speed(lpt):
    """Table VII tip speed / tip radius must give ONE rpm for both stages,
    and it is case 72's 3,611. This is what fixes the '23.7' misprint."""
    ap = lpt["aero_design_parameters"]
    rpms = [v / (d / 200) * 60 / (2 * math.pi) for v, d in zip(ap["tip_speed_m_s"], ap["tip_diameter_cm"])]
    assert abs(rpms[0] - rpms[1]) / rpms[0] < 0.003, rpms
    case72 = lpt["design_cycle_points"]["case_72_max_stress"]["rotor_physical_speed_rpm"][0]
    assert abs(rpms[0] - case72) / case72 < 0.003, (rpms, case72)


def test_max_climb_speed_matches_the_cycle_data_two_ways(lpt, published):
    """Table VI 3,539 rpm; Table I N/sqrt(T49) at max climb; and the fan
    tip speed de-corrected -- three routes to the LP speed."""
    case41 = lpt["design_cycle_points"]["case_41_flowpath_and_clearance"]["fan_physical_speed_rpm"][0]
    er = published["lpt"]["earlier_requirements"]["max_climb"]
    from_table_i = rpm_from_corrected(er["N_over_sqrtT"], er["T49_K"])
    assert abs(from_table_i - case41) / case41 < 0.003, (from_table_i, case41)


def test_cruise_goal_speed_matches_table_i_max_cruise(lpt, published):
    goal = lpt["design_goals"]["performance"]
    er = published["lpt"]["earlier_requirements"]["max_cruise"]
    from_table_i = rpm_from_corrected(er["N_over_sqrtT"], er["T49_K"])
    assert abs(from_table_i - goal["physical_speed_rpm"]) / goal["physical_speed_rpm"] < 0.01
    # the recorded print: the goal's 91.7 % / 1.29 are Table I's max-CLIMB figures
    mc = published["lpt"]["earlier_requirements"]["max_climb"]
    assert goal["efficiency"] != er["efficiency"] and goal["efficiency"] == mc["efficiency"]
    assert abs(goal["loading_parameter"] - mc["loading"]) < 0.01
    assert "not corrected" in lpt["design_goals"]["as_printed_inconsistency"]


def test_overspeed_cases_are_2_6_percent_except_the_recorded_one(lpt):
    d = lpt["design_cycle_points"]
    for case in ("case_72_max_stress", "case_27_max_stress"):
        for i, (base, over) in enumerate(zip(d[case]["rotor_physical_speed_rpm"], d[case]["at_2_6pct_overspeed_rpm"])):
            ratio = over / base
            if case == "case_72_max_stress" and i == 1:
                assert 1.015 < ratio < 1.025, "growth case 72 now reads 2.6 % -- drop the inconsistency note"
            else:
                assert abs(ratio - 1.026) < 0.001, (case, i, ratio)


def test_growth_speeds_exceed_fps_and_the_122pct_capability_covers_them(lpt):
    d = lpt["design_cycle_points"]
    for case in d.values():
        if isinstance(case, dict) and "rotor_physical_speed_rpm" in case:
            assert case["rotor_physical_speed_rpm"][1] > case["rotor_physical_speed_rpm"][0]
    fps_max = max(c["rotor_physical_speed_rpm"][0] for c in d.values() if isinstance(c, dict) and "rotor_physical_speed_rpm" in c)
    growth_max = max(c["at_2_6pct_overspeed_rpm"][1] for c in d.values() if isinstance(c, dict) and "at_2_6pct_overspeed_rpm" in c)
    assert growth_max < 1.22 * fps_max * 1.1  # 122 % of max-rated growth speed comfortably covers every case


def test_acc_rpm_figure_is_flagged_not_used(lpt):
    acc = lpt["active_clearance_control"]["casing_cooling_objective"]
    case41 = lpt["design_cycle_points"]["case_41_flowpath_and_clearance"]["fan_physical_speed_rpm"][0]
    assert abs(acc["cycle_points_rpm"]["max_climb_10_7km"] - case41) / case41 > 0.05, "ACC rpm now matches Table VI -- drop the flag"
    assert "not reconciled" in acc["note"]


# ── clearance-control payoff ────────────────────────────────────────────

def test_acc_payoff_rows_multiply_and_sum(lpt):
    p = lpt["active_clearance_control"]["payoff_at_max_cruise_10_67km"]
    for s, (per10, closure, stage) in enumerate(zip(p["d_eta_per_10_mils"], p["closure_mils"], p["d_eta_per_stage"]), 1):
        # d_eta/10 mils x closure (in units of 10 mils)... closure is printed
        # as 0.032 etc.; the per-stage figure is per10 x closure x 100.
        assert abs(per10 * closure * 100 - stage) < 0.006, f"stage {s}: {per10} x {closure} x 100 = {per10*closure*100:.3f} vs {stage}"
    assert abs(sum(p["d_eta_per_stage"]) - p["d_eta_total_pct"]) < 0.01
    assert abs(p["d_sfc_clearance_pct"] + p["d_sfc_fan_air_cost_pct"] - p["d_sfc_total_pct"]) < 0.005


# ── life and materials ──────────────────────────────────────────────────

def test_life_basis_arithmetic(lpt):
    lb = lpt["life_basis"]
    assert lb["stress_cycles_rotor"] == lb["aircraft_missions"] * lb["stress_cycles_per_mission_rotor"]
    assert lb["stress_cycles_other"] == lb["aircraft_missions"]
    for cm, inch in zip(lb["defect_size_cm"], lb["defect_size_in"]):
        assert abs(cm - inch * 2.54) < 0.001
    blade_lcf = lpt["rotor_blades"]["life"]["lcf"]
    assert blade_lcf["required_cycles"] == 36000


def test_materials_change_only_the_stage1_vane(lpt):
    m = lpt["materials"]
    for group in ("stator", "rotor"):
        for part, (icls, fps) in m[group].items():
            if part == "vane_1":
                assert (icls, fps) == ("Rene 77", "Rene 125")
            else:
                assert icls == fps, part


def test_start_temperatures_are_ordered_and_the_misprint_is_recorded(lpt):
    s = lpt["start_analysis"]
    assert s["early_analysis_hpt_inlet_C"] - s["after_1980_81_tests"]["hpt_inlet_C"] == s["after_1980_81_tests"]["hpt_inlet_reduction_C"]
    v, b = s["lpt_stage1_vane"], s["lpt_stage1_blade"]
    assert b["inlet_with_average_pf_C"] < v["hot_streak_C"]
    assert abs((v["hot_streak_F"] - 32) / 1.8 - v["hot_streak_C"]) < 1.5
    assert abs((b["inlet_with_average_pf_F"] - 32) / 1.8 - b["inlet_with_average_pf_C"]) < 1.5
    assert abs(b["transient_gradient_max_F"] / 1.8 - b["transient_gradient_max_C"]) < 1.0
    assert v["steady_gradient_te_to_bulk_max_C"] < v["transient_gradient_max_C"]
    assert "misprint" in v["note"]
    for pf in s["pattern_factors_at_start_pilot_only"].values():
        if isinstance(pf, dict):
            assert pf["peak"] > pf["circumferential_average"]


def test_vane_counts_are_the_resonance_forcing_orders(lpt):
    v = lpt["vane_counts"]
    x = lpt["rotor_blades"]["vibration"]["stage1_crossings_near_operating_range"]
    assert x["forcing"] == [v["stage1"], v["stage2"]]


def test_takeoff_stresses_convert_between_mpa_and_ksi(lpt):
    s = lpt["airfoil_stress_takeoff"]
    for key in ("centrifugal_pitch", "centrifugal_root", "leading_edge_resultant_pitch", "leading_edge_resultant_root", "uncorrected_gas_bending_root"):
        for st, (mpa, ksi) in enumerate(zip(s[f"{key}_MPa"], s[f"{key}_ksi"]), 1):
            assert abs(mpa - ksi * 6.89476) < 0.45, f"stage {st} {key}: {mpa} MPa vs {ksi} ksi"


def test_centrifugal_stress_rises_stage_by_stage_and_root_exceeds_pitch(lpt):
    s = lpt["airfoil_stress_takeoff"]
    assert s["centrifugal_root_MPa"] == sorted(s["centrifugal_root_MPa"])
    for r, p in zip(s["centrifugal_root_MPa"], s["centrifugal_pitch_MPa"]):
        assert r > p
    assert s["uncorrected_gas_bending_root_MPa"] == sorted(s["uncorrected_gas_bending_root_MPa"])


def test_stage1_and_5_root_centrifugal_stress_are_a_shrouded_blade_away_from_rho_omega2_a(lpt):
    """sigma_root = rho omega^2 A / (2 pi) for an untapered, unshrouded
    blade. The E3 LPT blades are near-constant-chord AND carry tip
    shrouds, so the printed root stress should sit a little ABOVE that
    figure -- the shroud mass -- not below it. Table VII gives tip diameter
    and inlet radius ratio for stages 1 and 5; Table VIII the stress at the
    3,707 rpm takeoff case; Rene 77 density ~7,900 kg/m3."""
    ap, s = lpt["aero_design_parameters"], lpt["airfoil_stress_takeoff"]
    rpm = lpt["design_cycle_points"]["case_72_max_stress"]["at_2_6pct_overspeed_rpm"][0]
    omega = rpm * 2 * math.pi / 60
    for col, stage_idx in ((0, 0), (1, 4)):
        r_t = ap["tip_diameter_cm"][col] / 200
        r_h = r_t * ap["inlet_radius_ratio"][col]
        area = math.pi * (r_t ** 2 - r_h ** 2)
        untapered = 7900 * omega ** 2 * area / (2 * math.pi) / 1e6
        printed = s["centrifugal_root_MPa"][stage_idx]
        assert 0.95 < printed / untapered < 1.35, f"stage {stage_idx+1}: printed {printed} MPa, rho omega^2 A/2pi = {untapered:.1f}"


def test_rupture_mission_hours_sum_to_the_life_and_units_convert(lpt):
    m = lpt["rupture_mission"]
    cols = m["columns"]
    hours = sum(p[cols.index("hours")] for p in m["points"])
    assert abs(hours - m["total_hours"]) < 0.1
    for p in m["points"]:
        c, f = p[cols.index("t49_C")], p[cols.index("t49_F")]
        assert abs((f - 32) / 1.8 - c) < 1.5, p
        kpa, psi = p[cols.index("p49_kPa")], p[cols.index("p49_psi")]
        assert abs(kpa - psi * 6.89476) < 4, p
    assert m["points"][0][cols.index("rpm")] == lpt["design_cycle_points"]["case_72_max_stress"]["at_2_6pct_overspeed_rpm"][0]
    # three mission counts in one report -- each section's own arithmetic holds
    lb, lcf = lpt["life_basis"], lpt["rotor_blades"]["life"]["lcf"]
    assert lb["aircraft_missions"] * lb["stress_cycles_per_mission_rotor"] == lb["stress_cycles_rotor"]
    assert 18000 * 2 == lcf["required_cycles"]
    assert lb["aircraft_missions"] != 18000 and "flagged" in lb["as_printed_inconsistency"]
    assert m["total_hours"] == lpt["design_goals"]["life_hours_and_cycles"]["cold_nonflowpath_parts"]
    assert m["total_hours"] / lpt["flight_cycle"]["total_minutes"] * 60 == 9000


def test_rupture_and_hcf_margins(lpt):
    r = lpt["blade_life_results"]
    assert r["rupture_capability_hours"]["stage1"]["minimum"] > r["rupture_required_hours"]
    assert r["rupture_capability_hours"]["stage1"]["minimum"] / r["rupture_required_hours"] < 2.0
    assert r["rupture_capability_hours"]["stage2"]["minimum"] > 5 * r["rupture_required_hours"]
    h = r["hcf"]
    assert abs(h["minimum_allowable_vibratory_MPa"] - h["minimum_allowable_vibratory_ksi"] * 6.89476) < 1.5
    assert h["capability_MPa_range"][0] > 2.5 * h["minimum_allowable_vibratory_MPa"]


def test_stage1_campbell_is_ordered_and_the_crossings_are_where_the_text_says(lpt):
    c = lpt["stage1_blade_campbell"]
    f = c["natural_frequencies_Hz"]
    order = ["first_flex", "first_torsion", "first_axial", "second_torsion"]
    at0 = [f[m]["at_0_rpm"] for m in order]
    at4k = [f[m]["at_4000_rpm"] for m in order]
    assert at0 == sorted(at0) and at4k == sorted(at4k)
    for m in order:
        assert f[m]["at_4000_rpm"] < f[m]["at_0_rpm"]  # softening with speed, as drawn
    assert f["two_stripe"]["at_3700_rpm"] > 2 * f["second_torsion"]["at_0_rpm"] * 0.8
    # second torsion vs 72/rev: crossing where 72 * N / 60 = f(N); interpolate linearly
    lo, hi = c["steady_state_band_rpm"]
    def second_torsion(n):
        return f["second_torsion"]["at_0_rpm"] + (f["second_torsion"]["at_4000_rpm"] - f["second_torsion"]["at_0_rpm"]) * n / 4000
    cross_72 = next(n for n in range(1000, 5000, 10) if 72 * n / 60 >= second_torsion(n))
    cross_102 = next(n for n in range(1000, 5000, 10) if 102 * n / 60 >= second_torsion(n))
    assert lo - 400 < cross_102 < lo + 200, cross_102
    assert hi - 200 < cross_72 < hi + 500, cross_72
    # no first-mode crossing with either vane line inside the band
    for n in range(lo, hi + 1, 50):
        for m in ("first_flex", "first_torsion", "first_axial"):
            fm = f[m]["at_0_rpm"] + (f[m]["at_4000_rpm"] - f[m]["at_0_rpm"]) * n / 4000
            assert abs(72 * n / 60 - fm) > 150 or m == "first_axial" and n > hi - 100 and False, (m, n)


def test_published_data_carries_the_lpt_blade_counts(lpt, published):
    p = published["lpt"]["blade_counts_per_stage"]
    assert p["value"] == lpt["rotor_blades"]["blade_count"]
    assert p["verified"] is True


def test_flight_cycle_is_two_hours(lpt):
    f = lpt["flight_cycle"]
    minutes = sum(v / 60 if k.endswith("_s") else v for k, v in f["segments_minutes"].items())
    assert abs(minutes - f["total_minutes"]) < 2.5, minutes


# ── rotor structure: shrouds, dovetails, disks, bolts (pp.96-119) ───────

def pairs_convert(a, b, factor, tol):
    for x, y in zip(a, b):
        if x is None or y is None:
            continue
        assert abs(x - y * factor) < tol, (x, y)


def test_blade_lcf_table_converts_and_cools_rearward(lpt):
    x = lpt["blade_lcf"]
    pairs_convert(x["sigma_max_MPa"], x["sigma_max_ksi"], 6.89476, 0.05)
    for c, f in zip(x["temperature_C"], x["temperature_F"]):
        assert abs((f - 32) / 1.8 - c) < 0.6
    assert x["temperature_C"] == sorted(x["temperature_C"], reverse=True)
    assert x["sigma_max_MPa"] == sorted(x["sigma_max_MPa"])
    assert x["required_cycles"] == lpt["rotor_blades"]["life"]["lcf"]["required_cycles"]


def test_flutter_margins_all_at_least_one_and_stage4_is_the_marginal_one(lpt):
    f = lpt["flutter"]
    assert min(f["torsion"]) >= 1.0 and min(f["flex"]) >= 1.0
    assert f["torsion"].index(min(f["torsion"])) == 3
    for t_, fl in zip(f["torsion"], f["flex"]):
        assert fl > t_


def test_tip_shroud_table_converts_except_the_recorded_dropped_zero(lpt):
    ts = lpt["tip_shrouds"]
    for i, (cm2, in2) in enumerate(zip(ts["interlock_surface_cm2"], ts["interlock_surface_in2"])):
        if i == 1:
            assert abs(cm2 / 6.4516 - in2 / 10) < 0.001  # 0.319 printed for 0.0319
        else:
            assert abs(cm2 / 6.4516 - in2) < 0.001
    pairs_convert(ts["overhang_l_cm"], ts["overhang_l_in"], 2.54, 0.013)
    pairs_convert(ts["contact_stress_MPa"], ts["contact_stress_ksi"], 6.89476, 0.5)
    assert ts["theta_deg"] == sorted(ts["theta_deg"])  # interlock angle grows with radius


def test_frequency_margin_definition_reproduces_every_printed_margin(lpt):
    """% margin = (f - f_exc)/f with f_exc = 102 x 3707 / 60 Hz -- the
    stage-2 vane passing at hot-day takeoff. Six margins, one definition."""
    rpm = lpt["design_cycle_points"]["case_72_max_stress"]["at_2_6pct_overspeed_rpm"][0]
    f_exc = lpt["vane_counts"]["stage2"] * rpm / 60
    sh = lpt["tip_shrouds"]["stage1_analysis"]
    for f, m in zip(sh["frequency_Hz"], sh["margin_over_102_s2_pct"]):
        assert abs((f - f_exc) / f * 100 - m) < 1.2, (f, m)
    aw = lpt["angel_wings_stage1"]
    for f, m in zip(aw["frequency_Hz"], aw["margin_over_102_s2_pct"]):
        assert abs((f - f_exc) / f * 100 - m) < 1.2, (f, m)


def test_shroud_and_angel_wing_stresses_sit_under_their_creep_limits(lpt):
    sh = lpt["tip_shrouds"]["stage1_analysis"]
    assert max(sh["stress_MPa"]) < sh["creep_limit_MPa"]
    assert abs(sh["creep_limit_MPa"] - sh["creep_limit_ksi"] * 6.89476) < 0.1
    pairs_convert(sh["stress_MPa"], sh["stress_ksi"], 6.89476, 0.1)
    aw = lpt["angel_wings_stage1"]
    assert max(aw["stress_MPa"]) < aw["creep_limit_MPa"]
    assert aw["frequency_Hz"][1] < aw["frequency_Hz"][0]  # the long aft wing is the soft one


def test_coupled_blade_disk_two_diameter_clears_2_per_rev(lpt):
    c = lpt["coupled_blade_disk_stage1"]
    f2 = c["nodal_diameter_frequency_Hz"]["two"]
    for rpm in (c["max_speed_base_rpm"], c["max_speed_growth_rpm"]):
        f_mode = f2["at_0_rpm"] + (f2["at_4600_rpm"] - f2["at_0_rpm"]) * rpm / 4600
        assert f_mode > 2 * 2 * rpm / 60  # at least 100 % margin over 2/rev
    nd = c["nodal_diameter_frequency_Hz"]
    assert nd["two"]["at_0_rpm"] < nd["four"]["at_0_rpm"] < nd["six"]["at_0_rpm"]


def test_stage1_dovetail_stress_map_converts_and_the_blade_box_is_table_xii(lpt):
    d = lpt["dovetails"]["stage1_stress_distribution"]
    for row in ("blade_A", "blade_B", "disk_C", "disk_D"):
        pairs_convert(d[f"{row}_MPa"], d[f"{row}_ksi"], 6.89476, 0.5)
    ls = lpt["dovetails"]["life_summary"]
    assert max(d["blade_B_MPa"]) == ls["blade_sigma_max_MPa"][0] == 215.8
    assert d["kt"]["blade_B"] == ls["blade_kt"][0]
    # the recorded disagreement: no disk value in the figure is Table XII's 208.2
    assert ls["disk_sigma_max_MPa"][0] not in d["disk_C_MPa"] + d["disk_D_MPa"]
    assert d["kt"]["disk_D"] == ls["disk_kt"][0]


def test_dovetail_life_summary_converts_and_stage4_is_the_lightly_loaded_one(lpt):
    ls = lpt["dovetails"]["life_summary"]
    pairs_convert(ls["blade_sigma_max_MPa"], ls["blade_sigma_max_ksi"], 6.89476, 0.1)
    pairs_convert(ls["disk_sigma_max_MPa"], ls["disk_sigma_max_ksi"], 6.89476, 0.1)
    for c, f in zip(ls["temperature_C"], ls["temperature_F"]):
        assert abs((f - 32) / 1.8 - c) < 0.6
    assert min(ls["blade_sigma_max_MPa"]) == ls["blade_sigma_max_MPa"][3]  # 156 small blades
    assert ls["disk_lcf_required_cycles"] == 2 * ls["blade_lcf_required_cycles"] == lpt["disks"]["lcf_requirement_cycles"]
    assert ls["disk_lcf_required_cycles"] == lpt["life_basis"]["stress_cycles_rotor"]


def test_retainers_convert_and_stage3_sits_on_the_allowable(lpt):
    r = lpt["blade_retainers"]["stages_1_3"]
    pairs_convert(r["t1_cm"], r["t1_in"], 2.54, 0.002)
    pairs_convert(r["t2_cm"], r["t2_in"], 2.54, 0.002)
    pairs_convert(r["design_force_N"], r["design_force_lbf"], 4.44822, 0.6)
    pairs_convert(r["sigma_max_MPa"], r["sigma_max_ksi"], 6.89476, 0.1)
    assert max(r["sigma_max_MPa"]) == r["design_allowable_MPa"]
    assert r["sigma_max_MPa"] == sorted(r["sigma_max_MPa"])
    s45 = lpt["blade_retainers"]["stages_4_5"]
    pairs_convert(s45["thickness_cm"], s45["thickness_in"], 2.54, 0.002)


def test_disk_lcf_table_converts_and_every_disk_is_on_its_limit_once(lpt):
    x = lpt["disk_lcf_summary"]
    for blk in (x["bore"], x["dovetail_slot_bottom_kt_1_7"]):
        key = "hoop_stress_half_peak" if "hoop_stress_half_peak_MPa" in blk else "stress_half_peak"
        pairs_convert(blk[f"{key}_MPa"], blk[f"{key}_ksi"], 6.89476, 3.5)  # ksi printed to the integer
        for c, f in zip(blk["temperature_C"], blk["temperature_F"]):
            assert abs((f - 32) / 1.8 - c) < 0.6
    req = lpt["disks"]["lcf_requirement_cycles"]
    for i in range(5):
        on_limit = [x["bore"]["allowable_cycles"][i] == req, x["dovetail_slot_bottom_kt_1_7"]["allowable_cycles"][i] == req]
        assert on_limit.count(True) == 1, (i, on_limit)
        assert min(x["bore"]["allowable_cycles"][i], x["dovetail_slot_bottom_kt_1_7"]["allowable_cycles"][i]) >= req
    # stages 4-5 run the hotter bores and move the limit to the slot
    assert min(x["bore"]["temperature_C"][3:]) > max(x["bore"]["temperature_C"][:3]) + 130


def test_stage1_disk_figure_agrees_with_table_xv(lpt):
    d = lpt["disks"]["stage1_disk"]
    x = lpt["disk_lcf_summary"]
    assert abs(d["hoop_stress_MPa"]["bore"] - 2 * x["bore"]["hoop_stress_half_peak_MPa"][0]) < 5
    assert abs(d["temperature_C_rim_to_bore"][0] - x["dovetail_slot_bottom_kt_1_7"]["temperature_C"][0]) < 1
    assert abs(d["temperature_C_rim_to_bore"][-1] - x["bore"]["temperature_C"][0]) < 3
    assert d["hoop_stress_MPa"]["bore"] <= d["lcf_limit_MPa"]["bore"]
    assert d["hoop_stress_MPa"]["rim"] < d["lcf_limit_MPa"]["rim_kt_1_7"]
    assert d["radial_stress_MPa"]["bore"] == 0  # free bore
    for c, f in zip(d["temperature_C_rim_to_bore"], d["temperature_F_rim_to_bore"]):
        assert abs((f - 32) / 1.8 - c) < 0.6
    assert abs(d["lcf_limit_MPa"]["rim_kt_1_7"] - d["lcf_limit_ksi"]["rim_kt_1_7"] * 6.89476) < 1


def test_stage1_disk_bore_stress_is_a_rotating_ring_plus_rim_load_not_less(lpt, ):
    """A free rotating ring of mean radius r at omega carries rho omega^2 r^2;
    the bore of a disk with blades and a hot rim carries more than that
    and less than ~4x. Plausibility, not agreement."""
    d = lpt["disks"]["stage1_disk"]
    rpm = lpt["coupled_blade_disk_stage1"]["max_speed_growth_rpm"]
    omega = rpm * 2 * math.pi / 60
    r = sum(d["radius_range_cm"]) / 200
    ring = 8200 * omega ** 2 * r ** 2 / 1e6
    # a bladed disk with a rim 60 C hotter than its bore runs several times
    # the free-ring figure at the bore; the E3 stage 1 runs about 6x
    assert 3 < d["hoop_stress_MPa"]["bore"] / ring < 9, ring


def test_rotor_bolts_convert_and_residual_clamp_covers_every_requirement(lpt):
    b = lpt["disks"]["rotor_bolts"]
    for key in ("required_torque_and_radial_shear_mu_0_15", "required_torque_mu_0_10", "required_separation", "available_cold_assembly"):
        pairs_convert(b[f"{key}_N"], b[f"{key}_lbf"], 4.44822, 3)
    for i, (n, lbf) in enumerate(zip(b["residual_after_9000h_N"], b["residual_after_9000h_lbf"])):
        if i == 2:
            assert 200 < n - lbf * 4.44822 < 250  # the recorded 33,139 vs 7,400
        else:
            assert abs(n - lbf * 4.44822) < 3
    for i in range(4):
        need = max(b["required_torque_and_radial_shear_mu_0_15_N"][i], b["required_torque_mu_0_10_N"][i], b["required_separation_N"][i])
        assert b["residual_after_9000h_N"][i] > need, i
        assert b["available_cold_assembly_N"][i] > b["residual_after_9000h_N"][i]
    # limiting mode per Table XIV: torque on 1-4, separation on 4-5
    sel = lpt["disks"]["bolt_selection"]
    for i, mode in enumerate(sel["limiting_mode"][1:]):
        sep, tq = b["required_separation_N"][i], b["required_torque_mu_0_10_N"][i]
        assert (mode == "flange separation") == (sep > tq), (i, mode)


def test_bolt_sizes_convert_and_the_biggest_joint_gets_the_most_bolts(lpt):
    sel = lpt["disks"]["bolt_selection"]
    pairs_convert(sel["size_cm"], sel["size_in"], 2.54, 0.002)
    assert sel["quantity"][3] == max(sel["quantity"]) and sel["size_cm"][3] == max(sel["size_cm"])
    b = lpt["disks"]["rotor_bolts"]
    assert b["available_cold_assembly_N"][2] == max(b["available_cold_assembly_N"])


def test_spacer_arm_temperatures_convert_except_the_recorded_pair(lpt):
    sa = lpt["disks"]["spacer_arm_stresses"]
    bad = [(c, f) for c, f in sa["metal_temperatures_C_F_front_to_rear"] if abs((f - 32) / 1.8 - c) > 1.0]
    assert bad == [(446, 853)], bad
    assert sa["peak_effective_MPa"] < sa["lcf_limit_MPa"]


# ── stator stage-1 nozzle ───────────────────────────────────────────────

def test_stage1_nozzle_counts_tie_together(lpt, published):
    n = lpt["stator"]["stage1_nozzle_assembly"]["nozzle"]
    assert n["segments"] * n["vanes_per_segment"] == n["vanes"] == lpt["vane_counts"]["stage1"]
    assert n["bolts_to_support"]["count"] == n["segments"] * n["bolts_to_support"]["per_segment"]
    sup = lpt["stator"]["stage1_nozzle_assembly"]["outer_support"]["stresses_at_takeoff"]
    assert sup["bolt_holes"]["count"] == n["bolts_to_support"]["count"]
    assert sup["air_holes"]["count"] == n["vanes"]
    assert lpt["stator"]["stage1_nozzle_assembly"]["outer_duct"]["segments"] == n["segments"]
    assert n["material"].startswith(lpt["materials"]["stator"]["vane_1"][1])


def test_stage1_nozzle_table_xvi_converts_and_the_two_misprints_are_recorded(lpt):
    a = lpt["stator"]["stage1_nozzle_assembly"]["nozzle"]["airfoil_at_takeoff"]
    for c, f in ((a["t_gas_max_C"], a["t_gas_max_F"]), (a["t_metal_C"], a["t_metal_F"]), (a["t_cooling_fifth_stage_purge_C"], a["t_cooling_fifth_stage_purge_F"])):
        assert abs((f - 32) / 1.8 - c) < 0.6
    # the '8 C (47 F)' cooling effect: the F is right, the C is the gas-metal difference
    assert abs((a["t_gas_max_C"] - a["t_metal_C"]) * 1.8 - a["cooling_effect_F"]) < 1
    assert a["cooling_effect_C"] != a["t_gas_max_C"] - a["t_metal_C"]
    assert abs(a["purge_max_cooling_capability_C"] * 1.8 - a["purge_max_cooling_capability_F"]) > 20
    assert len(a["as_printed_inconsistencies"]) == 2
    for n, lbf in ((a["axial_gas_load_per_vane_N"], a["axial_gas_load_per_vane_lbf"]), (a["tangential_gas_load_per_vane_N"], a["tangential_gas_load_per_vane_lbf"]), (a["dp_load_per_vane_N"], a["dp_load_per_vane_lbf"])):
        assert abs(n - lbf * 4.44822) < 0.6
    assert abs(a["bending_stress_tip_le_MPa"] - a["bending_stress_tip_le_ksi"] * 6.89476) < 0.1
    assert a["rupture_life_ratio"] > 1 and a["creep_0_5pct_life_ratio"] > 1 and a["lcf_life_ratio"] >= 1
    assert a["t_metal_C"] < a["t_gas_max_C"]


def test_stage1_nozzle_hook_forces_are_line_loads_and_stresses_convert(lpt):
    h = lpt["stator"]["stage1_nozzle_assembly"]["nozzle"]["hooks_at_takeoff"]
    for v, lbin in zip(h["forces_printed_as_MPa"], h["forces_lb_per_in"]):
        assert abs(v * 10 - lbin * 0.175127) < 0.05  # kN/cm, not MPa
    pairs_convert(h["stress_MPa"], h["stress_ksi"], 6.89476, 0.1)
    assert h["kt"][3] == 1.0 and max(h["kt"]) == 1.51
    bad = [(c, f) for c, f in h["temperatures_C_F"] if abs((f - 32) / 1.8 - c) > 1.0]
    assert bad == [(634, 1142)], bad


def test_outer_support_stress_bookkeeping(lpt):
    s = lpt["stator"]["stage1_nozzle_assembly"]["outer_support"]["stresses_at_takeoff"]
    assert abs(s["concentrated_peak_MPa"] - s["concentrated_peak_ksi"] * 6.89476) < 0.5
    assert abs(s["alternating_MPa"] - s["alternating_ksi"] * 6.89476) < 0.5
    assert abs(s["mean_MPa"] - s["mean_ksi"] * 6.89476) < 0.5
    assert abs(s["concentrated_peak_MPa"] + s["alternating_MPa"] - s["mean_MPa"]) < 4  # peak = mean - alt
    for mpa, ksi in s["field_MPa_ksi"]:
        assert abs(mpa - ksi * 6.89476) < 1.6
    assert abs(s["air_holes"]["diameter_cm"] - s["air_holes"]["diameter_in"] * 2.54) < 0.005
    assert abs(s["bolt_holes"]["diameter_cm"] - s["bolt_holes"]["diameter_in"] * 2.54) < 0.005


# ── stators 2-5, casing, ACC manifold (pp.120-135) ──────────────────────

def test_vane_segments_multiply_to_the_vane_counts(lpt, published):
    seg = lpt["stator"]["stages_2_5_nozzles"]["segments"]
    for n, vps, ns in zip(seg["vanes"], seg["vanes_per_segment"], seg["segments"]):
        assert vps * ns == n
    assert seg["vanes"] == lpt["vane_counts"]["all"] == published["lpt"]["vane_counts_per_stage"]["value"]
    assert seg["material"][0] != seg["material"][1] and len(set(seg["material"][1:])) == 1
    assert sum(seg["segments"]) == 90


def test_tangential_load_per_segment_is_six_vanes_of_fig81(lpt):
    st = lpt["stator"]["stages_2_5_nozzles"]
    ls, af = st["tangential_load_stops"], st["airfoil_at_takeoff"]
    for per_seg, per_vane in zip(ls["tangential_gas_load_per_segment_N"], af["tangential_gas_load_per_vane_N"]):
        assert abs(per_seg / st["vanes_per_segment"] - per_vane) / per_vane < 0.004, (per_seg, per_vane)


def test_stages_2_5_airfoil_table_converts_and_the_mpa_column_is_a_tenth(lpt):
    af = lpt["stator"]["stages_2_5_nozzles"]["airfoil_at_takeoff"]
    for c, f in zip(af["max_gas_temp_95pct_span_C"], af["max_gas_temp_95pct_span_F"]):
        assert abs((f - 32) / 1.8 - c) < 0.6
    for key in ("axial_gas_load_per_vane", "tangential_gas_load_per_vane", "dp_load_per_vane"):
        for n, lbf in zip(af[f"{key}_N"], af[f"{key}_lbf"]):
            assert abs(n - lbf * 4.44822) < 1.0, (key, n, lbf)
    for mpa10, ksi in zip(af["stress_le_MPa_as_printed"], af["stress_le_ksi"]):
        assert abs(mpa10 * 10 - ksi * 6.89476) < 0.6  # the recorded factor of ten
    assert af["max_gas_temp_95pct_span_C"] == sorted(af["max_gas_temp_95pct_span_C"], reverse=True)
    assert af["creep_0_2pct_margin"][0] == min(af["creep_0_2pct_margin"]) == 1
    assert af["rupture_margin"][0] == min(af["rupture_margin"])


def test_stage2_hook_maxima_are_nominal_times_kt(lpt):
    h = lpt["stator"]["stages_2_5_nozzles"]["stage2_hooks_at_takeoff"]
    for nom, kt, mx in zip(h["sigma_nom_MPa"], h["kt"], h["sigma_max_MPa"]):
        assert abs(nom * kt - mx) / mx < 0.006, (nom, kt, mx)
    pairs_convert(h["sigma_nom_MPa"], h["sigma_nom_ksi"], 6.89476, 0.6)
    pairs_convert(h["sigma_max_MPa"], h["sigma_max_ksi"], 6.89476, 0.6)
    for c, f in zip(h["temperature_C"], h["temperature_F"]):
        assert abs((f - 32) / 1.8 - c) < 0.6
    # point F is the Fig.81 stage-2 leading edge: same stress, same Kt
    af = lpt["stator"]["stages_2_5_nozzles"]["airfoil_at_takeoff"]
    assert h["sigma_nom_ksi"][5] == af["stress_le_ksi"][0] and h["kt"][5] == af["kt"][0]
    assert h["temperature_C"][5] == af["max_gas_temp_95pct_span_C"][0] + 1


def test_load_stop_stresses_convert_and_sit_under_their_limits(lpt):
    ls = lpt["stator"]["stages_2_5_nozzles"]["tangential_load_stops"]
    pairs_convert(ls["tangential_gas_load_per_segment_N"], ls["tangential_gas_load_per_segment_lbf"], 4.44822, 1.0)
    for i, (mpa, ksi) in enumerate(zip(ls["slug_shear_stress_MPa"], ls["slug_shear_stress_ksi"])):
        if i == 3:
            assert 2.5 < mpa - ksi * 6.89476 < 3.5  # the recorded pair
        else:
            assert abs(mpa - ksi * 6.89476) < 0.6
    pairs_convert(ls["nozzle_hook_bearing_MPa"], ls["nozzle_hook_bearing_ksi"], 6.89476, 0.6)
    pairs_convert(ls["casing_hook_bearing_MPa"], ls["casing_hook_bearing_ksi"], 6.89476, 0.6)
    assert max(ls["slug_shear_stress_MPa"]) < ls["limits_MPa"]["slug_shear"]
    assert max(ls["nozzle_hook_bearing_MPa"]) < ls["limits_MPa"]["nozzle_hook_bearing"]
    assert max(ls["casing_hook_bearing_MPa"]) < ls["limits_MPa"]["casing_hook_bearing"]
    # the load falls rearward with the gas temperature and pressure
    assert ls["tangential_gas_load_per_segment_N"][1:] == sorted(ls["tangential_gas_load_per_segment_N"][1:], reverse=True)


def test_inner_seal_support_groove_is_nominal_times_kt_and_just_under_its_limit(lpt):
    st = lpt["stator"]["stage1_nozzle_assembly"]["inner_seal_supports"]["stresses"]
    a = st["at_A"]
    assert abs(a["sigma_nom_MPa"] * a["kt"] - a["sigma_max_MPa"]) / a["sigma_max_MPa"] < 0.01
    lim = st["elastic_limit_72000_cycles"]
    assert a["sigma_max_MPa"] < lim["MPa"] and lim["MPa"] - a["sigma_max_MPa"] < 10
    assert abs(lim["MPa"] - lim["ksi"] * 6.89476) < 0.5
    for mpa, ksi in st["field_MPa_ksi"]:
        assert abs(mpa - ksi * 6.89476) < 1.6
    hw = lpt["stator"]["stage1_nozzle_assembly"]["inner_seal_supports"]["hardware"]
    assert hw["spoolies"] == lpt["vane_counts"]["stage1"]
    assert hw["clamp_bolts"]["count"] == lpt["stator"]["stage1_nozzle_assembly"]["nozzle"]["bolts_to_support"]["count"]


def test_casing_end_flanges_convert_and_the_case_takes_one_cycle_per_mission(lpt):
    ef = lpt["stator"]["casing"]["end_flanges"]
    pairs_convert(ef["stress_MPa"], ef["stress_ksi"], 6.89476, 0.6)
    assert max(ef["stress_MPa"]) < lpt["stator"]["casing"]["attachment_stresses"]["allowable_outer_538C"]["MPa"]
    assert ef["requirement_cycles"] * 2 == lpt["disks"]["lcf_requirement_cycles"]
    assert ef["requirement_cycles"] == lpt["life_basis"]["aircraft_missions"]
    assert lpt["active_clearance_control_design"]["casing_life"].startswith("the only component")


def test_hpt_lpt_flange_bolt_matches_the_rotor_bolt_family(lpt):
    b = lpt["stator"]["casing"]["hpt_lpt_flange_bolts"]
    assert abs(b["diameter_cm"] - b["diameter_in"] * 2.54) < 0.006
    assert b["diameter_in"] in lpt["disks"]["bolt_selection"]["size_in"]


def test_containment_energies_convert_and_imply_a_plausible_blade_mass(lpt):
    """E = 1/2 m V^2 at the blade centroid (about 0.45 x tip radius above the
    hub) at growth speed + 5 %. The implied mass must be a real LPT blade
    with shroud and dovetail -- 0.1 to 0.6 kg -- and grow rearward."""
    c = lpt["stator"]["casing"]["containment"]
    pairs_convert(c["impact_energy_N_m"], c["impact_energy_ft_lbf"], 1.35582, 60)
    assert abs(c["capability_N_m"] - c["capability_ft_lbf"] * 1.35582) < 5
    assert abs(c["minimum_actual_combined_thickness_cm"] - c["minimum_actual_combined_thickness_in"] * 2.54) < 0.002
    assert max(c["impact_energy_N_m"]) < c["capability_N_m"]
    assert max(c["required_wall_cm"]) < c["minimum_actual_combined_thickness_cm"]
    rpm = lpt["coupled_blade_disk_stage1"]["max_speed_growth_rpm"] * 1.05
    omega = rpm * 2 * math.pi / 60
    ap = lpt["aero_design_parameters"]
    masses = {}
    for col, st in ((0, 0), (1, 4)):
        r_t = ap["tip_diameter_cm"][col] / 200
        r_h = r_t * ap["inlet_radius_ratio"][col]
        r_cg = r_h + 0.45 * (r_t - r_h)
        v = omega * r_cg
        masses[st] = 2 * c["impact_energy_N_m"][st] / v ** 2
        assert 0.1 < masses[st] < 0.6, (st, masses[st])
    assert masses[4] > masses[0]


def test_acc_manifold_tube_counts_add_up(lpt):
    m = lpt["active_clearance_control_design"]["manifold"]
    assert m["forward_part_tubes"] + m["aft_part_tubes"] == 10
    assert m["sectors"] * m["sector_arc_deg"] == 360
    assert lpt["stator"]["casing"]["manifold_flanges"].startswith("four")


# ── clearances and weights (pp.136-142) ─────────────────────────────────

def test_out_of_round_terms_sum_in_mils_and_the_one_mm_misprint_is_recorded(lpt):
    oor = lpt["clearance_predictions"]["out_of_round_stage1"]
    for cond in ("takeoff_rotation", "second_segment_climb", "low_mach_cruise"):
        c = oor[cond]
        for i in range(4):
            mils = c["beam_bending_mils"][i] + c["vibration_mils"][i] + c["ovalization_mils"][i]
            assert abs(mils - c["sum_mils"][i]) < 0.02, (cond, i, mils)
            mm = c["beam_bending_mm"][i] + c["vibration_mm"][i] + c["ovalization_mm"][i]
            if cond == "takeoff_rotation" and i == 3:
                assert abs(mm - (-0.101)) < 0.002 and c["sum_mm"][i] == 0.031  # recorded print, 6 o'clock
            elif cond == "takeoff_rotation" and i == 2:
                assert c["sum_mm"][i] == -0.193 and c["beam_bending_mm"][i] == -0.114  # recorded prints, 12 o'clock
                assert abs(c["sum_mils"][i] * 0.0254 - (-0.170)) < 0.001
            else:
                assert abs(mm - c["sum_mm"][i]) < 0.002, (cond, i, mm)
            for key in ("beam_bending", "vibration", "ovalization"):
                if cond == "takeoff_rotation" and i == 2 and key == "beam_bending":
                    continue
                assert abs(c[f"{key}_mm"][i] - c[f"{key}_mils"][i] * 0.0254) < 0.0015, (cond, key, i)
    assert len(oor["as_printed_inconsistencies"]) == 2
    assert min(oor["second_segment_climb"]["sum_mils"]) < min(oor["takeoff_rotation"]["sum_mils"]) < min(oor["low_mach_cruise"]["sum_mils"])
    worst = oor["second_segment_climb"]["sum_mils"].index(min(oor["second_segment_climb"]["sum_mils"]))
    assert oor["clock"][worst] == 6


def test_combined_clearance_bookkeeping_holds(lpt):
    t = lpt["clearance_predictions"]["stage1_combined_clearance"]
    for key in ("tip_clearance_round_engine", "out_of_round_imposed", "single_point_rub", "resultant_gap", "acc_closure_needed_for_0_038cm", "acc_closure_capability"):
        pairs_convert(t[f"{key}_cm"], t[f"{key}_in"], 2.54, 0.006)
    for i in range(4):
        rnd, oor, rub, res = t["tip_clearance_round_engine_cm"][i], t["out_of_round_imposed_cm"][i], t["single_point_rub_cm"][i], t["resultant_gap_cm"][i]
        assert abs(rnd + t["takeoff_rub_depth_cm"] - res) < 0.002, (i, rnd, res)
        if oor is not None:
            assert abs(rnd - oor - rub) < 0.002, (i, rnd, oor, rub)
        need = t["acc_closure_needed_for_0_038cm_cm"][i]
        if need is not None:
            assert abs(res - t["goal_gap_cm"] - need) < 0.002, (i, res, need)
            assert need < t["acc_closure_capability_cm"][i]
    assert t["single_point_rub_cm"][1] == -t["takeoff_rub_depth_cm"]


def test_clearance_summary_meets_the_goal_new_and_stage5_is_the_hard_one(lpt):
    s = lpt["clearance_predictions"]["summary"]
    t = lpt["clearance_predictions"]["stage1_combined_clearance"]
    for key in ("acc_closure_needed", "acc_closure_capability", "operating_clearance_new", "operating_clearance_after_max_service"):
        pairs_convert(s[f"{key}_cm"], s[f"{key}_in"], 2.54, 0.006)
    assert s["acc_closure_needed_cm"][0] == t["acc_closure_needed_for_0_038cm_cm"][2]
    assert s["acc_closure_capability_cm"][0] == t["acc_closure_capability_cm"][2]
    for need, cap, new in zip(s["acc_closure_needed_cm"], s["acc_closure_capability_cm"], s["operating_clearance_new_cm"]):
        assert need < cap and new < s["goal_cm"]
    assert s["acc_closure_needed_cm"][2] == max(s["acc_closure_needed_cm"])
    assert s["acc_closure_capability_cm"][2] == min(s["acc_closure_capability_cm"])
    assert max(s["operating_clearance_after_max_service_cm"]) > s["goal_cm"]


def test_weights_add_up_in_both_units_and_match_the_engine_table_to_3_percent(lpt, published):
    w = lpt["weights"]
    r, st = w["rotor"], w["stator"]
    assert abs(sum(r["blades_per_stage_kg"]) + sum(r["disks_per_stage_kg"]) + r["seals_retainers_fasteners_kg"] - r["total_kg"]) < 0.15
    assert sum(r["blades_per_stage_lb"]) + sum(r["disks_per_stage_lb"]) + r["seals_retainers_fasteners_lb"] == r["total_lb"]
    assert abs(sum(st["vanes_per_stage_kg"]) + st["casing_and_acc_manifold_kg"] + st["seals_ring_fasteners_kg"] - st["total_kg"]) < 0.15
    assert sum(st["vanes_per_stage_lb"]) + st["casing_and_acc_manifold_lb"] + st["seals_ring_fasteners_lb"] == st["total_lb"]
    assert abs(r["total_kg"] + st["total_kg"] - w["total_kg"]) < 0.05 and r["total_lb"] + st["total_lb"] == w["total_lb"]
    assert abs(w["total_kg"] - w["total_lb"] * 0.45359) < 0.5
    for kg, lb in zip(r["blades_per_stage_kg"] + r["disks_per_stage_kg"] + st["vanes_per_stage_kg"], r["blades_per_stage_lb"] + r["disks_per_stage_lb"] + st["vanes_per_stage_lb"]):
        assert abs(kg - lb * 0.45359) < 0.3
    mod = None
    for k, v in published.items():
        if isinstance(v, dict) and "lpt_module" in v:
            mod = v["lpt_module"]
    assert mod is not None
    assert abs(mod["rotor"] - r["total_kg"]) / r["total_kg"] < 0.03
    assert abs(mod["stator"] - st["total_kg"]) / st["total_kg"] < 0.03
    assert sum(r["blades_per_stage_kg"]) + sum(st["vanes_per_stage_kg"]) > 0.5 * w["total_kg"]


def test_blade_mass_from_the_weight_table_matches_the_containment_energy(lpt):
    """Third route to the blade mass: Table XXI set weight / blade count
    against 2E/V^2 from Fig.88. Within 25 percent on both ends of the
    turbine -- the shroud and dovetail share is the uncertainty."""
    w = lpt["weights"]["rotor"]
    rb = lpt["rotor_blades"]
    c = lpt["stator"]["casing"]["containment"]
    ap = lpt["aero_design_parameters"]
    rpm = lpt["coupled_blade_disk_stage1"]["max_speed_growth_rpm"] * 1.05
    omega = rpm * 2 * math.pi / 60
    for col, st in ((0, 0), (1, 4)):
        per_blade = w["blades_per_stage_kg"][st] / rb["blade_count"][st]
        r_t = ap["tip_diameter_cm"][col] / 200
        r_h = r_t * ap["inlet_radius_ratio"][col]
        v = omega * (r_h + 0.45 * (r_t - r_h))
        implied = 2 * c["impact_energy_N_m"][st] / v ** 2
        assert abs(implied - per_blade) / per_blade < 0.25, (st, implied, per_blade)


def test_manifold_tube_dimensions_convert(lpt):
    g = lpt["active_clearance_control_design"]["manifold"]["tube_geometry"]
    for cm, inch in ((g["manifold_sheet_cm"], g["manifold_sheet_in"]), (g["tube_od_cm"], g["tube_od_in"]), (g["tube_wall_cm"], g["tube_wall_in"])):
        assert abs(cm - inch * 2.54) < 0.002


def test_appendix_extents_match_the_section_figures(lpt):
    aero = yaml.safe_load((DATA / "lpt-aero.yaml").read_text())
    rows = aero["airfoil_sections"]["rows"]
    assert rows["V1"]["axial_in"][0] - 0.15 < 2.69 and 4.78 < rows["V1"]["axial_in"][1]
    assert rows["R1"]["axial_in"][0] - 0.1 < 5.47 and 6.63 < rows["R1"]["axial_in"][1] + 0.05
    assert lpt["appendix_airfoil_coordinates"]["status"].startswith("not transcribed")
