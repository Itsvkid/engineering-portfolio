"""Gas properties and the ideal-cycle reference formula. No pyOCC anywhere
in this project — every test here runs in plain Python."""

from __future__ import annotations

import math

import pytest

from src.gas import AIR, COMBUSTION_GAS, GasProperties, ideal_brayton_efficiency, \
    isentropic_area_mach_ratio, isentropic_temperature_ratio


def test_rejects_nonpositive_cp():
    with pytest.raises(ValueError):
        GasProperties(cp=0.0, gamma=1.4)


def test_rejects_gamma_not_greater_than_one():
    with pytest.raises(ValueError):
        GasProperties(cp=1005.0, gamma=1.0)


def test_r_derived_from_cp_and_gamma_matches_known_air_value():
    """cp - cv = R, gamma = cp/cv => R = cp*(1 - 1/gamma). For air's
    standard values this has to land near the textbook 287 J/(kg*K), not
    just be positive."""
    assert AIR.r == pytest.approx(287.14, abs=1.0)


def test_combustion_gas_has_higher_cp_and_lower_gamma_than_air():
    """The whole reason two GasProperties exist: burned gas is not air.
    Higher cp (more triatomic CO2/H2O), lower gamma follows from cp/cv."""
    assert COMBUSTION_GAS.cp > AIR.cp
    assert COMBUSTION_GAS.gamma < AIR.gamma


def test_isentropic_ratio_is_identity_at_pressure_ratio_one():
    assert isentropic_temperature_ratio(1.0, AIR) == pytest.approx(1.0)


def test_isentropic_ratio_compression_and_expansion_are_inverses():
    """Compressing by PR then expanding by 1/PR must return to the start —
    the isentropic relation is reversible by construction."""
    pr = 12.0
    up = isentropic_temperature_ratio(pr, AIR)
    down = isentropic_temperature_ratio(1.0 / pr, AIR)
    assert up * down == pytest.approx(1.0)


def test_ideal_brayton_efficiency_rejects_opr_at_or_below_one():
    with pytest.raises(ValueError):
        ideal_brayton_efficiency(1.0)
    with pytest.raises(ValueError):
        ideal_brayton_efficiency(0.5)


def test_ideal_brayton_efficiency_is_zero_in_the_opr_to_one_limit():
    """No compression, no cycle, no efficiency — the formula's own
    limiting case, checked the same way project 07 checks a zero-camber
    section or project 06 checks zero exit swirl."""
    assert ideal_brayton_efficiency(1.0001) == pytest.approx(0.0, abs=1e-3)


def test_ideal_brayton_efficiency_increases_with_pressure_ratio():
    values = [ideal_brayton_efficiency(opr) for opr in (2, 5, 10, 20, 40, 80)]
    assert values == sorted(values)
    assert all(0.0 < v < 1.0 for v in values)


def test_ideal_brayton_efficiency_matches_hand_calculation():
    opr = 20.0
    expected = 1.0 - 1.0 / opr ** ((AIR.gamma - 1.0) / AIR.gamma)
    assert ideal_brayton_efficiency(opr, AIR) == pytest.approx(expected)


def test_area_mach_ratio_rejects_nonpositive_mach():
    with pytest.raises(ValueError):
        isentropic_area_mach_ratio(0.0, AIR)


def test_area_mach_ratio_is_exactly_one_at_sonic():
    """The defining property of A*: the sonic area is the reference area,
    so the ratio is 1 there by construction, not by coincidence."""
    assert isentropic_area_mach_ratio(1.0, AIR) == pytest.approx(1.0)


def test_area_mach_ratio_rises_on_both_sides_of_sonic():
    """A* is a minimum, not an endpoint — the reason a duct that keeps
    narrowing chokes at M=1 and can go no further: continuing to shrink
    area would require moving away from the minimum, which isn't possible
    on either branch of this curve."""
    subsonic = isentropic_area_mach_ratio(0.5, AIR)
    sonic = isentropic_area_mach_ratio(1.0, AIR)
    supersonic = isentropic_area_mach_ratio(2.0, AIR)
    assert subsonic > sonic
    assert supersonic > sonic


def test_area_mach_ratio_matches_hand_calculation_at_mach_two():
    mach = 2.0
    exponent = (AIR.gamma + 1.0) / (2.0 * (AIR.gamma - 1.0))
    bracket = (2.0 / (AIR.gamma + 1.0)) * (1.0 + 0.5 * (AIR.gamma - 1.0) * mach ** 2)
    expected = (1.0 / mach) * bracket ** exponent
    assert isentropic_area_mach_ratio(mach, AIR) == pytest.approx(expected)
