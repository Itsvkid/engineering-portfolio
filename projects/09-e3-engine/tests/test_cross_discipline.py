"""Stage I unit I1: cross-discipline consistency
(solvers/verification/STEP0.md unit I1).

These are the tests Stage I1 asked for by name: "as tests, not by
inspection". Each one is a place where two stages could have drifted apart
silently and nothing else in the suite would have noticed."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from verification.consistency import (  # noqa: E402
    closure_scoreboard, closure_summary, cooling_flows_across_stages,
    metal_temperatures_across_stages, spool_speeds_four_routes,
    t41_across_stages, t41_margin_arithmetic,
    t41_solved_is_the_rating_it_was_solved_to,
)

T41 = t41_across_stages()
CF = cooling_flows_across_stages()
MT = metal_temperatures_across_stages()
SP = spool_speeds_four_routes()
CLOSURES = closure_scoreboard()
SUMMARY = closure_summary()


# --- T41 in B, D and E -----------------------------------------------------

def test_t41_at_the_design_point_agrees_between_the_cycle_and_the_hpt_report():
    """finding 118 -- two documents, neither derived from the other"""
    g = T41["T41 max climb, the aero design point"]
    assert g["spread_pct"] < 0.5
    assert g["spread_pct"] < 0.05          # in fact 0.01 %


def test_the_hpt_reports_earlier_requirements_are_chronology_not_disagreement():
    """finding 119 -- comparing against the wrong block would have
    manufactured a finding out of a design history"""
    ch = T41["chronology"]
    assert ch["drop_max_climb_K"] == pytest.approx(40, abs=1)
    assert ch["drop_max_cruise_K"] == pytest.approx(30, abs=1)
    assert ch["drop_max_climb_K"] > 0      # the design got cooler, not hotter


def test_takeoff_means_three_things_and_the_two_that_agree_share_a_definition():
    """finding 120 -- a T41 quoted 'at takeoff' without its Mach number
    is a range, not a temperature"""
    g = T41["T41 takeoff"]
    assert len(g["rows"]) == 3
    assert g["spread_pct"] < 2.0
    by = {a.stage: a.value for a in g["rows"]}
    pair = abs(by["A HPT report"] / by["D cooling"] - 1) * 100
    assert pair < 0.5                       # the two sea-level definitions
    assert by["B cycle"] > by["A HPT report"]   # the static one is hottest


def test_the_cycle_still_solves_to_the_rating_it_was_given():
    """the hinge every downstream stage hangs on"""
    rows = t41_solved_is_the_rating_it_was_solved_to()
    assert len(rows) == 3
    for r in rows:
        assert abs(r["err_pct"]) < 1e-6


def test_ds_t41_margin_stack_recomputes_including_its_root_sum_square():
    """finding 123"""
    m = t41_margin_arithmetic()
    assert m["direct_sum"] == pytest.approx(m["direct_printed"], abs=0.05)
    assert m["rss"] == pytest.approx(m["rss_printed"], abs=0.5)
    assert m["new_engine"] == pytest.approx(m["new_printed"], abs=0.05)
    assert m["with_det"] == pytest.approx(m["with_det_printed"], abs=0.05)
    assert m["design_C"] == pytest.approx(m["design_printed_C"], abs=0.5)


# --- cooling flows in B, D and D3 -----------------------------------------

def test_the_cycles_bleeds_are_the_streams_stage_d3_measured():
    """finding 118 -- not close, the same numbers"""
    assert len(CF["streams"]) == 4
    for s in CF["streams"]:
        assert abs(s["err_pct"]) < 1e-9
    assert CF["cycle_total_pct"] == pytest.approx(CF["published_total_pct"], abs=1e-9)
    assert CF["published_total_pct"] == pytest.approx(16.14, abs=1e-9)


def test_d1s_detailed_design_sums_to_its_own_printed_total():
    assert CF["detailed_total_pct"] == pytest.approx(CF["detailed_printed"], abs=0.05)


def test_the_hpt_reports_third_number_is_a_different_denominator():
    """18.2 % of W2c against 18.87 % of W25 -- not a disagreement"""
    assert CF["hpt_table_iii_pct_w2c"] != CF["detailed_total_pct"]
    assert abs(CF["hpt_table_iii_pct_w2c"] - CF["detailed_total_pct"]) < 1.0


# --- metal temperatures in D, E and F -------------------------------------

def test_the_metal_temperatures_are_ordered_the_way_the_gas_path_is():
    assert MT["hpc_max_C"] < MT["hpt_shank_C"] < MT["hpt_blade_metal_C"]
    assert MT["hpt_disc_bore_C"] < MT["hpt_shank_C"]
    assert MT["hpc_max_C"] == 655
    assert len(MT["f_hpc_blades"]) == 10
    assert len(MT["d_cooled_rows"]) == 4


def test_the_hpc_metal_temperature_rises_monotonically_through_the_compressor():
    t = [r["metal_C"] for r in MT["f_hpc_blades"]]
    assert t == sorted(t)


def test_every_cooled_row_is_cooler_than_its_gas_and_hotter_than_its_coolant():
    for r in MT["d_cooled_rows"]:
        assert r["t_coolant_C"] < r["t_metal_C"] < r["t_gas_C"]


# --- spool speeds from four routes ----------------------------------------

def test_the_lp_speed_agrees_from_the_fan_report_and_the_lpt_report():
    """finding 121"""
    assert SP["lp_spread_pct"] < 2.0
    assert len(SP["lp"]) == 2


def test_the_hp_speed_agrees_from_hpc_table_x_and_the_hpt_report():
    """finding 121"""
    assert SP["hp_spread_pct"] < 2.0
    assert len(SP["hp"]) == 2


def test_the_spool_ratio_matches_the_assumption_stage_h_was_going_to_use():
    """finding 121 -- checked before H is ever built"""
    assert abs(SP["ratio"] / 3.6 - 1) < 0.03
    assert 3.5 < SP["ratio"] < 3.7


# --- every closure re-checked ---------------------------------------------

def test_every_numeric_closure_is_inside_its_band_or_a_recorded_miss():
    """finding 122 -- Stage I1's third bullet, made a test.

    Two misses now. B3's takeoff sfc has been a pinned xfail since Stage B.
    E3 joined it on 2026-09-08 when transcribing HPC Figs 33-42 lifted the
    gate on its closure and let it be *evaluated* for the first time -- at
    which point it failed, 1 of 24 inside a 5 % band (finding 143). A miss
    that can be measured is worth more than a gate that cannot, so this
    test wants both to be present and explained, not absent."""
    misses = SUMMARY["misses"]
    assert {m["stage"] for m in misses} == {"B3", "E3"}
    for m in misses:
        assert m["state"] == "half"
        assert m.get("gate"), f"{m['stage']} misses its band without an explanation"


def test_the_scoreboard_covers_every_stage_that_has_a_closure():
    stages = {r["stage"][0] for r in CLOSURES}
    assert stages >= set("BCDEFGH")
    assert SUMMARY["total"] >= 20


def test_no_closure_is_open_without_a_reason_attached():
    """finding 122 -- half and gated closures must name what blocks them"""
    for r in CLOSURES:
        if r["state"] in ("half", "gated"):
            assert r.get("gate"), r["what"]
        if r["band"] is None and r["state"] != "gated":
            assert r.get("note") or r.get("gate"), r["what"]


def test_no_gated_closure_carries_an_achieved_number():
    """a gated closure with a number in it would be a guess wearing a result"""
    for r in CLOSURES:
        if r["state"] == "gated":
            assert r["achieved"] is None
