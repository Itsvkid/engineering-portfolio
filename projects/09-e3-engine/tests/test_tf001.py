"""Stage L: ME TF0.01, a higher-bypass derivative of the E3 on a fixed core
(solvers/derivative/STEP0.md).

The bands are step 0's, and they are written to be able to fail. Band 1
checks the excursion machinery returns the E3 before it leaves it; band 3
checks the LPT stage count falls out of a measured loading limit rather
than being chosen. Both compare against published numbers.
"""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from derivative.tf001 import (  # noqa: E402
    FPR_BRACKET, LOADING_LIMIT, LPT_R_PITCH, M_AXIAL, M_REL_CEILING,
    MAX_EXTRA_LPT_STAGES, DH_LPT_TABLE_II, N_E3_RPM, Excursion,
    blade_root_stress, e3_mean_stage_loading, fan_radius, rpm_for_stages,
    stages_needed, tip_relative_mach,
)

PUBLISHED_FAN_DIAMETER_M = 2.108      # CR-165148 Table IV p.47 (210.8 cm)
PUBLISHED_M_REL_TIP = 1.41            # CR-165148 Fig.10, tip section
PUBLISHED_U_TIP_CORRECTED = 411.5     # CR-165148 Table I p.4, max climb


@pytest.fixture(scope="module")
def ex():
    return Excursion()


@pytest.fixture(scope="module")
def sweep(ex):
    return ex.sweep()


# ── band 1: the baseline reproduces the E3 before the excursion leaves it ──

def test_band1_the_swept_baseline_returns_the_e3_cycle(ex, sweep):
    """Run the excursion machinery at the E3's own bypass ratio and it must
    return the E3, not something near it."""
    p = sweep[0]
    assert p.bpr == pytest.approx(6.7)
    assert abs(p.sfc / ex.base.sfc_kg_N_h - 1) < 0.001, "sfc within 0.1 %"
    assert abs(p.dsfc_pct) < 0.1


def test_band1_the_fan_diameter_reproduces_the_published_one(sweep):
    """Continuity on the published specific flow and radius ratio, against a
    diameter printed in a different table."""
    got = sweep[0].fan_diameter_m
    assert abs(got / PUBLISHED_FAN_DIAMETER_M - 1) < 0.005, f"{got:.4f} m"


def test_band1_the_tip_relative_mach_reproduces_the_published_one():
    """A specific flow and a corrected tip speed are a velocity triangle, and
    neither of the two inputs mentions a Mach number."""
    assert abs(tip_relative_mach(PUBLISHED_U_TIP_CORRECTED) - PUBLISHED_M_REL_TIP) < 0.02


def test_band1_the_stage_count_returns_five_at_the_e3s_own_speed(sweep):
    n = stages_needed(sweep[0].lpt_dh_J_kg, N_E3_RPM)
    assert abs(n - 5.0) < 0.15, f"{n:.3f} stages"


# ── band 2: the mixer closure holds across the sweep ──────────────────────

def test_band2_the_mixer_matches_at_every_swept_point(ex, sweep):
    for p in sweep:
        assert abs(p.p5_over_p13 - ex.mixer_target) < 1e-4, p.bpr


def test_band2_the_fan_pressure_ratio_stays_inside_a_physical_bracket(sweep):
    for p in sweep:
        assert not p.fpr_at_bracket_end, f"BPR {p.bpr} pinned at a bracket end"
        assert FPR_BRACKET[0] < p.fpr_bypass < FPR_BRACKET[1]


def test_the_mixer_target_is_the_e3s_published_band(ex):
    """0.95-0.96 at all three ratings is the published behaviour; the solve
    target has to sit in it or the constraint is the wrong one."""
    assert 0.95 <= ex.mixer_target <= 0.96


# ── band 3: the stage count falls out of a limit, not a choice ────────────

def test_band3_the_loading_limit_is_measured_on_the_e3(ex):
    """Not a textbook number: Table II's five printed energy extractions over
    the five pitch radii derived from the transcribed airfoil coordinates."""
    assert len(LPT_R_PITCH) == 5
    assert LOADING_LIMIT == pytest.approx(e3_mean_stage_loading())
    assert 1.0 < LOADING_LIMIT < 1.5, LOADING_LIMIT
    # and it is the E3's own five stages by construction
    u_sq = (N_E3_RPM * 2 * math.pi / 60) ** 2 * sum(r ** 2 for r in LPT_R_PITCH.values()) / 5
    assert DH_LPT_TABLE_II / 5 / (2 * u_sq) == pytest.approx(LOADING_LIMIT)


def test_band3_two_independent_routes_to_the_lpt_work_agree(ex):
    """The five PRINTED energy extractions of LPT Table II against the cycle
    solver's own LPT specific work, which comes from the fan power and the
    spool balance and never saw Table II. Nothing was fitted between them."""
    solver = ex.base.stations["lpt_dh_per_kg"]
    assert abs(solver / DH_LPT_TABLE_II - 1) < 0.01, \
        f"{solver/1e3:.1f} vs {DH_LPT_TABLE_II/1e3:.1f} kJ/kg"


def test_the_stage_count_and_the_speed_are_inverses(sweep):
    for p in sweep[::3]:
        for n in (5, 6, 7):
            assert stages_needed(p.lpt_dh_J_kg, rpm_for_stages(p.lpt_dh_J_kg, n)) == pytest.approx(n)


# ── band 4: the fan tip Mach ceiling, fixed before the answer ─────────────

def test_band4_the_ceiling_is_above_the_e3_and_stated_in_advance():
    assert M_REL_CEILING == 1.45
    assert M_REL_CEILING > PUBLISHED_M_REL_TIP


def test_band4_the_largest_direct_drive_bpr_satisfies_its_own_definition(ex):
    best = ex.largest_direct_drive_bpr()
    assert best is not None
    a = ex.architecture(ex.point(best), 5 + MAX_EXTRA_LPT_STAGES)
    assert a["m_rel_tip"] <= M_REL_CEILING + 1e-3
    # and it is a real boundary: a little more bypass breaks it
    worse = ex.architecture(ex.point(best + 0.3), 5 + MAX_EXTRA_LPT_STAGES)
    assert worse["m_rel_tip"] > M_REL_CEILING


def test_band4_five_lpt_stages_is_rejected_at_high_bypass(ex, sweep):
    """The scoping answer that did NOT survive the stated ceiling."""
    a = ex.architecture(sweep[-1], 5)
    assert a["m_rel_tip"] > 1.6 and not a["within_ceiling"]


def test_seven_stages_at_bpr_ten_misses_the_ceiling_it_was_scoped_against(ex, sweep):
    """Scoping called 7 stages at BPR 10 'closes'. Against the ceiling written
    down in step 0 it does not -- 1.47 against 1.45. Pinned so the correction
    cannot quietly revert."""
    a = ex.architecture(sweep[-1], 7)
    assert 1.46 < a["m_rel_tip"] < 1.48
    assert not a["within_ceiling"]
    assert ex.architecture(sweep[-1], 8)["within_ceiling"]


# ── band 5: the core really is untouched ──────────────────────────────────

def test_band5_every_core_station_is_invariant_across_the_sweep(ex, sweep):
    ref = ex.core_invariants(sweep[0])
    for p in sweep[1:]:
        got = ex.core_invariants(p)
        for k, v in ref.items():
            assert abs(got[k] / v - 1) < 1e-6, f"{k} moved at BPR {p.bpr}"


def test_the_bypass_flow_is_what_grows(sweep):
    a, b = sweep[0], sweep[-1]
    assert b.w_core_kg_s == pytest.approx(a.w_core_kg_s, rel=1e-6)
    byp_a, byp_b = a.w2_kg_s - a.w_core_kg_s, b.w2_kg_s - b.w_core_kg_s
    assert byp_b / byp_a > 1.45


# ── the results themselves ────────────────────────────────────────────────

def test_sfc_falls_monotonically_with_bypass_ratio(sweep):
    for x, y in zip(sweep, sweep[1:]):
        assert y.sfc < x.sfc and y.fan_diameter_m > x.fan_diameter_m
        assert y.fpr_bypass < x.fpr_bypass and y.lpt_dh_J_kg > x.lpt_dh_J_kg


def test_the_shaft_speed_conflict_is_the_result(ex, sweep):
    """At the E3's own bypass ratio the fan and the LPT want the same shaft;
    at BPR 10 they are ~46 % apart. That gap IS the gearbox ratio."""
    at_e3 = ex.shaft_speed_conflict(sweep[0])
    at_10 = ex.shaft_speed_conflict(sweep[-1])
    assert abs(at_e3["gear_ratio"] - 1.0) < 0.02, "the E3 is a matched direct drive"
    assert 1.40 < at_10["gear_ratio"] < 1.55


def test_the_fan_loading_is_computed_in_one_frame(ex, sweep):
    """psi = dh/U^2 is frame-invariant only if dh and U are in the SAME frame.
    The published 411.5 m/s is CORRECTED and the cycle's dh is PHYSICAL;
    mixing them reads psi low by exactly theta. Pinned at the right value."""
    psi = ex.shaft_speed_conflict(sweep[0])["fan_psi"]
    assert psi == pytest.approx(0.3056, abs=0.002)
    theta = ex.base.stations["t0"] / 288.15
    mixed = psi * theta
    assert mixed == pytest.approx(0.2738, abs=0.002), "the wrong answer, for the record"


def test_the_gearbox_ratio_is_too_small_to_argue_for(ex, sweep):
    """A 1.46:1 reduction is the whole case for a gearbox here, against ~3:1
    on a real geared fan. The unit reports the number rather than the slogan."""
    for n, lo, hi in ((5, 1.40, 1.55), (4, 1.55, 1.75), (3, 1.80, 2.00)):
        g = ex.shaft_speed_conflict(sweep[-1], n_stages_target=n)["gear_ratio"]
        assert lo < g < hi, f"{n} stages -> {g:.3f}"


def test_the_quarter_stage_booster_does_not_survive(ex, sweep):
    """Fan hub and bypass are the same rotor, so a lower bypass PR drops the
    hub's too; holding the core supercharged falls to the booster."""
    b = ex.booster_loading(sweep[-1], 7)
    assert b["e3_pitch_loading"] == pytest.approx(0.235, abs=0.01)
    ratio = b["loading_if_one_stage"] / b["e3_pitch_loading"]
    assert 1.8 < ratio < 2.0, f"loading rises {ratio:.2f}x"
    assert b["loading_if_one_stage"] > 0.40, "at or past the subsonic stage limit"
    assert b["stages_at_psi_040"] > 1.0, "one comfortable stage no longer does it"
    assert b["fan_hub_pr"] < 1.40


def test_the_held_efficiency_assumption_is_priced(ex):
    s = ex.fan_efficiency_sensitivity(delta=-0.01)
    assert 0.5 < s["pct_sfc_per_point"] < 0.9
    assert s["sfc_perturbed"] > s["sfc_ref"]


def test_blade_root_stress_does_not_run_away_with_the_bigger_fan(ex, sweep):
    """A bigger fan turns slower, so AN^2 barely moves -- the tip Mach binds
    this design, not the blade stress."""
    e3 = blade_root_stress(sweep[0].fan_annulus_m2, N_E3_RPM)
    d = ex.architecture(sweep[-1], 8)["root_stress_Pa"]
    assert 0.85 < d / e3 < 1.05


def test_the_fan_face_axial_mach_is_the_published_match_point_value():
    assert M_AXIAL == pytest.approx(0.63, abs=0.01)


def test_fan_radius_inverts_the_annulus(sweep):
    for p in sweep[::3]:
        assert fan_radius(p.w2_corrected_kg_s) == pytest.approx(p.fan_diameter_m / 2)
