"""HPT mechanical design (CR-167955 section 5), checked against itself,
the cooling file and the LPT report. Plain interpreter."""

from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def mech():
    return yaml.safe_load((DATA / "hpt-mechanical.yaml").read_text())


@pytest.fixture(scope="module")
def lpt():
    return yaml.safe_load((DATA / "lpt-design.yaml").read_text())


def f_to_c(f):
    return (f - 32) / 1.8


# ── lives ───────────────────────────────────────────────────────────────

def test_design_lives_double_with_one_repair_and_disks_get_twice_the_flowpath(mech):
    d = mech["design_lives"]
    fp, dk = d["flowpath_components_and_blade_retainers"], d["disks_shafts_seal_disk"]
    assert fp[2] == 2 * fp[0] and fp[3] == 2 * fp[1]
    assert dk[2] == 2 * dk[0] and dk[3] == 2 * dk[1]
    assert dk[0] == 2 * fp[0]
    assert fp[0] == fp[1] and dk[0] == dk[1]  # one cycle per hour in this report
    assert mech["rotor_components"]["forward_hp_shaft"]["fps_lcf_life_cycles"] == dk[3]
    assert mech["rotor_components"]["inducer_disk"]["lcf_objective_cycles"] == dk[3]


def test_hpt_and_lpt_agree_on_36000_cycles_by_different_missions(mech, lpt):
    hpt_cycles = mech["design_lives"]["disks_shafts_seal_disk"][3]
    assert hpt_cycles == lpt["life_basis"]["aircraft_missions"]
    # the LPT counts two rotor cycles per mission and reaches 72,000; the HPT one per flight hour
    assert lpt["disks"]["lcf_requirement_cycles"] == 2 * hpt_cycles


# ── materials ───────────────────────────────────────────────────────────

def test_material_selections_are_consistent_between_figures_table_and_text(mech):
    m = mech["materials"]
    r, s = m["rotor_parts"], m["static_parts"]
    assert r["stage1_blade"] == r["stage2_blade"] == "Rene 150"
    assert r["disk1"] == r["disk2"] == r["outer_liner"] == "Rene 95"
    for part in ("interstage_seal_disk", "impeller", "inducer_seal_disk", "boltless_retainer"):
        assert r[part] == "AF115", part
    assert r["hpt_shaft"] == r["aft_shaft_and_disk"] == "Inco 718"
    rows = {row[0]: row for row in m["table_xvi"]["rows"]}
    assert rows["stage1_and_2_blades"][1] == "Rene 150" and "DS" in rows["stage1_and_2_blades"][2]
    assert rows["stage1_and_2_disks"][1] == "Rene 95" and rows["stage1_and_2_disks"][2] == "PM"
    assert rows["impeller"][1] == "AF115" and rows["interstage_seal_disk_and_spacer_retainer"][1] == "AF115"
    assert rows["stage1_vanes"][1] == "MA754" and rows["stage1_bands"][1] == "MAR-M-509"
    assert s["stage1_nozzle"] == {"bands": "MAR-M-509", "airfoils": "MA754"}
    assert rows["stage2_vane"][1] == "Rene 150" and rows["stage2_vane_band"][1] == "Rene 80"
    assert s["stage2_nozzle"]["bands"] == "Rene 80"
    assert "Rene 77" in rows["stage2_shrouds"][1] and "Rene 77" in s["stage2_shroud"]
    assert rows["forward_shaft"][1] == "Inco 718" and rows["aft_shaft_disk"][1] == "Inco 718"
    assert "903A" in rows["inducer_cdp_seal"][1] and "903A" in s["inducer_and_cdp_seal"]


def test_coating_temperatures_convert_and_the_margin_is_the_difference(mech):
    c = mech["materials"]["blade_coating"]["cf6_50_evidence"]
    assert abs(f_to_c(c["predicted_le_temperature_F"]) - c["predicted_le_temperature_C"]) < 0.6
    assert abs(f_to_c(c["e3_stage1_max_surface_temperature_F"]) - c["e3_stage1_max_surface_temperature_C"]) < 0.6
    assert c["predicted_le_temperature_C"] - c["e3_stage1_max_surface_temperature_C"] == c["margin_below_cf6_test_C"]
    assert abs(c["margin_below_cf6_test_F"] / 1.8 - c["margin_below_cf6_test_C"]) < 0.5


# ── rotor temperatures and stresses ─────────────────────────────────────

def test_every_rotor_temperature_triple_converts(mech):
    t = mech["rotor_temperatures"]
    assert set(t["locations_C"]) == set(t["locations_F"])
    for loc, cs in t["locations_C"].items():
        for c, f in zip(cs, t["locations_F"][loc]):
            assert abs(f_to_c(f) - c) < 0.75, (loc, c, f)  # both columns rounded to the degree


def test_bores_are_coldest_at_40s_and_shanks_hottest(mech):
    t = mech["rotor_temperatures"]["locations_C"]
    for bore in ("stage1_disk_bore", "stage2_disk_bore", "stage1_disk_web", "forward_shaft_cone", "aft_shaft"):
        assert t[bore][0] < t[bore][1] and t[bore][0] < t[bore][2], bore
        assert t[bore][1] - t[bore][0] > 100, bore  # the transient gradient
    for hot in ("stage1_blade_shank", "inducer_outer"):
        assert t[hot][0] == max(t[hot]), hot
    assert max(v[0] for v in t.values()) == t["stage1_blade_shank"][0]


def test_every_stress_triple_converts_except_the_recorded_one(mech):
    s = mech["rotor_effective_stress"]
    bad = []
    for loc, mpas in s["locations_MPa"].items():
        for mpa, ksi in zip(mpas, s["locations_ksi"][loc]):
            if abs(mpa - ksi * 6.89476) > 4.0:
                bad.append(loc)
                break
    assert bad == ["stage1_disk_bore"], bad
    mx = s["maximum"]
    assert max(max(v) for v in s["locations_MPa"].values()) == mx["MPa"]
    assert abs(mx["MPa"] - mx["ksi"] * 6.89476) < 4


def test_stresses_fall_from_40s_to_1700s_where_the_transient_governs(mech):
    s = mech["rotor_effective_stress"]["locations_MPa"]
    for loc in ("impeller_to_stage1_forward_arm", "stage1_blade_retainer", "stage2_blade_retainer", "stage2_disk_bore_aft", "outer_liner"):
        assert s[loc][0] > s[loc][2], loc
    # the shaft numbers quoted in the text are on the figure
    fs = mech["rotor_components"]["forward_hp_shaft"]
    assert fs["max_stress_forward_flange_face_MPa"] in [v[0] for v in s.values()]
    assert abs(fs["max_stress_forward_flange_face_MPa"] - fs["max_stress_forward_flange_face_ksi"] * 6.89476) < 1
    assert abs(fs["max_concentrated_stress_aft_flange_bolt_circle_MPa"] - fs["max_concentrated_stress_aft_flange_bolt_circle_ksi"] * 6.89476) < 1
    ol = mech["rotor_components"]["outer_liner"]
    assert abs(ol["max_stress_MPa"] - ol["max_stress_ksi"] * 6.89476) < 1


def test_forward_shaft_lives_order_by_material(mech):
    fs = mech["rotor_components"]["forward_hp_shaft"]
    assert fs["lcf_life_inco_718_cycles"] < fs["lcf_life_standard_inco_718_3sigma_cycles"] < fs["fps_lcf_life_cycles"]
    assert fs["max_concentrated_stress_aft_flange_bolt_circle_MPa"] < fs["max_stress_forward_flange_face_MPa"]


def test_flight_times_are_monotonic_and_the_limiting_ones_are_in_the_list(mech):
    ft = mech["rotor_analysis_conditions"]["flight_times_s"]
    seq = [ft["ground_idle"]] + [ft["ground_idle"] + t for t in ft["transient_takeoff_from_idle"]] + [ft["end_of_max_cruise_from_ground_idle"]] + ft["max_cruise"] + [ft["flight_idle"], ft["thrust_reverse"]]
    assert seq == sorted(seq)
    lim = mech["rotor_analysis_conditions"]["limiting_times_s"]
    assert lim[0] in ft["transient_takeoff_from_idle"] and lim[1] == ft["end_of_max_cruise_from_ground_idle"] and lim[2] in ft["max_cruise"]
    f = mech["rotor_analysis_conditions"]["fig53_transient"]
    assert f["rpm"]["max_takeoff"] == max(f["rpm"].values()) and f["t3_C"]["max_takeoff"] == max(f["t3_C"].values())


def test_analytical_toolset_is_shared_with_the_lpt(mech, lpt):
    progs = mech["analytical_methods"]["programs"]
    assert "CLASS_MASS" in progs and "BOLFAN" in progs and "FINITE" in progs
    assert "CLASS/MASS" in lpt["stator"]["stage1_nozzle_assembly"]["outer_support"]["stresses_at_takeoff"]["src"]
    assert mech["design_criteria"]["creep_limit_total_pct"] == 0.2


# ── impeller and stage-1 disk ───────────────────────────────────────────

def test_impeller_counts_and_fig60_conversions(mech):
    imp = mech["rotor_components"]["impeller_and_stage1_retention"]
    assert imp["stage1_blades"] == imp["seal_plates"] == 76
    assert imp["race_track_holes"] * 2 == imp["stage1_blades"]
    f = imp["fig60"]
    for k, kn in f["line_loads_kN_m"].items():
        assert abs(kn - f["line_loads_lbf_in"][k] * 0.175127) < 0.15, k
    for p in f["points"]:
        assert abs(p["stress_MPa"] - p["stress_ksi"] * 6.89476) < 1.0, p
        assert abs(f_to_c(p["temperature_F"]) - p["temperature_C"]) < 0.6, p
    assert max(p["stress_MPa"] for p in f["points"]) == 1048
    hot = max(p["temperature_C"] for p in f["points"])
    assert hot == 649  # the AF115 ceiling of Table XVI


def test_stage1_disk_fig61_converts_and_point5_is_the_life_limit(mech):
    d = mech["rotor_components"]["stage1_disk"]
    c = d["concentration_points"]
    for i in range(9):
        assert abs(c["nominal_MPa"][i] - c["nominal_ksi"][i] * 6.89476) < 1.0, i
        assert abs(c["kt_sigma_MPa"][i] - c["kt_sigma_ksi"][i] * 6.89476) < 1.0, i
        assert abs(f_to_c(c["temperature_F"][i]) - c["temperature_C"][i]) < 0.6, i
        assert c["kt_sigma_MPa"][i] > c["nominal_MPa"][i]
    kt = [k / n for k, n in zip(c["kt_sigma_MPa"], c["nominal_MPa"])]
    assert all(1.1 < k < 3.1 for k in kt), kt
    i_max = c["kt_sigma_MPa"].index(max(c["kt_sigma_MPa"]))
    assert c["point"][i_max] == 5 and c["lcf_kilocycles"][i_max] == 36
    assert all(v == 100 for j, v in enumerate(c["lcf_kilocycles"]) if j != i_max)
    # the 40-s points are the cold ones; the 875-s points the hot ones
    for t40 in (j for j, v in enumerate(c["critical_time_s"]) if v == 40):
        assert c["temperature_C"][t40] < min(c["temperature_C"][j] for j, v in enumerate(c["critical_time_s"]) if v == 875)
    assert d["posts_and_slots"] == mech["rotor_components"]["impeller_and_stage1_retention"]["stage1_blades"]
    dm = d["dovetail_max"]
    assert abs(dm["stress_MPa"] - dm["stress_ksi"] * 6.89476) < 1.0
    assert dm["lcf_cycles"] == mech["design_lives"]["disks_shafts_seal_disk"][3]


def test_stage1_disk_temperatures_agree_with_fig54_at_875s(mech):
    c = mech["rotor_components"]["stage1_disk"]["concentration_points"]
    web_875 = mech["rotor_temperatures"]["locations_C"]["stage1_disk_web"][1]
    arm_875 = [t for t, s in zip(c["temperature_C"], c["critical_time_s"]) if s == 875]
    assert all(abs(t - web_875) < 30 for t in arm_875), (web_875, arm_875)


# ── Figs.64-70 ──────────────────────────────────────────────────────────

def mpa_ksi_ok(mpa, ksi, tol=1.0):
    return abs(mpa - ksi * 6.89476) < tol


def test_stage1_disk_map_converts_except_the_recorded_pair_and_shares_1103(mech):
    d = mech["rotor_components"]["stage1_disk"]
    sm = d["stress_life_map"]
    bad = [p["where"] for p in sm["points"] + sm["dovetail_inset"] if not mpa_ksi_ok(p["MPa"], p["ksi"], 1.5)]
    assert bad == ["web lower"], bad
    assert max(p["MPa"] for p in sm["dovetail_inset"]) == max(d["concentration_points"]["kt_sigma_MPa"]) == 1103
    bore = next(p for p in sm["points"] if p["where"] == "bore")
    assert bore["MPa"] == 1034 and bore["lcf"].startswith(">")


def test_interstage_seal_disk_converts_except_the_boxed_pair(mech):
    isd = mech["rotor_components"]["interstage_seal_disk"]
    bad = [p["where"] for p in isd["points"] if not mpa_ksi_ok(p["MPa"], p["ksi"], 1.5)]
    assert bad == ["neck (boxed)"], bad
    for p in isd["points"]:
        assert abs(f_to_c(p["F"]) - p["C"]) < 0.75, p
    limiting = [p for p in isd["points"] if p["lcf"] == 36000]
    assert len(limiting) == 1 and limiting[0]["MPa"] == max(p["MPa"] for p in isd["points"])
    assert max(p["C"] for p in isd["points"]) == 708  # the seal arm, gas-washed


def test_retainer_figures_convert_except_the_recorded_temperature(mech):
    r = mech["rotor_components"]["blade_retainers"]
    for st in ("stage1_aft_retainer", "stage2_aft_retainer"):
        for c, f in r[st]["temperatures_C_F"]:
            assert abs(f_to_c(f) - c) < 0.75, (st, c, f)
        for p in r[st]["stress_points"]:
            assert mpa_ksi_ok(p["MPa"], p["ksi"], 1.0), p
    bad = [(p["C"], p["F"]) for p in r["stage1_aft_retainer"]["stress_points"] if abs(f_to_c(p["F"]) - p["C"]) > 0.75]
    assert bad == [(620, 1116)], bad
    for p in r["stage2_aft_retainer"]["stress_points"]:
        assert abs(f_to_c(p["F"]) - p["C"]) < 0.75, p
    # stage 2's retainer runs cooler and is stressed harder than stage 1's
    assert max(p["MPa"] for p in r["stage2_aft_retainer"]["stress_points"]) > max(p["MPa"] for p in r["stage1_aft_retainer"]["stress_points"])
    assert max(c for c, _ in r["stage2_aft_retainer"]["temperatures_C_F"]) < max(c for c, _ in r["stage1_aft_retainer"]["temperatures_C_F"])


def test_stage2_disk_fig69_converts_and_the_air_hole_limits_both_disks(mech):
    c2 = mech["rotor_components"]["stage2_disk"]["concentration_points"]
    c1 = mech["rotor_components"]["stage1_disk"]["concentration_points"]
    for i in range(7):
        assert mpa_ksi_ok(c2["nominal_MPa"][i], c2["nominal_ksi"][i]), i
        assert mpa_ksi_ok(c2["kt_sigma_MPa"][i], c2["kt_sigma_ksi"][i]), i
        assert abs(f_to_c(c2["temperature_F"][i]) - c2["temperature_C"][i]) < 0.75, i
    lim2 = c2["lcf_kilocycles"].index(min(c2["lcf_kilocycles"]))
    lim1 = c1["lcf_kilocycles"].index(min(c1["lcf_kilocycles"]))
    assert c2["location"][lim2] == c1["location"][lim1] == "forward arm air hole"
    assert c2["kt_sigma_MPa"][lim2] == max(c2["kt_sigma_MPa"])
    assert c1["kt_sigma_MPa"][lim1] == max(c1["kt_sigma_MPa"])
    # the highest nominal stress on stage 2 is NOT the limiting point
    assert c2["nominal_MPa"].index(max(c2["nominal_MPa"])) != lim2
    assert min(c2["lcf_kilocycles"]) * 1000 > mech["design_lives"]["disks_shafts_seal_disk"][3]


def test_both_dovetails_sit_on_36000_cycles_at_30s(mech):
    d1 = mech["rotor_components"]["stage1_disk"]["dovetail_max"]
    d2 = mech["rotor_components"]["stage2_disk"]["dovetail_max"]
    assert d1["lcf_cycles"] == 36000
    for p in d2["points"]:
        assert p["lcf"] == 36000 and mpa_ksi_ok(p["MPa"], p["ksi"]) and abs(f_to_c(p["F"]) - p["C"]) < 0.75
    assert abs(d1["stress_MPa"] - max(p["MPa"] for p in d2["points"])) < 10


def test_shaft_materials_and_lives_line_up(mech):
    fwd, aft = mech["rotor_components"]["forward_hp_shaft"], mech["rotor_components"]["aft_shaft_seal_disk"]
    assert fwd["icls_material"] == aft["icls_material"].replace("standard ", "")
    assert fwd["fps_material"].startswith("Super Inco 718") and aft["fps_material"] == "Super Inco 718"
    assert aft["lcf_life_inco_718_3sigma_cycles"] > fwd["lcf_life_standard_inco_718_3sigma_cycles"]
    assert 5 < aft["max_stress_MPa"] - aft["max_stress_ksi"] * 6.89476 < 9  # the recorded pair


# ── Figs.71-72, the stage-1 blade mission ───────────────────────────────

def test_aft_seal_disk_and_stage2_cyanide_convert(mech):
    a = mech["rotor_components"]["aft_shaft_seal_disk"]["fig72"]
    for mpa, ksi in a["points_MPa_ksi"]:
        assert mpa_ksi_ok(mpa, ksi, 3.0), (mpa, ksi)
    assert a["maximum"]["MPa"] == max(p[0] for p in a["points_MPa_ksi"])
    assert abs(f_to_c(a["maximum"]["temperature_F"]) - a["maximum"]["temperature_C"]) < 0.75
    assert a["maximum"]["ksi"] == mech["rotor_components"]["aft_shaft_seal_disk"]["max_stress_ksi"]
    for mpa, ksi in mech["rotor_components"]["stage2_disk_cyanide"]["points_MPa_ksi"]:
        assert mpa_ksi_ok(mpa, ksi, 1.0), (mpa, ksi)


def test_design_mission_sums_to_two_hours_and_matches_the_lpt(mech, lpt):
    dm = mech["stage1_blade"]["design_mission"]
    assert abs(sum(dm["minutes"]) - dm["total_minutes"]) < 0.05
    assert abs(sum(dm["percent"]) - 100) < 0.05
    off = [(mnt, pct) for mnt, pct in zip(dm["minutes"], dm["percent"]) if abs(mnt / dm["total_minutes"] * 100 - pct) > 0.1]
    assert off == [(7.7, 6.2), (5.0, 4.3)], off  # the recorded pair of rows
    assert dm["total_minutes"] == lpt["flight_cycle"]["total_minutes"]
    for ms, kn in zip(dm["climb_airspeed_m_s"], dm["climb_airspeed_knots"]):
        assert abs(ms - kn * 0.514444) < 0.1
    # km/ft pairs, where a range is printed
    for km, ft in zip(dm["altitude_km"], dm["altitude_ft"]):
        if km is None:
            continue
        for k, f in zip(str(km).split("-"), str(ft).split("-")):
            assert abs(float(k) - float(f) * 0.0003048) < 0.006, (k, f)


def test_blade_mission_mix_hours_and_life_fractions(mech):
    mm = mech["stage1_blade"]["rupture_life"]["mission_mix"]
    assert sum(mm["hours_at_point"]) == mm["total_hours"] == mech["stage1_blade"]["life_objective"]["mission_mix_hours"]
    assert abs(sum(mm["pct_life_used"]) - 100) < 0.2
    assert mm["pct_life_used"][0] > mm["hours_at_point"][0] / mm["total_hours"] * 100 * 15  # takeoff punches far above its hours
    assert mm["available_blade_life_at_max_takeoff_hours"] > mm["equivalent_hours_at_max_takeoff"]
    assert mm["available_blade_life_at_max_takeoff_hours"] / mm["equivalent_hours_at_max_takeoff"] < 1.1  # a thin margin
    f = mech["stage1_blade"]["rupture_life"]["fig74_ambient_mix"]
    for cond in ("takeoff", "max_climb", "max_cruise"):
        assert abs(sum(f[cond]["bands_pct"]) - 100) < 0.5, cond
    assert [f[c]["hours"] for c in ("takeoff", "max_climb", "max_cruise")] == mm["hours_at_point"][:3]


def test_blade_vibratory_allowable_converts_and_lives_match_flowpath_table(mech):
    tv = mech["stage1_blade"]["tilt_and_vibration"]
    assert mpa_ksi_ok(tv["allowable_vibratory_stress_MPa"], tv["allowable_vibratory_stress_ksi"], 1.0)
    lo = mech["stage1_blade"]["life_objective"]
    assert lo["mission_mix_hours"] == mech["design_lives"]["flowpath_components_and_blade_retainers"][2]
    assert lo["lcf_cycles"] == mech["design_lives"]["flowpath_components_and_blade_retainers"][3]


# ── stage-1 blade: transient, Campbell, dovetail ────────────────────────

def test_blade_lcf_ranges_convert_and_miner_is_recorded(mech):
    b = mech["stage1_blade"]["lcf"]
    le = b["leading_edge_stress_history"]
    assert mpa_ksi_ok(le["total_range_MPa"], le["total_range_ksi"], 1.0)
    assert abs((le["decel_to_idle_peak_MPa"] - le["transient_to_takeoff_MPa"]) - le["total_range_MPa"]) < 25
    assert le["lcf_cycles_at_limiting_location"] > mech["stage1_blade"]["life_objective"]["lcf_cycles"]
    tr = b["thrust_reverse"]
    assert mpa_ksi_ok(tr["range_MPa"], tr["range_ksi"], 1.0)
    combined = 1 / (1 / le["lcf_cycles_at_limiting_location"] + 1 / 1e6)
    assert abs(combined - 25341) < 2
    assert 30 < tr["lcf_combined_printed"] - combined < 50  # the recorded print


def test_campbell_forcing_orders_are_the_engine_counts(mech, lpt):
    f = mech["stage1_blade"]["lcf"]["campbell"]["forcing_per_rev"]
    assert f["stage1_vanes"] == 46 and f["stage2_vanes"] == 48
    assert f["stage1_vanes"] == 2 * f["stage1_nozzle_segments"]
    assert f["stage2_vanes"] == 2 * f["stage2_nozzle_segments"]
    assert f["lpt_stage1_vanes"] == lpt["vane_counts"]["stage1"]
    assert f["burners"] == 30
    c = mech["stage1_blade"]["lcf"]["campbell"]
    sp = c["speeds_rpm"]
    assert sp["ground_idle"] < sp["flight_idle"] < sp["max_cruise"] < sp["max_climb"] < sp["max_takeoff"]
    for name, md in c["modes_kHz"].items():
        assert md["at_14000"] < md["at_0"], name
    f1t = c["modes_kHz"]["first_torsion"]
    cross = next(n for n in range(2000, 14000, 50) if 46 * n / 60 >= (f1t["at_0"] + (f1t["at_14000"] - f1t["at_0"]) * n / 14000) * 1000)
    assert sp["flight_idle"] < cross < sp["max_cruise"], cross


def test_stage2_first_torsion_meets_24_per_rev_near_flight_idle(mech):
    c2 = mech["stage2_blade"]["campbell"]
    sp = mech["stage1_blade"]["lcf"]["campbell"]["speeds_rpm"]
    f1t = c2["modes_kHz"]["first_torsion"]
    cross = next(n for n in range(2000, 14000, 50) if 24 * n / 60 >= (f1t["at_0"] + (f1t["at_14000"] - f1t["at_0"]) * n / 14000) * 1000)
    assert abs(cross - sp["flight_idle"]) < 700, cross
    assert c2["forcing_per_rev"]["stage2_nozzle_segments"] == 24
    # stage 2's blade is longer and softer: every mode below stage 1's
    c1 = mech["stage1_blade"]["lcf"]["campbell"]["modes_kHz"]
    for mode in c2["modes_kHz"]:
        assert c2["modes_kHz"][mode]["at_0"] < c1[mode]["at_0"], mode


def test_platform_damper_numbers_convert(mech):
    d = mech["stage1_blade"]["lcf"]["platform_damper"]
    assert abs(d["equivalent_g_load_N"] - d["equivalent_g_load_lbf"] * 4.44822) < 0.15
    assert abs(d["damping_load_N"] - d["damping_load_lbf"] * 4.44822) < 0.15
    assert mpa_ksi_ok(d["first_flex_vibratory_stress_with_damper_MPa"], d["first_flex_vibratory_stress_with_damper_ksi"], 1.0)
    assert d["first_flex_vibratory_stress_with_damper_MPa"] < mech["stage1_blade"]["tilt_and_vibration"]["allowable_vibratory_stress_MPa"] / 5
    assert mech["stage2_blade"]["damper"]["count"] == mech["stage2_blade"]["blades"] == 70


def test_rupture_vs_span_has_its_minimum_at_pitch_above_the_line(mech):
    r = mech["stage1_blade"]["lcf"]["rupture_vs_span"]
    i = r["hours"].index(min(r["hours"]))
    assert r["span_pct"][i] == 50 and r["hours"][i] > r["required_hours"]


def dovetail_checks(d, n_tangs):
    import math
    assert abs(d["load_per_blade_kN"] - d["load_per_blade_lbf"] * 0.00444822) < 0.01
    assert abs(d["axial_chord_cm"] - d["axial_chord_in"] * 2.54) < 0.006
    assert len(d["tangs"]) == n_tangs
    for tg in d["tangs"]:
        assert mpa_ksi_ok(tg["combined_stress_with_kt_MPa"], tg["ksi"], 1.0)
        assert abs(tg["neck_width_cm"] - tg["neck_width_in"] * 2.54) < 0.002
    widths = [tg["neck_width_cm"] for tg in d["tangs"]]
    assert widths == sorted(widths, reverse=True)  # necks narrow downward
    omega = d["condition"]["rpm"] * 2 * math.pi / 60
    return d["load_per_blade_kN"] * 1000 / omega ** 2


def test_both_dovetails_convert_and_imply_real_blade_masses(mech):
    m1 = dovetail_checks(mech["stage1_blade"]["dovetail"], 2) / 0.32   # F/(omega^2 r_cg), r_cg ~ 0.32 m
    m2 = dovetail_checks(mech["stage2_blade"]["dovetail"], 3) / 0.36
    assert 0.06 < m1 < 0.25 and 0.10 < m2 < 0.35, (m1, m2)
    assert m2 > m1
    d1, d2 = mech["stage1_blade"]["dovetail"], mech["stage2_blade"]["dovetail"]
    assert d1["tangs"][0]["combined_stress_with_kt_MPa"] == max(t["combined_stress_with_kt_MPa"] for t in d1["tangs"])  # upper tang on stage 1
    assert d2["tangs"][-1]["combined_stress_with_kt_MPa"] == max(t["combined_stress_with_kt_MPa"] for t in d2["tangs"])  # lower tang on stage 2, as the text says
    assert d1["condition"]["rpm"] == d2["condition"]["rpm"] == 13948


def test_stage2_blade_mission_mix_and_rupture_map(mech):
    mm = mech["stage2_blade"]["rupture_life"]["mission_mix"]
    assert sum(mm["hours_at_point"]) == mm["total_hours"]
    assert abs(sum(mm["pct_life_used"]) - 100) < 0.2
    assert mm["hours_at_point"] == mech["stage1_blade"]["rupture_life"]["mission_mix"]["hours_at_point"]
    assert mm["available_blade_life_at_max_takeoff_hours"] - mm["equivalent_hours_at_max_takeoff"] == 1
    pm = mech["stage2_blade"]["rupture_life"]["pitch_section_map"]["points"]
    for p in pm:
        assert abs(f_to_c(p["F"]) - p["C"]) < 0.75, p
    limiting = min(pm, key=lambda p: p["hours"])
    assert limiting["hours"] == mm["available_blade_life_at_max_takeoff_hours"]
    assert max(p["C"] for p in pm) > limiting["C"] + 80  # the hottest point is not the limiting one
    assert 1.03 < 13948 / 13414 < 1.05


# ── dynamics, bolts, stator start ───────────────────────────────────────

def test_dynamic_safety_margins_recompute_from_the_definition(mech):
    d = mech["rotor_dynamics"]
    n_max = d["max_engine_speed_rps"]
    for crit, sm in zip(d["table_xxii"]["critical_speed_rps"], d["table_xxii"]["safety_margin"]):
        assert abs((crit - n_max) / n_max - sm) < 0.012, (crit, sm)
    assert min(d["table_xxii"]["safety_margin"]) > 1.5
    assert abs(n_max * 60 - 13948) / 13948 < 0.005
    a = d["aft_seal_disk"]
    assert a["backward_wave_zero_rps"] == d["table_xxii"]["critical_speed_rps"][3]
    assert a["N"] == d["table_xxii"]["critical_nodes_N"][3]
    assert a["idle_rps"] * 60 > 9000 and a["idle_rps"] < n_max


def test_bolt_flanges_convert_and_the_clamp_margins_hold(mech):
    b = mech["rotor_bolts"]
    for cm, inch in zip(b["flanges"]["diameter_cm"], b["flanges"]["diameter_in"]):
        assert abs(cm - inch * 2.54) < 0.003
    ind = b["inducer_disk_bolt"]
    assert abs(ind["initial_clamp_kN"] - ind["initial_clamp_lbf"] * 0.00444822) < 0.5
    assert ind["initial_clamp_kN"] > ind["after_9000h_kN"] > ind["minimum_cold_clamp_kN"]
    assert abs((ind["after_9000h_kN"] / ind["minimum_cold_clamp_kN"] - 1) * 100 - ind["margin_after_9000h_pct"]) < 3
    assert ind["bolts"]["count"] == b["flanges"]["count"][0] and ind["bolts"]["diameter_cm"] == b["flanges"]["diameter_cm"][0]
    it = b["interstage_disk_bolt"]
    assert abs(it["initial_clamp_kN"] - it["initial_clamp_lbf"] * 0.00444822) < 0.5
    assert abs(it["minimum_cold_clamp_kN"] - it["minimum_cold_clamp_lbf"] * 0.00444822) < 0.3
    assert it["initial_clamp_kN"] > it["after_9000h_kN"] > it["minimum_cold_clamp_kN"]
    assert it["bolts"]["count"] == b["flanges"]["count"][1] and it["bolts"]["diameter_cm"] == b["flanges"]["diameter_cm"][1]
    assert abs(f_to_c(ind["bolts"]["t_max_F"]) - ind["bolts"]["t_max_C"]) < 0.75
    assert b["life_objective_hours"] == mech["design_lives"]["flowpath_components_and_blade_retainers"][0]


def test_stator_materials_and_ogv_joint(mech):
    st = mech["stator"]
    assert st["casings"]["fps_material"].startswith("Direct Age Inco 718")
    assert abs(st["stage1_nozzle_support"]["ogv_joint"]["diameter_cm"] - st["stage1_nozzle_support"]["ogv_joint"]["diameter_in"] * 2.54) < 0.003
    assert st["stage1_nozzle_support"]["ogv_joint"]["bolts"] == 64
    assert "Rene 41" in st["casings"]["shroud_support"]


# ── casing, nozzle support, inducer seal, stage-1 nozzle ────────────────

def test_casing_map_converts_and_hot_parts_are_in_hoop_compression(mech):
    pts = mech["stator"]["casing_lcf_map"]["points"]
    for p in pts:
        assert mpa_ksi_ok(p["hoop_MPa"], p["hoop_ksi"], 1.0), p
        assert mpa_ksi_ok(p["radial_MPa"], p["radial_ksi"], 1.0), p
        if "bending_MPa" in p:
            assert mpa_ksi_ok(p["bending_MPa"], p["bending_ksi"], 1.0), p
        assert abs(f_to_c(p["F"]) - p["C"]) < 0.75, p
    for p in pts:
        if p["C"] > 500:
            assert p["hoop_MPa"] < 0, p
        else:
            assert p["hoop_MPa"] > 0, p
    assert max(p["C"] for p in pts) == 626 and min(p["C"] for p in pts) == 323


def test_nozzle_support_and_inducer_seal_figures_convert(mech):
    ns = mech["stator"]["stage1_nozzle_support_stresses"]
    for key in ("aft_flange", "weld_upper", "discourager_seal", "weld_lower", "forward_flange_to_ogv"):
        p = ns[key]
        assert mpa_ksi_ok(p["MPa"], p["ksi"], 1.0) and abs(f_to_c(p["F"]) - p["C"]) < 0.75, key
    for kpa, psi in zip(ns["delta_p_kPa"], ns["delta_p_psi"]):
        assert abs(kpa - psi * 6.89476) < 1.0
    assert ns["aft_flange"]["MPa"] == 1034  # the same 150 ksi the LPT and disk bores keep landing on
    ind = mech["stator"]["inducer_and_piston_balance_seal"]
    for p in ind["stresses"]["points"]:
        assert mpa_ksi_ok(p["MPa"], p["ksi"], 1.0) and abs(f_to_c(p["F"]) - p["C"]) < 0.75, p
    assert max(p["MPa"] for p in ind["stresses"]["points"]) == 841
    assert ind["bypass_tubes"]["count"] == ind["ogv_bolts"]["count"] == 64
    assert ind["ogv_bolts"]["count"] == mech["stator"]["stage1_nozzle_support"]["ogv_joint"]["bolts"]
    assert abs(ind["tangential_holes"]["diameter_cm"] - ind["tangential_holes"]["diameter_in"] * 2.54) < 0.002
    assert abs(ind["bypass_tubes"]["diameter_cm"] - ind["bypass_tubes"]["diameter_in"] * 2.54) < 0.002


def test_nozzle_counts_tie_to_the_campbell_orders(mech):
    n1, n2 = mech["stator"]["stage1_nozzle"], mech["stator"]["stage2_nozzle"]
    f = mech["stage1_blade"]["lcf"]["campbell"]["forcing_per_rev"]
    assert n1["vanes"] == n1["vanes_per_segment"] * n1["segments"] == f["stage1_vanes"]
    assert n1["segments"] == f["stage1_nozzle_segments"]
    assert n2["vanes"] == n2["vanes_per_segment"] * n2["segments"] == f["stage2_vanes"]
    assert n2["segments"] == f["stage2_nozzle_segments"]
    assert n1["bolts_to_inner_support"]["count"] == n1["segments"] * n1["bolts_to_inner_support"]["per_segment"]
    assert n1["vane_material"] == mech["materials"]["static_parts"]["stage1_nozzle"]["airfoils"]
    assert n2["vane_material"] in mech["materials"]["static_parts"]["stage2_nozzle"]["airfoils"]


def test_stage1_nozzle_flange_and_gas_temperature_convert(mech):
    n1 = mech["stator"]["stage1_nozzle"]
    assert mpa_ksi_ok(n1["flange"]["allowable_text_MPa"], n1["flange"]["allowable_text_ksi"], 1.0)
    assert abs(n1["aft_cavity_wall_ballooning"]["bulge_mm"] - n1["aft_cavity_wall_ballooning"]["bulge_in"] * 25.4) < 0.002
    a = n1["airfoil_lcf"]
    assert abs(f_to_c(a["max_peak_gas_temperature_F"]) - a["max_peak_gas_temperature_C"]) < 0.75
    assert abs(a["design_adder_F"] / 1.8 - a["design_adder_C"]) < 0.5
    assert a["max_peak_gas_temperature_C"] > 1600


# ── nozzles: Figs.99-105 ────────────────────────────────────────────────

def test_stage1_nozzle_flange_and_bulge_figures_convert(mech):
    fl = mech["stator"]["stage1_nozzle"]["flange"]
    assert mpa_ksi_ok(fl["allowable_text_MPa"], fl["allowable_text_ksi"], 1.0)
    assert mpa_ksi_ok(fl["allowable_figure_MPa"], fl["allowable_figure_ksi"], 1.0)
    assert mpa_ksi_ok(fl["flange_stress_with_gussets_MPa"], fl["flange_stress_with_gussets_ksi"], 1.0)
    assert abs(fl["moment_N_m"] - fl["moment_in_lb"] * 0.112985) < 0.02
    assert fl["flange_stress_with_gussets_MPa"] < fl["allowable_figure_MPa"] < fl["allowable_text_MPa"]
    b = mech["stator"]["stage1_nozzle"]["aft_cavity_wall_ballooning"]
    assert abs(b["delta_p_kPa"] - b["delta_p_psi"] * 6.89476) < 1.0
    assert abs(f_to_c(b["wall_temperature_at_max_bulge_F"]) - b["wall_temperature_at_max_bulge_C"]) < 0.75
    for k in ("height", "bottom"):
        assert abs(b["panel_cm"][k] - b["panel_in"][k] * 2.54) < 0.01, k
    assert abs(b["panel_cm"]["top"] - b["panel_in"]["top"] * 2.54) > 0.1  # the recorded print
    assert b["bulge_mm"] < b["bulge_at_3000h_mm"]


def test_stage1_vane_lcf_map_converts_and_records_the_short_lives(mech):
    pts = mech["stator"]["stage1_nozzle"]["airfoil_lcf"]["lcf_map"]["points"]
    for p in pts:
        assert mpa_ksi_ok(p["MPa"], p["ksi"], 1.0) and abs(f_to_c(p["F"]) - p["C"]) < 0.75, p
    firm = [p for p in pts if not p.get("ge")]
    worst = min(firm, key=lambda p: p["cycles"])
    assert worst["where"] == "trailing edge" and worst["cycles"] == 3500
    service = mech["design_lives"]["flowpath_components_and_blade_retainers"][1]
    assert worst["cycles"] < service  # the finding
    hottest = max(pts, key=lambda p: p["C"])
    assert hottest["where"] == "leading edge" and hottest["cycles"] == 5000
    assert "finding" in mech["stator"]["stage1_nozzle"]["airfoil_lcf"]["lcf_map"]


def test_stage2_nozzle_lcf_meets_its_goal_at_the_trailing_edge(mech):
    n2 = mech["stator"]["stage2_nozzle"]
    lcf = n2["lcf"]
    for c, f, _ in lcf["span_95"] + lcf["span_65"]:
        assert abs(f_to_c(f) - c) < 0.75, (c, f)
    lim = lcf["limiting"]
    assert lim["cycles"] > lcf["goal_cycles"] == mech["stage1_blade"]["life_objective"]["lcf_cycles"]
    assert lim["cycles"] == min(x[2] for x in lcf["span_65"])
    assert min(x[2] for x in lcf["span_95"]) > lim["cycles"]
    assert lim["C"] == max(x[0] for x in lcf["span_65"])
    fs = n2["flange_stresses"]
    assert mpa_ksi_ok(fs["outer_hook_MPa"], fs["outer_hook_ksi"], 1.0) and mpa_ksi_ok(fs["bolt_flange_MPa"], fs["bolt_flange_ksi"], 1.0)
    f = n2["features"]
    assert abs(f["fastener_per_segment"]["diameter_cm"] - f["fastener_per_segment"]["diameter_in"] * 2.54) < 0.003
    assert f["seals"]["forward"] == f["seals"]["inner_discourager"] == f["seals"]["interstage_flat"] == 6


# ── ceramic shrouds ─────────────────────────────────────────────────────

def test_ceramic_shroud_thickness_arithmetic_and_conversions(mech):
    th = mech["stator"]["ceramic_shrouds"]["thickness"]
    st = th["stackup"]
    assert abs(st["eccentricity_cm"] + st["tolerance_on_radius_cm"] - st["total_cm"]) < 0.001
    assert abs(st["eccentricity_in"] + st["tolerance_on_radius_in"] - st["total_in"]) < 0.0005
    for k in ("eccentricity", "tolerance_on_radius", "total"):
        assert abs(st[f"{k}_cm"] - st[f"{k}_in"] * 2.54) < 0.001, k
    assert abs(th["minimum_ceramic_cm"] - th["minimum_ceramic_in"] * 2.54) < 0.001
    assert abs(th["bond_coat_below_982C_down_to_cm"] + st["total_cm"] - th["minimum_ceramic_cm"]) < 0.001
    assert abs(th["peg_end_holds_1038C_from_cm"] - th["peg_end_holds_1038C_from_in"] * 2.54) < 0.001
    assert abs(th["bond_coat_below_982C_down_to_in"] * 2.54 - th["bond_coat_below_982C_down_to_cm"]) > 0.002  # the recorded 0.021
    assert abs(f_to_c(th["peg_end_F"]) - th["peg_end_C"]) < 0.75
    c = mech["stator"]["ceramic_shrouds"]["construction"]
    assert abs(f_to_c(c["bond_coat_limit_F"]) - c["bond_coat_limit_C"]) < 0.75


def test_fig107_curves_behave_as_the_text_describes(mech):
    f = mech["stator"]["ceramic_shrouds"]["thickness"]["fig107_read_off"]
    limit = mech["stator"]["ceramic_shrouds"]["construction"]["bond_coat_limit_C"]
    assert f["ceramic_surface_C"] == sorted(f["ceramic_surface_C"])
    assert f["bond_coat_C"] == sorted(f["bond_coat_C"], reverse=True)
    # bond coat crosses 982 C near 0.05 cm
    i = next(k for k, v in enumerate(f["bond_coat_C"]) if v <= limit)
    assert f["ceramic_thickness_cm"][i - 1] <= 0.05 <= f["ceramic_thickness_cm"][i]  # crosses 982 C at about 0.05 cm
    # the peg end is flat-ish: within 90 C across the range
    assert max(f["peg_end_C"]) - min(f["peg_end_C"]) < 100
    for surf, bond in zip(f["ceramic_surface_C"], f["bond_coat_C"]):
        assert surf > bond


def test_ceramic_shroud_stress_points_convert(mech):
    pts = mech["stator"]["ceramic_shrouds"]["stress_life"]["points"]
    for p in pts:
        assert mpa_ksi_ok(p["MPa"], p["ksi"], 1.0) and abs(f_to_c(p["F"]) - p["C"]) < 0.75, p
    labelled_max = next(p for p in pts if p.get("note") == "maximum stress")
    assert labelled_max["MPa"] < max(p["MPa"] for p in pts)  # the recorded oddity
    assert mech["stator"]["stage1_nozzle"]["segments"] == 23 and "23 nozzle segments" in mech["maintainability"]["module1"]["assembly"]


# ── weights and the end of the report ───────────────────────────────────

def test_fps_turbine_weight_adds_and_converts(mech, lpt):
    w = mech["fps_weight"]
    assert w["hpt_stator_kg"] + w["hpt_rotor_kg"] == w["total_turbine_kg"]
    assert w["hpt_stator_lbm"] + w["hpt_rotor_lbm"] == w["total_turbine_lbm"]
    for kg, lb in ((w["total_turbine_kg"], w["total_turbine_lbm"]), (w["hpt_stator_kg"], w["hpt_stator_lbm"]), (w["hpt_rotor_kg"], w["hpt_rotor_lbm"])):
        assert abs(kg - lb * 0.45359) < 0.8, (kg, lb)
    assert w["hpt_rotor_kg"] / w["total_turbine_kg"] > 0.65
    # the HPT is lighter than the LPT, and its rotor share far higher
    assert w["total_turbine_kg"] < lpt["weights"]["total_kg"]
    pub = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())
    mod = None
    for k, v in pub.items():
        if isinstance(v, dict):
            for kk, vv in v.items():
                if isinstance(vv, dict) and "hpt" in kk.lower() and "rotor" in vv and "stator" in vv:
                    mod = vv
    if mod is not None:
        assert abs(mod["rotor"] - w["hpt_rotor_kg"]) / w["hpt_rotor_kg"] < 0.05
        assert abs(mod["stator"] - w["hpt_stator_kg"]) / w["hpt_stator_kg"] < 0.05


def test_station_numbers_match_the_topology_file(mech):
    topo = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())
    st = mech["report_end"]["symbols_of_note"]["stations"]
    assert st[41] == "HPT rotor-1 inlet" and st[49] == "LPT rotor-1 inlet"
    assert "T41" in str(topo) or "t41" in str(topo).lower()
