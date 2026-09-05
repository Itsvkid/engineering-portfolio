"""HPT active clearance control (CR-167955 section 4), checked against
itself and against the LPT's clearance data. Plain interpreter."""

from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def acc():
    return yaml.safe_load((DATA / "hpt-clearance.yaml").read_text())


@pytest.fixture(scope="module")
def lpt():
    return yaml.safe_load((DATA / "lpt-design.yaml").read_text())


def cm_in(cm_list, in_list, tol=0.0008):
    for cm, inch in zip(cm_list, in_list):
        if cm is None or inch is None:
            assert cm is None and inch is None
            continue
        assert abs(cm - inch * 2.54) < tol, (cm, inch)


# ── Table X payoff ──────────────────────────────────────────────────────

def test_payoff_columns_convert_and_multiply(acc):
    p = acc["payoff"]
    for per_mm, per_mil in zip(p["d_eta_per_mm"], p["d_eta_per_mil"]):
        assert abs(per_mm * 0.0254 - per_mil) < 0.0006
    cm_in(p["clearance_no_acc_cm"], p["clearance_no_acc_in"])
    cm_in(p["clearance_reduction_cm"], p["clearance_reduction_in"])
    for per_mm, red_cm, d_eta in zip(p["d_eta_per_mm"], p["clearance_reduction_cm"], p["d_eta_pct"]):
        assert abs(per_mm * red_cm * 10 - d_eta) < 0.012, (per_mm, red_cm, d_eta)
    assert abs(sum(p["d_eta_pct"]) - p["d_eta_total_pct"]) < 0.001
    assert abs(p["d_sfc_from_eta_pct"] + p["d_sfc_fan_air_pct"] - p["d_sfc_net_pct"]) < 0.001
    # the clearance after reduction is the 0.041 cm the table is based on
    for no_acc, red in zip(p["clearance_no_acc_cm"], p["clearance_reduction_cm"]):
        assert abs(no_acc - red - 0.041) < 0.03  # the seal keeps a larger gap


def test_hpt_acc_is_worth_more_than_the_lpts(acc, lpt):
    hpt = acc["payoff"]["d_sfc_net_pct"]
    lpt_sfc = lpt["active_clearance_control"]["payoff_at_max_cruise_10_67km"]["d_sfc_total_pct"]
    assert hpt < lpt_sfc < 0
    assert 3 < hpt / lpt_sfc < 4.5


def test_stage1_efficiency_sensitivity_exceeds_stage2(acc):
    p = acc["payoff"]
    assert p["d_eta_per_mm"][0] > p["d_eta_per_mm"][1] > p["d_eta_per_mm"][2]


# ── design clearance and the recorded misprint ──────────────────────────

def test_design_clearance_is_0_064_not_0_64(acc):
    d = acc["design_clearances"]
    assert abs(d["takeoff_tip_clearance_both_stages_cm"] - d["takeoff_tip_clearance_both_stages_in"] * 2.54) < 0.001
    assert "0.64 cm" in d["as_printed"]
    # and it is the 500-s cold-start pinch of Table XI on both stages
    s = acc["short_start_pinch"]
    assert s["stage1_blade"]["cold_cm"][-1] == s["stage2_blade"]["cold_cm"][-1] == d["takeoff_tip_clearance_both_stages_cm"]
    assert s["interstage_seal"]["cold_cm"][-1] == 0.0  # the seal just touches, by design


# ── Fig.47 ──────────────────────────────────────────────────────────────

def test_acc_flow_closes_clearance_monotonically_and_the_margins_match_the_text(acc):
    f = acc["acc_capability_vs_thrust"]
    for key in ("stage1_clearance_cm", "stage2_clearance_cm"):
        assert f[key] == sorted(f[key], reverse=True)
    m = f["margin_at_full_acc_cm"]
    assert abs(f["desired_cm"] - f["stage1_clearance_cm"][-1] - m["stage1"]) < 0.004
    assert abs(f["desired_cm"] - f["stage2_clearance_cm"][-1] - m["stage2"]) < 0.004
    for st in ("stage1", "stage2"):
        assert abs(m[st] - f["margin_at_full_acc_in"][st] * 2.54) < 0.001
    assert f["stage2_clearance_cm"][0] > f["stage1_clearance_cm"][0]  # the larger stage runs more open


# ── Tables XI and XII ───────────────────────────────────────────────────

def test_short_start_table_converts_and_opens_with_idle_time(acc):
    s = acc["short_start_pinch"]
    for row in ("stage1_blade", "interstage_seal", "stage2_blade"):
        cm_in(s[row]["cold_cm"], s[row]["cold_in"])
        cm_in(s[row]["warm_cm"], s[row]["warm_in"])
        assert s[row]["cold_cm"] == sorted(s[row]["cold_cm"])
        w = [v for v in s[row]["warm_cm"] if v is not None]
        assert w == sorted(w)
        # warm start pinches the blade tips tighter than cold at the same idle
        # time; the interstage seal rubs LESS on a warm start, as printed
        for c, wv in zip(s[row]["cold_cm"], s[row]["warm_cm"]):
            if wv is not None:
                assert (wv > c) if row == "interstage_seal" else (wv < c), (row, c, wv)


def test_heated_start_table_converts_and_the_text_claims_hold_where_stated(acc):
    h, s = acc["heated_start_pinch"], acc["short_start_pinch"]
    for row in ("stage1_blade", "interstage_seal", "stage2_blade"):
        cm_in(h[row]["cold_cm"], h[row]["cold_in"])
        cm_in(h[row]["warm_cm"], h[row]["warm_in"])
        # heating never closes the pinch at the 200-s point
        assert h[row]["cold_cm"][0] > s[row]["cold_cm"][0]
        assert h[row]["warm_cm"][0] > s[row]["warm_cm"][0]
    tc = h["text_claims"]
    # +0.023 on both tips for the WARM start, and on stage 1 cold
    assert abs(h["stage1_blade"]["warm_cm"][0] - s["stage1_blade"]["warm_cm"][0] - tc["gain_at_200s_blade_tips_cm"]) < 0.001
    assert abs(h["stage2_blade"]["warm_cm"][0] - s["stage2_blade"]["warm_cm"][0] - tc["gain_at_200s_blade_tips_cm"]) < 0.001
    assert abs(h["stage1_blade"]["cold_cm"][0] - s["stage1_blade"]["cold_cm"][0] - tc["gain_at_200s_blade_tips_cm"]) < 0.001
    assert abs(h["stage2_blade"]["cold_cm"][0] - s["stage2_blade"]["cold_cm"][0] - 0.031) < 0.001  # the recorded exception
    assert abs(h["interstage_seal"]["warm_cm"][0] - s["interstage_seal"]["warm_cm"][0] - tc["gain_at_200s_seal_cm"]) < 0.001
    # minimum pinch with heating is the warm-start minimum on each stage
    assert min(v for v in h["stage1_blade"]["warm_cm"] if v is not None) == tc["minimum_pinch_with_heating_cm"]["stage1"]
    assert min(v for v in h["stage2_blade"]["warm_cm"] if v is not None) == tc["minimum_pinch_with_heating_cm"]["stage2"]
    assert max(tc["minimum_pinch_with_heating_cm"].values()) < acc["design_clearances"]["takeoff_tip_clearance_both_stages_cm"]


def test_the_300_minus_row_is_the_best_case_because_heating_ran_into_the_takeoff(acc):
    h = acc["heated_start_pinch"]
    i = h["warm_up_time_s"].index("300-")
    for row in ("stage1_blade", "stage2_blade"):
        assert h[row]["cold_cm"][i] == max(h[row]["cold_cm"])
        assert h[row]["warm_cm"][i] == max(v for v in h[row]["warm_cm"] if v is not None)


# ── transients and hardware ─────────────────────────────────────────────

def test_transient_read_offs_are_ordered_the_way_the_text_says(acc):
    t = acc["transients"]
    for st in ("stage1_tip", "stage2_tip"):
        assert t[st]["cruise_running_clearance_with_acc"] < t[st]["cruise_clearance_no_acc"]
        assert t[st]["reburst_pinch_with_acc"] < t[st]["cruise_running_clearance_with_acc"] + 0.05
        assert t[st]["takeoff_pinch"] < t[st]["casing_peak_no_acc"]
    assert t["interstage_seal"]["takeoff_rub"] < 0  # by design
    assert t["stage1_tip"]["casing_peak_no_acc"] > t["stage1_tip"]["rotor_at_max_climb"]


def test_hardware_counts(acc):
    m = acc["mechanical"]
    assert m["manifold_segments_per_stage"] * m["manifold_arc_deg"] == 360
    assert m["feed_pipes_from_fan_duct"] == m["manifold_segments_per_stage"]
    assert m["shroud_segments_per_stage"] == 24
    assert acc["system"]["maximum_cooling_flow_pct_core_flow"] > acc["payoff"]["fan_air_pct_w25"]


# ── Tables XIII and XIV ─────────────────────────────────────────────────

def test_out_of_round_table_converts_and_sums_in_both_units(acc):
    oor = acc["out_of_round_stage1"]
    for cond in ("takeoff", "second_segment_climb", "low_mach_cruise"):
        c = oor[cond]
        for i in range(4):
            for key in ("beam_bending_rss", "vibration_unbalance", "ovalization"):
                assert abs(c[f"{key}_um"][i] - c[f"{key}_mils"][i] * 25.4) < 1.3, (cond, key, i)
            um = c["beam_bending_rss_um"][i] + c["vibration_unbalance_um"][i] + c["ovalization_um"][i]
            mils = c["beam_bending_rss_mils"][i] + c["vibration_unbalance_mils"][i] + c["ovalization_mils"][i]
            assert abs(um - c["sum_um"][i]) < 1.1, (cond, i, um)
            assert abs(mils - c["sum_mils"][i]) < 0.02, (cond, i, mils)
    worst = min(oor["second_segment_climb"]["sum_mils"])
    assert oor["clock"][oor["second_segment_climb"]["sum_mils"].index(worst)] == 6
    assert worst < min(oor["takeoff"]["sum_mils"]) and worst < min(oor["low_mach_cruise"]["sum_mils"])


def test_hpt_and_lpt_out_of_round_are_the_same_method(acc, lpt):
    h = acc["out_of_round_stage1"]
    l = lpt["clearance_predictions"]["out_of_round_stage1"]
    assert h["clock"] == l["clock"]
    for cond_h, cond_l in (("takeoff", "takeoff_rotation"), ("second_segment_climb", "second_segment_climb"), ("low_mach_cruise", "low_mach_cruise")):
        assert h[cond_h]["vibration_unbalance_mils"] == l[cond_l]["vibration_mils"]
    # the worst closures agree within 2 percent: -19.47 vs -19.78 mils at 6 o'clock in climb
    hw, lw = min(h["second_segment_climb"]["sum_mils"]), min(l["second_segment_climb"]["sum_mils"])
    assert abs(hw - lw) / abs(lw) < 0.02


def test_tip_shroud_table_converts_and_the_cruise_columns_recompute(acc):
    t = acc["blade_tip_shroud_clearance"]
    for key in ("clearance", "min_clearance", "out_of_round_12", "out_of_round_6", "beam_bending_12", "beam_bending_6", "total_closure_12", "total_closure_6", "max_interference_12", "max_interference_6"):
        for mm, inch in zip(t[f"{key}_mm"], t[f"{key}_in"]):
            if mm is None:
                continue
            assert abs(mm - inch * 25.4) < 0.013, (key, mm, inch)
    for c, mn in zip(t["clearance_mm"], t["min_clearance_mm"]):
        assert abs(c - t["tolerance_stack_mm"] - mn) < 0.003
    v = -t["vibration_mm"]
    for i in (2, 3):  # the two cruise columns
        assert abs(v + t["out_of_round_12_mm"][i] + t["beam_bending_12_mm"][i] - t["total_closure_12_mm"][i]) < 0.002, i
        assert abs(v + t["out_of_round_6_mm"][i] + t["beam_bending_6_mm"][i] - t["total_closure_6_mm"][i]) < 0.002, i
    # the recorded takeoff disagreement
    assert abs(v + t["out_of_round_12_mm"][1] + t["beam_bending_12_mm"][1] - (-0.068)) < 0.002
    assert t["total_closure_12_mm"][1] == -0.114
    for i in (1, 2, 3):
        for clk in ("12", "6"):
            interference = max(0.0, -(t["min_clearance_mm"][i] + t[f"total_closure_{clk}_mm"][i]))
            assert abs(interference - t[f"max_interference_{clk}_mm"][i]) < 0.002, (i, clk, interference)
    assert abs(t["max_interference_6_mm"][2] - t["shroud_offset_mm"] - t["max_rub_mm"]) < 0.002


def test_table_xiv_entries_are_table_xiii_values(acc):
    t, x = acc["blade_tip_shroud_clearance"], acc["out_of_round_stage1"]
    i12, i6 = x["clock"].index(12), x["clock"].index(6)
    assert abs(t["beam_bending_12_mm"][1] * 1000 - x["takeoff"]["beam_bending_rss_um"][i12]) < 0.6
    assert abs(t["beam_bending_6_mm"][1] * 1000 - x["takeoff"]["beam_bending_rss_um"][i6]) < 0.6
    assert abs(t["beam_bending_12_mm"][2] * 1000 - x["second_segment_climb"]["beam_bending_rss_um"][i12]) < 1.1
    assert abs(t["beam_bending_6_mm"][2] * 1000 - x["second_segment_climb"]["beam_bending_rss_um"][i6]) < 0.6
    assert abs(t["beam_bending_12_mm"][3] * 1000 - x["low_mach_cruise"]["beam_bending_rss_um"][i12]) < 0.6
    assert abs(t["beam_bending_6_mm"][3] * 1000 - x["low_mach_cruise"]["beam_bending_rss_um"][i6]) < 0.6
    assert abs(t["out_of_round_12_mm"][1] * 1000 - x["takeoff"]["ovalization_um"][i12]) < 0.6
    o = t["outcome"]
    assert abs(o["probable_net_closure_cm"]["12:00"] * 10 - t["total_closure_12_mm"][2]) < 0.001
    assert abs(o["probable_net_closure_cm"]["6:00"] * 10 - t["total_closure_6_mm"][2]) < 0.006  # -0.050 cm printed for -0.495 mm
    assert abs(o["shroud_centreline_offset_cm"] * 10 - t["shroud_offset_mm"]) < 0.003
    assert o["minimum_average_clearance_cm"] == acc["acc_capability_vs_thrust"]["desired_cm"]
