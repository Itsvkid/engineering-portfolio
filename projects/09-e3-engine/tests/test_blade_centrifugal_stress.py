"""Stage E unit E1: HPC blade root centrifugal stress from the section
geometry (solvers/mechanical/STEP0.md unit E1). The band is the work
plan's own E1 closure: 10 % on all ten stages."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from mechanical.blade_stress import (  # noqa: E402
    RHO_NICKEL, RHO_TITANIUM, all_stages, area_distribution, root_stress, stress_speed_rpm,
)

ROWS = all_stages()
BY = {r.stage: r for r in ROWS}
BAND = 0.10
TITANIUM_STAGES = (1, 2, 3, 4)
NICKEL_STAGES = (5, 6, 7, 8, 9, 10)


def test_the_stress_case_is_the_deteriorated_engine_speed():
    """finding 75: Table X's footnote, not the aero design point"""
    assert stress_speed_rpm() == 13948


def test_all_ten_stages_are_present():
    assert len(ROWS) == 10
    assert [r.stage for r in ROWS] == list(range(1, 11))
    for r in ROWS:
        assert len(area_distribution(r.stage)) == 12
        assert r.r_tip_m > r.r_root_m > 0.15


@pytest.mark.parametrize("stage", TITANIUM_STAGES)
def test_the_forward_stages_match_titanium(stage):
    r = BY[stage]
    assert abs(r.sigma_titanium_kN_cm2 / r.printed_kN_cm2 - 1) < BAND


@pytest.mark.parametrize("stage", NICKEL_STAGES)
def test_the_aft_stages_match_nickel(stage):
    r = BY[stage]
    assert abs(r.sigma_nickel_kN_cm2 / r.printed_kN_cm2 - 1) < BAND


def test_neither_material_works_for_both_groups():
    """finding 74: the discrimination is what locates the weld"""
    for s in NICKEL_STAGES:
        assert BY[s].sigma_titanium_kN_cm2 / BY[s].printed_kN_cm2 - 1 < -0.35
    for s in TITANIUM_STAGES:
        assert BY[s].sigma_nickel_kN_cm2 / BY[s].printed_kN_cm2 - 1 > 0.7


def test_the_crossover_is_between_stages_four_and_five():
    ti_ok = [r.stage for r in ROWS if abs(r.sigma_titanium_kN_cm2 / r.printed_kN_cm2 - 1) < BAND]
    ni_ok = [r.stage for r in ROWS if abs(r.sigma_nickel_kN_cm2 / r.printed_kN_cm2 - 1) < BAND]
    assert ti_ok == list(TITANIUM_STAGES)
    assert ni_ok == list(NICKEL_STAGES)
    assert max(ti_ok) + 1 == min(ni_ok)


def test_e1_closure_every_stage_within_ten_percent():
    """with the material each stage actually uses"""
    for r in ROWS:
        best = r.sigma_titanium_kN_cm2 if r.stage in TITANIUM_STAGES else r.sigma_nickel_kN_cm2
        assert abs(best / r.printed_kN_cm2 - 1) < BAND


def test_using_the_aero_design_speed_would_read_every_stage_low():
    """finding 75: a factor of 1.29 in stress"""
    for stage in (1, 5, 10):
        rho = RHO_TITANIUM if stage in TITANIUM_STAGES else RHO_NICKEL
        at_design, *_ = root_stress(stage, rho, rpm=12303)
        at_stress, *_ = root_stress(stage, rho, rpm=stress_speed_rpm())
        assert at_design / at_stress < 0.80
        assert abs(at_design / at_stress - (12303 / 13948) ** 2) < 1e-9


def test_taper_reduces_the_stress_substantially():
    """finding 76"""
    for r in ROWS:
        assert 0.5 < r.taper_factor < 0.85
    assert BY[1].taper_factor < BY[6].taper_factor      # longest blade tapered hardest
