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
