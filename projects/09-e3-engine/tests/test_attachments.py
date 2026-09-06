"""Stage E unit E5: attachments and joints
(solvers/mechanical/STEP0.md unit E5)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from mechanical.attachments import (  # noqa: E402
    casing_bolting, dovetail_crush, hpt_dovetail_tangs, lpt_fig70_kt,
    lpt_retainers, weak_link_order,
)

T = hpt_dovetail_tangs()
CRUSH = {c.blade: c for c in dovetail_crush()}
KT = {r["section"]: r for r in lpt_fig70_kt()}
RET, ALLOW, LAWS = lpt_retainers()
FAN, BOOSTER, HPT = weak_link_order()
BOLTS = {b["flange"]: b for b in casing_bolting()[0]}


# --- the HPT two-tang dovetail --------------------------------------------

def test_the_printed_tang_stresses_track_the_printed_neck_widths():
    """finding 98 -- five printed numbers fix the load split"""
    assert abs(1 - T["ratio_of_ratios"]) < 0.02          # the stated +-2 %
    assert abs(1 - T["ratio_of_ratios"]) < 0.01          # and in fact 0.47 %


def test_the_upper_tang_carries_the_higher_load_as_the_text_says():
    """finding 98 -- 57/43, not the 54/46 of an equal-stress design"""
    assert T["names"][0] == "upper"
    assert T["split_w2"][0] > T["split_w2"][1]
    assert 0.56 < T["split_w2"][0] < 0.59
    assert T["printed_MPa"][0] > T["equal_stress_MPa"]


def test_a_hand_tension_calculation_reads_the_dovetail_six_times_low():
    """finding 97 -- why dovetails are done by FE"""
    assert 100 < min(T["nominal_MPa"]) < 150
    for f in T["combined_factor"]:
        assert 6.0 < f < 7.0
    assert abs(T["combined_factor"][0] - T["combined_factor"][1]) < 0.05


# --- crush ----------------------------------------------------------------

def test_the_two_crush_figures_are_not_quoted_over_the_same_thing():
    """finding 99 -- one uses two flanks, the other one"""
    assert abs(CRUSH["fan rotor"].implied_flanks - 2.0) < 0.2
    assert abs(CRUSH["booster rotor"].implied_flanks - 1.0) < 0.1


def test_each_crush_reading_is_internally_consistent():
    for c in CRUSH.values():
        n = round(c.implied_flanks)
        assert abs(c.implied_area_cm2 / (n * c.one_flank_cm2) - 1) < 0.10


# --- LPT Fig 70's own Kt ---------------------------------------------------

def test_the_blade_sections_reproduce_the_printed_kt():
    """finding 100 -- positions 1 and 2 are the nominal and concentrated
    reading of one place"""
    for name in ("blade_A", "blade_B"):
        assert KT[name]["agrees"]
        assert abs(KT[name]["err_pct"]) < 1.0


def test_the_disc_sections_do_not_and_that_is_recorded():
    """finding 100 -- flagged for a re-read, not reconciled"""
    for name in ("disk_C", "disk_D"):
        assert not KT[name]["agrees"]
        assert abs(KT[name]["err_pct"]) > 30


# --- retainers -------------------------------------------------------------

def test_every_retainer_has_margin_and_the_third_sits_exactly_on_it():
    """E5's closure, on the one set of attachments with a printed allowable"""
    assert ALLOW == pytest.approx(634.3)
    assert all(r["margin"] >= 1.0 for r in RET)
    assert RET[2]["margin"] == pytest.approx(1.0, abs=1e-9)
    assert RET[0]["margin"] > RET[1]["margin"] > RET[2]["margin"]


def test_the_retainer_is_a_bending_part_and_t2_is_its_section():
    """finding 101 -- four candidate laws, one wins by more than 2x"""
    ranked = sorted(LAWS.items(), key=lambda kv: kv[1]["worst_pct"])
    assert ranked[0][0] == "t2_cm F/t^2"
    assert ranked[0][1]["worst_pct"] < 5.0
    assert ranked[1][1]["worst_pct"] > 2 * ranked[0][1]["worst_pct"]


def test_the_load_rises_far_more_than_the_stress_does():
    """finding 101 -- 75 % on force, 2 % on stress"""
    assert RET[2]["force_N"] / RET[0]["force_N"] > 1.7
    assert RET[2]["sigma_MPa"] / RET[0]["sigma_MPa"] < 1.03


# --- weak-link order -------------------------------------------------------

def test_the_disc_post_has_more_margin_than_the_blade_dovetail():
    """finding 103 -- the order is about margin, not about stress"""
    by = {r["part"]: r for r in FAN}
    assert by["fan disc post corner"]["margin"] > by["fan blade dovetail corner"]["margin"]
    assert all(r["margin"] > 1.0 for r in FAN)


def test_the_booster_attachment_is_below_its_airfoil():
    assert BOOSTER["attachment_below_airfoil"]
    assert BOOSTER["dovetail_corner"] < BOOSTER["airfoil_peak"]


def test_both_hpt_attachments_sit_exactly_on_their_own_life_requirement():
    """finding 103"""
    assert HPT["disc_lcf"] == HPT["disc_required"] == 36000
    assert HPT["blade_required"] == 18000
    assert HPT["blade_lcf"].lstrip(">").replace(",", "") == "18000"
    assert HPT["disc_slot"] > HPT["blade_tang_max"]      # as printed


# --- casing flanges --------------------------------------------------------

def test_the_rear_flanges_land_on_the_material_limit_at_the_2x_criterion():
    """finding 102 -- pi r^2 is an upper bound and it lands ON ~1000 MPa"""
    assert BOLTS["aft"]["bolt_stress_MPa"] > 900
    assert BOLTS["manifold"]["bolt_stress_MPa"] > 1000
    assert BOLTS["manifold"]["bolt_stress_MPa"] > BOLTS["aft"]["bolt_stress_MPa"]


def test_the_bolt_count_tracks_the_pressure_the_flange_sees():
    """finding 102 -- 60 bolts where it is 1.6 bar, 28 where it is 33"""
    assert BOLTS["front"]["bolts"] > BOLTS["manifold"]["bolts"]
    assert BOLTS["front"]["pressure_MPa"] < BOLTS["manifold"]["pressure_MPa"]
    assert BOLTS["front"]["bolt_stress_MPa"] < 100


def test_the_tensile_stress_area_is_the_standard_unf_value():
    _, a_t, rating = casing_bolting()
    assert a_t * 1e6 == pytest.approx(56.7, abs=0.2)     # 0.0878 in^2
    assert rating == "takeoff"


def test_the_gated_hpc_dovetails_are_absent_rather_than_guessed():
    """HPC sec 3.2.3 was never transcribed"""
    import yaml
    data = pathlib.Path(__file__).resolve().parents[1] / "data"
    hpc = yaml.safe_load((data / "hpc-mechanical.yaml").read_text())
    assert not [k for k in hpc if "dovetail" in k or "blade" in k]
