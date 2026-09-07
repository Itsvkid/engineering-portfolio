"""Stage C4 unit 1: the solver against an exact answer
(solvers/cfd/STEP0.md unit C4-1).

The exact Riemann solver is tested unconditionally -- it is pure arithmetic
and it is the known answer everything else leans on. The comparison with
OpenFOAM is skipped when the run directory is absent, because the run needs
a Docker daemon and the outputs are gitignored: `./cfd/run_shocktube.sh`
regenerates them."""
import math
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solvers"))
from cfd.shocktube import (  # noqa: E402
    CASE, GAMMA, R_SPECIFIC, State, compare, exact_profile, sample, star_state,
    wave_speeds,
)

LEFT = State(100000.0 / (R_SPECIFIC * 348.432), 0.0, 100000.0)
RIGHT = State(10000.0 / (R_SPECIFIC * 278.746), 0.0, 10000.0)
P_STAR, U_STAR = star_state(LEFT, RIGHT)
has_run = pytest.mark.skipif(not (CASE / "0.007" / "p").exists(),
                             reason="no OpenFOAM run; ./cfd/run_shocktube.sh regenerates it")


# --- the exact solver's own known answer ----------------------------------

def test_the_case_really_is_sods_problem():
    assert LEFT.rho == pytest.approx(1.0, abs=0.001)
    assert RIGHT.rho == pytest.approx(0.125, abs=0.001)
    assert LEFT.p / RIGHT.p == pytest.approx(10.0)


def test_the_exact_solver_returns_sods_textbook_star_pressure():
    """finding 125 -- without this the CFD comparison is a program
    agreeing with itself"""
    assert P_STAR / LEFT.p == pytest.approx(0.30313, abs=0.001)


def test_the_star_state_satisfies_the_rankine_hugoniot_shock_jump():
    """mass and momentum across the right-running shock, from first
    principles rather than from the solver's own internals"""
    s = wave_speeds(LEFT, RIGHT, P_STAR, U_STAR)["shock"]
    post = sample(s - 1e-6, LEFT, RIGHT, P_STAR, U_STAR)   # just behind it
    # in the shock frame: rho1 (S - u1) = rho2 (S - u2)
    m1 = RIGHT.rho * (s - RIGHT.u)
    m2 = post.rho * (s - post.u)
    assert m1 == pytest.approx(m2, rel=1e-6)
    # momentum: p1 + rho1 (S-u1)^2 = p2 + rho2 (S-u2)^2
    f1 = RIGHT.p + RIGHT.rho * (s - RIGHT.u) ** 2
    f2 = post.p + post.rho * (s - post.u) ** 2
    assert f1 == pytest.approx(f2, rel=1e-6)


def test_the_contact_carries_a_density_jump_and_no_pressure_jump():
    eps = 1e-9
    a = sample(U_STAR - eps, LEFT, RIGHT, P_STAR, U_STAR)
    b = sample(U_STAR + eps, LEFT, RIGHT, P_STAR, U_STAR)
    assert a.p == pytest.approx(b.p, rel=1e-9)
    assert a.u == pytest.approx(b.u, rel=1e-9)
    assert a.rho > 1.5 * b.rho


def test_entropy_is_constant_through_the_expansion_fan_and_rises_over_the_shock():
    s = wave_speeds(LEFT, RIGHT, P_STAR, U_STAR)
    def entropy(st):
        return st.p / st.rho ** GAMMA
    fan_mid = sample(0.5 * (s["fan_head"] + s["fan_tail"]), LEFT, RIGHT, P_STAR, U_STAR)
    assert entropy(fan_mid) == pytest.approx(entropy(LEFT), rel=1e-6)
    post_shock = sample(s["shock"] - 1e-6, LEFT, RIGHT, P_STAR, U_STAR)
    assert entropy(post_shock) > entropy(RIGHT)


def test_the_waves_are_ordered_and_the_shock_is_supersonic_ahead_of_it():
    s = wave_speeds(LEFT, RIGHT, P_STAR, U_STAR)
    assert s["fan_head"] < s["fan_tail"] < s["contact"] < s["shock"]
    assert (s["shock"] - RIGHT.u) / RIGHT.a > 1.0        # it really is a shock


def test_far_from_the_diaphragm_the_solution_is_still_the_initial_state():
    got, _, _ = exact_profile([-4.9, 4.9], 0.007, LEFT, RIGHT)
    assert got[0].p == pytest.approx(LEFT.p)
    assert got[1].p == pytest.approx(RIGHT.p)


# --- OpenFOAM against it ---------------------------------------------------

@has_run
def test_openfoam_reproduces_the_star_pressure():
    """finding 124"""
    c = compare()
    assert abs(c["p_star_err_pct"]) < 2.0
    assert abs(c["p_star_err_pct"]) < 0.5          # in fact 0.02 %


@has_run
def test_openfoam_reproduces_the_star_velocity():
    assert abs(compare()["u_star_err_pct"]) < 3.0


@has_run
def test_the_shock_lands_within_two_cells_of_the_exact_position():
    c = compare()
    cells = abs(c["shock_x_cfd"] - c["shock_x_exact"]) / c["dx"]
    assert cells < 2.0


@has_run
def test_the_l2_errors_are_inside_their_bands():
    c = compare()
    assert c["l2_p"] < 0.05
    assert c["l2_rho"] < 0.05
    assert c["l2_u"] < 0.08


@has_run
def test_the_error_is_ordered_the_way_discretisation_orders_it():
    """finding 126 -- pressure is continuous across the contact, density
    jumps there, velocity carries the dissipation of fan and contact both.
    A coding error would not put the error in the expected order."""
    c = compare()
    assert c["l2_p"] < c["l2_rho"] < c["l2_u"]
