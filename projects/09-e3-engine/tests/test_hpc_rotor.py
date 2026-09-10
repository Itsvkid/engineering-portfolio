"""Stage E unit E9: the HPC rotor structure
(solvers/mechanical/STEP0.md unit E9)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from mechanical.hpc_rotor import (  # noqa: E402
    candidate_positions, hp_torque_kNm, joint_demand_curve,
    published_construction, summary, torque_through_joint, versus_hpt_joint,
    what_is_not_published, work_split,
)

WS = work_split()
PC = published_construction()
V = versus_hpt_joint()


# --- the sentence, read carefully ---------------------------------------

def test_the_rotor_has_two_kinds_of_joint_not_one():
    assert PC["inertia_welds"]["count"] == "plural, unstated"
    assert PC["bolt_joints"]["count"] == 1
    assert "inertia-welded" in PC["line"] and "single bolt joint" in PC["line"]


def test_neither_joint_position_is_published():
    assert PC["inertia_welds"]["position_published"] is False
    assert PC["bolt_joints"]["position_published"] is False


def test_the_conflation_that_cost_finding_74_is_named():
    assert "finding 74" in PC["why_two_kinds"] or "E1" in PC["why_two_kinds"]
    assert "WELD" in PC["why_two_kinds"]


# --- the work split ------------------------------------------------------

def test_the_work_split_closes_on_figure_14s_own_total():
    assert WS["closes_to_C"] < 0.05, WS["closes_to_C"]
    assert WS["printed_total_C"] == 493.5
    assert len(WS["rows"]) == 10


def test_the_cumulative_fraction_runs_from_nothing_to_everything():
    f = [r["fraction_forward"] for r in WS["rows"]]
    assert f == sorted(f)
    assert 0 < f[0] < 0.15
    assert f[-1] == pytest.approx(1.0, abs=1e-9)


def test_stages_six_and_seven_take_the_smallest_steps():
    """the deliberately unloaded pair, seen from the work split"""
    steps = [r["dt_C"] for r in WS["rows"]]
    two_smallest = sorted(range(10), key=lambda i: steps[i])[:2]
    assert sorted(i + 1 for i in two_smallest) == [6, 7]


# --- the torque curve ----------------------------------------------------

def test_the_torque_through_a_joint_is_monotone_in_position():
    t = [r["torque_kNm"] for r in joint_demand_curve()]
    assert t == sorted(t)
    assert all(x > 0 for x in t)


def test_the_aftmost_joint_carries_the_whole_hp_torque():
    r = torque_through_joint(10)
    assert r["fraction"] == pytest.approx(1.0, abs=1e-9)
    assert r["torque_kNm"] == pytest.approx(hp_torque_kNm("takeoff"))


def test_no_joint_carries_more_than_the_shaft_delivers():
    for r in joint_demand_curve():
        assert 0 < r["fraction"] <= 1.0 + 1e-12


def test_every_forward_joint_is_below_the_hpt_joint():
    """the HPT joint carries the whole HP torque; each HPC joint part"""
    assert V["all_below_one"] is True
    for r in V["rows"][:-1]:
        assert r["fraction_of_hpt_joint"] < 1.0


def test_the_comparison_needs_no_unpublished_hpc_bolt_data():
    """it is a torque ratio, so no HPC bolt count, size or radius enters --
    which is just as well, because none of them is published"""
    import inspect
    src = inspect.getsource(versus_hpt_joint)
    assert "dimensionless" in src
    # the ratio really is torque over torque, and nothing else
    assert 'r["torque_kNm"] / hpt["torque_kNm"]' in src
    # and nothing bolt-shaped reaches the result
    for row in V["rows"]:
        assert set(row) == {"after_stage", "torque_kNm", "fraction_of_hpt_joint"}


def test_the_takeoff_rating_is_the_worst_case():
    a = hp_torque_kNm("takeoff")
    for other in ("max_climb", "max_cruise"):
        assert a > hp_torque_kNm(other)


# --- what the open material question costs -------------------------------

def test_the_two_candidate_stations_differ_by_a_large_factor():
    c = candidate_positions()
    rows = {r["after_stage"]: r for r in c["rows"]}
    assert set(rows) == {4, 7}
    ratio = rows[7]["torque_kNm"] / rows[4]["torque_kNm"]
    assert ratio == pytest.approx(1.67, abs=0.05)


def test_listing_them_is_declared_an_argument_for_neither():
    c = candidate_positions()
    assert c["is_an_argument_for_neither"] is True
    assert "finding 74" in c["note"]


def test_the_candidates_are_material_evidence_not_weld_positions():
    c = candidate_positions()
    for r in c["rows"]:
        assert "material" in r["why"] or "density" in r["why"]


# --- what is not claimed -------------------------------------------------

def test_nothing_unpublished_is_invented():
    n = what_is_not_published()
    for k in ("weld_positions", "weld_count", "bolt_count", "bolt_size",
              "bolt_circle_radius", "axial_load"):
        assert n[k] is False
    assert "function of" in n["consequence"]


def test_the_summary_gives_a_curve_and_not_a_single_number():
    s = summary()
    assert "aft of" in s
    assert "not published" in s
    assert s.count("kNm") > 3
