"""Stage D unit D5: the combustor exit (the work plan's D2)
(solvers/thermal/STEP0.md unit D5)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from thermal.combustor import (  # noqa: E402
    airflow_split, implied_combustor_exit_temperature, pattern_factor,
    profile_temperatures, radial_profile,
)

GROUPS, TOTAL, PRINTED, N_LABELS = airflow_split()
IMP = implied_combustor_exit_temperature()
RP = radial_profile()
PF_REQUIRED = 0.25


def test_the_airflow_split_closes_exactly():
    """finding 70"""
    assert N_LABELS == 24
    assert abs(TOTAL - PRINTED) < 1e-9
    assert abs(TOTAL - 100.0) < 1e-9


def test_most_of_the_core_flow_is_cooling_and_dilution():
    domes = GROUPS["pilot dome"] + GROUPS["main dome"]
    assert 39 < domes < 42
    assert TOTAL - domes > 55


@pytest.mark.xfail(strict=True, reason="unit D5 finding 71: T41 is the ROTOR inlet, downstream of the nonchargeable coolant, not the combustor exit average. Used as the average it gives PF 0.386 against a 0.25 requirement.")
def test_t41_can_be_used_as_the_combustor_exit_average():
    assert IMP["pf_if_t41_were_the_average"] < PF_REQUIRED


def test_the_wrong_reading_is_pinned():
    assert 0.35 < IMP["pf_if_t41_were_the_average"] < 0.42
    assert IMP["pf_if_t41_were_the_average"] > 1.4 * PF_REQUIRED


def test_the_implied_combustor_exit_is_above_the_rotor_inlet():
    """finding 71: the gap is the nonchargeable coolant's work"""
    assert IMP["t4_implied_C"] > IMP["t41_design_C"]
    assert 60 < IMP["drop_across_coolant_C"] < 110


def test_it_agrees_with_what_stage_b_computed_independently():
    """Stage B's cycle solver put the combustor-exit-to-rotor-inlet drop at
    55 K at max climb with 7.46 % nonchargeable; this design point runs
    9.46 % at a hotter condition"""
    from e3cycle.cycle import load_inputs, solve_rating
    inp = load_inputs()
    res = solve_rating(next(r for r in inp.ratings if r.name == "max_climb"), inp)
    b_drop = res.stations["t4"] - res.stations["t41"]
    assert 40 < b_drop < 80
    assert IMP["drop_across_coolant_C"] > b_drop        # more coolant, hotter gas
    assert IMP["drop_across_coolant_C"] < 2.5 * b_drop


def test_the_pattern_factor_formula():
    assert abs(pattern_factor(1739, 1503, 597) - 0.26) < 0.01
    assert abs(pattern_factor(1421, 1421, 597)) < 1e-12


def test_the_profile_peaks_where_the_blade_is_rupture_limited():
    """finding 72"""
    assert RP["design_profile"]["peak_at_pct_height"] == 65
    assert RP["design_profile"]["peak"] > 0
    assert RP["design_profile"]["hub"] < -0.2 and RP["design_profile"]["tip"] < -0.2
    assert "rupture-limiting" in RP["note"]


def test_the_pattern_factor_limit_does_not_police_the_ends():
    assert RP["pf_limit_span_pct"] == [20, 90]


def test_the_profile_as_temperatures_is_sensible():
    t = profile_temperatures()
    assert t["peak"] > t["at_20pct"] > t["hub"]
    assert abs(t["hub"] - t["tip"]) < 1.0        # symmetric ends by design
    assert t["peak"] < IMP["t40_max_C"]          # the hot streak is above the profile
