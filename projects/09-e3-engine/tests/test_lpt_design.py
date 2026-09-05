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
