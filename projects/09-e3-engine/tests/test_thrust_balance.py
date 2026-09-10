"""Stage D unit D6: thrust balance on the HP rotor
(solvers/thermal/STEP0.md unit D6)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from thermal.thrust_balance import (  # noqa: E402
    disc_face_curve, disc_face_force, figs_95_96_contain, hpc_continuity_check,
    hpc_rotor_loads, hpt_rotor_loads, net_hp_gas_load, summary,
    what_is_not_published, why_gated,
)

HPC = hpc_rotor_loads()
HPT = hpt_rotor_loads()
N = net_hp_gas_load()
G = why_gated()


# --- what the named figures actually contain ----------------------------

def test_figs_95_96_give_structure_and_not_a_thrust():
    f = figs_95_96_contain()
    assert f["structure_given"] is True
    assert f["tangential_holes"] == 62 and f["bypass_tubes"] == 64
    assert f["stress_points"] == 11
    for k in ("thrust_given", "piston_area_given", "piston_radius_given",
              "cavity_pressure_given"):
        assert f[k] is False, k
    assert "never as a load" in f["consequence"]


# --- the annulus term, which is what closes -----------------------------

def test_all_ten_hpc_rotors_are_present():
    assert [r["stage"] for r in HPC] == list(range(1, 11))
    assert all(r["blades"] > 0 for r in HPC)


def test_the_annulus_term_is_dominated_by_pressure_not_momentum():
    for r in HPC:
        assert abs(r["pressure_N"]) > 5 * abs(r["momentum_N"]), r["stage"]


def test_continuity_holds_across_the_rotor_stations():
    """a check on the streamline areas and the pressure chain -- if this
    fails the loads mean nothing"""
    for r in hpc_continuity_check():
        err = abs(r["w_implied"] / r["w_cycle"] - 1) * 100
        assert err < 15.0, (r["stage"], err)


def test_the_hpc_annulus_term_pushes_aft_not_forward():
    """finding 192: STEP0 predicted forward and was wrong for THIS control
    volume -- the forward push is the disc-face term, which it excludes"""
    assert N["hpc_forward_N"] < 0
    assert G["annulus_is_aft"] is True
    assert abs(N["hpc_forward_N"]) / 1e3 == pytest.approx(106, abs=8)


def test_the_two_hpt_rotors_are_present_and_oppose_each_other():
    assert [r["stage"] for r in HPT] == [1, 2]
    assert HPT[0]["forward_N"] * HPT[1]["forward_N"] < 0


# --- the term that dominates, and the gate ------------------------------

def test_the_disc_face_force_is_forward_and_falls_with_bore_radius():
    c = disc_face_curve()
    f = [r["forward_N"] for r in c]
    assert all(x > 0 for x in f)
    assert f == sorted(f, reverse=True)      # bigger bore, less area


def test_the_disc_face_term_dominates_the_annulus_term():
    lo, hi = G["times_annulus_range"]
    assert lo > 3.0 and hi > 6.0


def test_the_disc_face_area_uses_the_published_hub_line():
    d = disc_face_force(0.12)
    assert d["r_hub_aft_m"] == pytest.approx(0.274, abs=0.002)
    assert d["area_m2"] > 0


def test_the_unit_is_gated_on_the_same_figure_as_e2_and_f2():
    assert "bore" in G["gated_on"] and "disc profile" in G["gated_on"]
    assert "F2 disc masses" in G["same_gate_as"]
    assert len(G["same_gate_as"]) == 3


def test_no_bore_radius_is_chosen():
    """the answer is a curve; picking a bore would invent the gate away"""
    src = (pathlib.Path(__file__).resolve().parents[1]
           / "solvers/thermal/thrust_balance.py").read_text()
    assert "returns a curve" in src
    import inspect
    from thermal import thrust_balance as tb
    assert "r_bore_m" in inspect.signature(tb.disc_face_force).parameters


# --- what is not claimed ------------------------------------------------

def test_the_balance_itself_is_not_claimed():
    n = what_is_not_published()
    for k in ("piston_area", "piston_radius", "cavity_pressures",
              "disc_face_areas", "bearing_1_load", "bearing_3_load",
              "bearing_capacity", "mission_sweep"):
        assert n[k] is False, k
    assert "not closed" in n["consequence"]


def test_the_summary_says_gated_and_why():
    s = summary()
    assert "GATED on" in s
    assert "same gate as" in s
    assert "thrust False" in s
