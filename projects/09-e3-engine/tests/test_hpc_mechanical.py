"""HPC mechanical design and 10A rig findings (HPC report section 3),
checked against themselves, the stagewise design file and the through-
flow data."""

from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def mech():
    return yaml.safe_load((DATA / "hpc-mechanical.yaml").read_text())


@pytest.fixture(scope="module")
def sw():
    return yaml.safe_load((DATA / "hpc-stagewise.yaml").read_text())


@pytest.fixture(scope="module")
def vd():
    return yaml.safe_load((DATA / "hpc-vector-diagrams.yaml").read_text())


def test_stator_response_rises_rearward(mech):
    r = mech["stator_aeromechanics"]["max_steady_state_response_pct_limit"]
    vals = [v for v in r if v is not None]
    assert vals[-1] == max(vals) == 56 and all(v < 100 for v in vals)
    assert mech["stator_aeromechanics"]["row"][-1] == "OGV" and r[-1] is None


def test_clearance_elements_convert(mech):
    c = mech["clearance_elements"]
    v = c["system_vibration"]
    assert abs(v["hp_unbalance_g_cm"] - v["hp_unbalance_g_in"] * 2.54) < 0.5
    assert abs(v["lp_unbalance_g_cm"] - v["lp_unbalance_g_in"] * 2.54) < 0.5
    assert abs(c["rub_allowance_cm"] - c["rub_allowance_in"] * 2.54) < 0.0006
    assert abs(c["stall_allowance_cm"] - c["stall_allowance_in"] * 2.54) < 0.0006
    assert c["stall_allowance_cm"] > c["rub_allowance_cm"]


def test_casing_temperatures_analysis_tracks_test(mech):
    c = mech["casing_temperatures_10A"]
    for a, t in zip(c["stations_outer_analysis_K"], c["stations_outer_test_K"]):
        assert abs(a - t) / t < 0.03, (a, t)
    for a, t in zip(c["stations_inner_analysis_K"], c["stations_inner_test_K"]):
        assert abs(a - t) / t < 0.045, (a, t)
    assert c["stations_inner_analysis_K"] == sorted(c["stations_inner_analysis_K"])
    assert c["stations_inner_analysis_K"][-1] == c["t3_analysis_K"] and c["stations_inner_test_K"][-1] == c["t3_test_K"]
    t25_a, t25_t = c["t25_analysis_C"] + 273.15, c["t25_test_C"] + 273.15
    assert 2.6 < c["t3_analysis_K"] / t25_a < 3.05 and 2.6 < c["t3_test_K"] / t25_t < 3.05
    pr_a, pr_t = c["p3_analysis_N_cm2"] / c["p25_analysis_N_cm2"], c["p3_test_N_cm2"] / c["p25_test_N_cm2"]
    assert 22 < pr_a < 28 and 22 < pr_t < 28


def test_rig_bleeds_tie_to_the_design_bleed_sizing(mech, sw):
    b = mech["rig_bleeds_10A"]
    d = sw["design_point"]["bleeds"]
    assert abs(b["hpt_nozzle2_cooling_pct"] - d["stage7"]["hpt_stage2_nozzle_pct"]) < 0.1
    assert b["customer_bleed_stage5_pct"].endswith(str(int(d["stage5"]["customer_max_pct"])))
    assert b["hptr_cooling_pct"] > b["hpt_nozzle2_cooling_pct"] > b["cavity_behind_hptr2_pct"]


def test_clearances_read_offs_are_consistent_across_the_two_figures(mech):
    c = mech["clearances"]
    for goal, cruise in zip(c["rig_goal_fps_cruise_mm"], c["fps_cruise_mm"]):
        assert abs(goal - cruise) < 0.035, (goal, cruise)  # Fig 62's goal IS Fig 61's FPS cruise
    for i, (cr, obj) in enumerate(zip(c["fps_cruise_mm"], c["e3_efficiency_objective_mm"]), 1):
        if i in (4, 5, 6):
            assert cr > obj - 0.001  # stages 4-6 sit at or above the objective as read
        else:
            assert cr <= obj + 0.001, (i, cr, obj)
    assert c["fps_buildup_mm"][0] == max(c["fps_buildup_mm"])
    post, goal = c["rig_post_test_analysis_mm"], c["rig_goal_fps_cruise_mm"]
    assert post[5] < 0.4 * goal[5] and post[7] < 0.7 * goal[7]
    assert post[3] > goal[3] and post[4] > goal[4]
    assert abs(c["rig_condition"]["t25_K"] - ((c["rig_condition"]["t25_F"] - 32) / 1.8 + 273.15)) < 0.6
    assert abs(c["rig_touch_probe_mm"]["stage4"] - post[3]) < 0.15


def test_casing_bolting(mech):
    b = mech["casing_bolting"]
    for k in ("front_casing", "aft_casing", "manifold_casing"):
        assert abs(b[k]["diameter_cm"] - b[k]["diameter_in"] * 2.54) < 0.003
    assert b["front_casing"]["bolts"] + b["aft_casing"]["bolts"] + b["manifold_casing"]["bolts"] == 120


def test_vsv_bushing_temperatures_order_and_selections_follow_them(mech, sw):
    v = mech["vsv_bushings"]
    for k in ("fps_hdto_K", "fps_cruise_K", "growth_hdto_K", "growth_cruise_K"):
        assert v[k] == sorted(v[k]), k
    for i in range(7):
        assert v["growth_hdto_K"][i] > v["fps_hdto_K"][i] > v["fps_cruise_K"][i]
        assert v["growth_cruise_K"][i] > v["fps_cruise_K"][i]
    sel = v["selection"]
    assert sel["ZX"] == ["IGV", 1, 2, 3] and sel["Fabroid_XV"] == ["IGV", 1, 2, 3, 4] and sel["PBH_20"] == [4, 5, 6]
    zx_max = max(v["fps_hdto_K"][v["stage"].index(s)] for s in sel["ZX"])
    pbh_min = min(v["fps_hdto_K"][v["stage"].index(s)] for s in sel["PBH_20"])
    assert zx_max < pbh_min
    assert sw["design_point"]["variable_geometry"].endswith("stators 1-4")


def test_endurance_rows_carry_table_xviii_temperatures(mech):
    v = mech["vsv_bushings"]
    rows = v["endurance_tests"]["rows"]
    t = {s: (h, c, gh, gc) for s, h, c, gh, gc in zip(v["stage"], v["fps_hdto_K"], v["fps_cruise_K"], v["growth_hdto_K"], v["growth_cruise_K"])}
    assert rows[0]["temperature_K"] == list(t[1][:2]) and rows[0]["growth_K"] == list(t[1][2:])
    assert rows[1]["temperature_K"] == list(t[4][:2]) and rows[1]["growth_K"] == list(t[4][2:])
    assert rows[4]["temperature_K"] == list(t[5][:2])  # the recorded print
    assert rows[4]["growth_K"] == list(t[4][2:])
    failed = [r for r in rows if "failed_at_cycles" in r]
    assert len(failed) == 1 and failed[0]["material"].startswith("ZX (NR150)")
    assert failed[0]["wear_bushing_mm"] / rows[0]["wear_bushing_mm"] > 5
    tc = v["endurance_tests"]["test_cycles"]
    assert tc["hdto"] + tc["cruise"] == 2500000
    assert abs(failed[0]["failed_at_cycles"] - (200000 + 1946000)) < 1


def test_vane_campbell_orders_are_the_original_blade_counts(mech, vd):
    c = mech["vane_campbell_10A"]
    final = {r["stage"]: r["blade_count"] for r in vd["rows"] if r["row"] == "rotor"}
    chg = vd["design_change_original_to_final"]["blade_counts"]
    orig = {8: final[8], 9: chg["rotor_9"]["original"], 10: chg["rotor_10"]["original"]}
    assert c["forcing_per_rev"] == {"R8": orig[8], "R9": orig[9], "R10": orig[10]}
    assert final[9] == chg["rotor_9"]["final"] and final[10] == chg["rotor_10"]["final"]
    assert c["forcing_per_rev"]["R9"] == 88 and c["forcing_per_rev"]["R10"] == 98
    s9 = c["stage9_vane"]["first_flex_kHz"]
    f_at = lambda n: (s9["at_0"] + (s9["at_14000"] - s9["at_0"]) * n / 14000) * 1000
    cross98 = next(n for n in range(5000, 14000, 50) if 98 * n / 60 >= f_at(n))
    assert 10000 < cross98 < 12000, cross98
    s10 = c["stage10_vane"]["first_flex_kHz"]
    assert 98 * 14000 / 60 < s10["at_14000"] * 1000
