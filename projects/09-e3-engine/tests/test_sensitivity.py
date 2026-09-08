"""Stage I unit I2: sensitivity
(solvers/verification/STEP0.md unit I2).

Six of these elasticities have exact analytic values. They are the step-0
validation: a sensitivity machine that cannot reproduce a derivative you
can do by hand has no business reporting the ones you cannot."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from verification.sensitivity import (  # noqa: E402
    disc_stress_sensitivities, handbook_exposure, metal_temperature_sensitivities,
    sfc_sensitivities,
)

SFC = {s.parameter: s for s in sfc_sensitivities()}
MET = {s.parameter: s for s in metal_temperature_sensitivities()}
DISC = {s.parameter: s for s in disc_stress_sensitivities()}


# --- the analytic checks ---------------------------------------------------

def test_combustor_efficiency_elasticity_on_sfc_is_minus_one():
    """sfc is fuel over thrust and fuel goes as 1/eta_comb"""
    assert SFC["combustor_efficiency"].elasticity == pytest.approx(-1.0, abs=0.02)


def test_density_elasticity_on_disc_stress_is_plus_one():
    assert DISC["density (Rene 95, handbook)"].elasticity == pytest.approx(1.0, abs=0.01)


def test_speed_and_radius_elasticities_on_disc_stress_are_plus_two():
    """sigma goes as rho omega^2 b^2"""
    assert DISC["rotor speed"].elasticity == pytest.approx(2.0, abs=0.01)
    assert DISC["rim radius"].elasticity == pytest.approx(2.0, abs=0.02)


def test_the_two_metal_temperatures_have_elasticities_summing_to_one():
    """T_m is a weighted average of T_gas and T_coolant and of nothing else"""
    total = MET["gas temperature"].elasticity + MET["coolant temperature"].elasticity
    assert total == pytest.approx(1.0, abs=0.01)


def test_the_two_heat_transfer_coefficients_are_equal_and_opposite():
    """only their ratio enters the wall balance"""
    a = MET["gas-side coefficient h_g (Fig 23)"].elasticity
    b = MET["internal conductance H_c (fitted, unit D2)"].elasticity
    assert a == pytest.approx(-b, abs=0.01)


# --- the findings ----------------------------------------------------------

def test_the_nozzle_coefficient_dominates_the_cycle():
    """finding 151 -- more leverage than any efficiency in the engine"""
    worst = sfc_sensitivities()[0]
    assert worst.parameter == "nozzle_coefficient"
    assert abs(worst.elasticity) > 2.0
    assert abs(worst.elasticity) > 5 * abs(SFC["hpt_efficiency"].elasticity)


def test_compressor_efficiency_barely_moves_the_fuel_burn():
    """finding 152 -- the flat rating cancels it: a worse compressor
    delivers hotter air and needs less fuel to reach the same T41"""
    assert abs(SFC["compressor_efficiency"].elasticity) < 0.1
    assert abs(SFC["compressor_efficiency"].elasticity) < \
        abs(SFC["hpt_efficiency"].elasticity)


def test_only_the_disc_stress_leans_on_handbook_constants():
    """finding 153"""
    ex = handbook_exposure()
    sfc = [v for k, v in ex.items() if k.startswith("sfc")][0]
    disc = [v for k, v in ex.items() if "disc" in k][0]
    metal = [v for k, v in ex.items() if "metal" in k][0]
    assert sfc["handbook_share_pct"] == 0.0
    assert metal["handbook_share_pct"] == 0.0
    assert 10 < disc["handbook_share_pct"] < 35


def test_poissons_ratio_hardly_matters():
    """finding 153 -- being 10 % wrong about it moves the answer under 1 %"""
    assert abs(DISC["Poisson's ratio (handbook)"].elasticity) < 0.1


def test_every_parameter_is_labelled_by_where_it_came_from():
    for d in (SFC, MET, DISC):
        for s in d.values():
            assert s.kind in ("published", "measured", "handbook")
