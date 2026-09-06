"""Stage E unit E4: shafts, criticals, bolted joints and blade-out
(solvers/mechanical/STEP0.md unit E4)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from mechanical.rotordynamics import (  # noqa: E402
    blade_masses, blade_out, bolted_joint_margin, critical_speed_margins,
    spool_torques, travelling_wave,
)

ROWS, N_MAX = critical_speed_margins()
BY = {r["component"]: r for r in ROWS}
TQ = {s.rating: s for s in spool_torques()}
TW = travelling_wave()
MASS = {b["name"]: b for b in blade_masses()}


# --- criticals: E4's first closure half -----------------------------------

def test_no_rotor_critical_sits_inside_the_operating_band():
    """E4's stated closure half"""
    assert N_MAX == 233
    assert len(ROWS) == 4
    assert not any(r["inside_band"] for r in ROWS)
    assert min(r["margin"] for r in ROWS) > 1.6


def test_table_xxii_checks_itself_to_the_printed_rounding():
    """finding 91 -- three printed quantities and one printed definition"""
    for r in ROWS:
        assert abs(r["diff"]) <= 0.01


def test_the_two_610_rps_components_give_the_same_margin_printed_two_ways():
    """finding 91 -- the transcription's as_printed note, quantified"""
    a, b = BY["inner_tube"], BY["aft_seal_disk"]
    assert a["crit_rps"] == b["crit_rps"] == 610
    assert abs(a["margin"] - b["margin"]) < 1e-12
    assert a["printed"] != b["printed"]          # 1.62 and 1.61 for one number


# --- the travelling wave --------------------------------------------------

def test_the_disc_must_stiffen_for_its_published_critical_to_exist():
    """finding 92 -- S falls out of three printed quantities"""
    assert TW["rigid_critical_rps"] == pytest.approx(500.0)
    assert TW["crit_rps"] == 610
    assert 0 < TW["southwell"] < TW["nodes"] ** 2
    assert TW["southwell"] == pytest.approx(8.20, abs=0.02)


def test_the_critical_is_self_consistent_by_construction():
    assert TW["f_disc_at_crit"] == pytest.approx(TW["check_n_omega"], rel=1e-9)


def test_the_440_rps_point_belongs_to_a_different_curve():
    """finding 93 -- flagged for a re-read, not reconciled by tuning"""
    assert TW["fwd_at_440_printed"] < TW["fwd_at_440_model"]
    assert TW["implied_nodes_at_440"] < 2.0


# --- shafts ---------------------------------------------------------------

def test_the_lp_shaft_carries_more_torque_than_the_hp_on_less_power():
    """finding 89 -- torque is power over speed, and the LP spool is slow"""
    for s in TQ.values():
        assert s.lp_power_MW < s.hp_power_MW
        assert s.lp_torque_kNm > 2 * s.hp_torque_kNm


def test_the_spool_speeds_close_across_three_documents():
    """finding 90 -- LPT report's N/sqrt(T), the cycle's T45, and the FAN
    report's stated maximum; none derived from the others"""
    assert abs(TQ["takeoff"].lp_rpm / 3653 - 1) < 0.02
    assert abs(TQ["max_climb"].hp_rpm / 12645 - 1) < 0.03


def test_takeoff_is_the_worst_torque_case_on_both_spools():
    for name in ("max_climb", "max_cruise"):
        assert TQ["takeoff"].hp_torque_kNm > TQ[name].hp_torque_kNm
        assert TQ["takeoff"].lp_torque_kNm > TQ[name].lp_torque_kNm


def test_the_bolted_joint_needs_a_radius_far_inside_the_disc():
    """finding 96 -- the radius is inverted because it is not printed"""
    j = bolted_joint_margin()
    assert j["rating"] == "takeoff"
    assert j["r_required_relaxed_cm"] > j["r_required_new_cm"]
    assert j["r_required_relaxed_cm"] < 31.0          # the disc rim radius
    assert 14 < j["relaxation_pct"] < 18


def test_the_required_radius_scales_inversely_with_the_friction_assumed():
    a = bolted_joint_margin(mu=0.15)["r_required_new_cm"]
    b = bolted_joint_margin(mu=0.30)["r_required_new_cm"]
    assert a / b == pytest.approx(2.0, rel=1e-9)


# --- masses and blade-out --------------------------------------------------

def test_the_airfoil_is_a_sensible_fraction_of_the_printed_blade_weight():
    """finding 95 -- the printed weight is the whole blade"""
    for b in MASS.values():
        assert 0.40 < b["fraction"] < 0.90
    assert MASS["fan rotor"]["fraction"] > MASS["booster rotor"]["fraction"]


def test_the_fan_blade_weight_matches_table_vis_own_per_blade_note():
    assert MASS["fan rotor"]["printed_kg"] == pytest.approx(7.272, abs=0.005)
    assert MASS["booster rotor"]["printed_kg"] == pytest.approx(0.284, abs=0.001)


def test_a_released_fan_blade_throws_seventy_odd_tonnes_into_the_mounts():
    """finding 94"""
    rows = {(b["blade"], b["basis"]): b for b in blade_out()}
    whole = rows[("fan rotor", "whole blade (Table VI)")]
    airfoil = rows[("fan rotor", "airfoil only")]
    assert 70 < whole["tonnes"] < 82
    assert 45 < airfoil["tonnes"] < 55
    assert whole["rpm"] == 3653


def test_the_hot_end_is_not_where_the_mount_loads_come_from():
    """finding 94 -- an HPT blade is 110 g against a fan blade's 7.3 kg"""
    hpt = next(b for b in blade_out() if b["blade"] == "HPT stage 1")
    assert 0.09 < hpt["mass_kg"] < 0.13
    assert hpt["load_kN"] == pytest.approx(77.395, abs=1e-3)
    assert hpt["tonnes"] < 10


def test_the_thrust_bearing_half_is_absent_rather_than_guessed():
    """no bearing capacity is published and D's thrust balance is not done"""
    import mechanical.rotordynamics as rd
    assert not [n for n in dir(rd) if "capacity" in n.lower()]
