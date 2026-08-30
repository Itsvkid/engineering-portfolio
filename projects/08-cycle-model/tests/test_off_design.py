"""The simplified single-parameter throttle model. No pyOCC — runs
anywhere."""

from __future__ import annotations

import pytest

from src.cycle import TurbofanDesignPoint, solve_cycle
from src.off_design import solve_off_design, throttle_design_point

REFERENCE = TurbofanDesignPoint(
    altitude=10668.0, mach=0.78,
    core_mass_flow=40.0, bypass_ratio=6.0,
    fan_pressure_ratio=1.6, booster_pressure_ratio=1.6, hpc_pressure_ratio=14.0,
    turbine_entry_temperature=1650.0,
)


def test_full_throttle_returns_the_reference_design_unmodified():
    """throttle=1.0 is the reference design itself, not a floating-point
    round-trip through the scaling formula that happens to land close to
    it — checked as object identity, not just numeric closeness."""
    assert throttle_design_point(REFERENCE, 1.0) is REFERENCE


def test_rejects_throttle_out_of_range():
    with pytest.raises(ValueError):
        throttle_design_point(REFERENCE, 0.0)
    with pytest.raises(ValueError):
        throttle_design_point(REFERENCE, 1.1)
    with pytest.raises(ValueError):
        throttle_design_point(REFERENCE, -0.5)


def test_pressure_ratios_scale_with_throttle_squared():
    """The defining identity of the scaling law this module uses:
    (PR_off - 1) / (PR_design - 1) == throttle**2, exactly, for every
    compressor — checked directly against the design point construction,
    not inferred from downstream thrust numbers."""
    throttle = 0.8
    design = throttle_design_point(REFERENCE, throttle)
    for name in ("fan_pressure_ratio", "booster_pressure_ratio", "hpc_pressure_ratio"):
        design_pr = getattr(REFERENCE, name)
        off_pr = getattr(design, name)
        assert (off_pr - 1.0) / (design_pr - 1.0) == pytest.approx(throttle ** 2)


def test_turbine_entry_temperature_scales_linearly_with_throttle():
    throttle = 0.8
    design = throttle_design_point(REFERENCE, throttle)
    assert design.turbine_entry_temperature == pytest.approx(
        REFERENCE.turbine_entry_temperature * throttle
    )


def test_other_design_inputs_are_unchanged_by_throttle():
    """Only pressure ratios and TET move — altitude, mach, mass flow,
    bypass ratio and every efficiency stay exactly what the reference
    design specified, per the module's documented simplifications."""
    design = throttle_design_point(REFERENCE, 0.75)
    assert design.altitude == REFERENCE.altitude
    assert design.mach == REFERENCE.mach
    assert design.core_mass_flow == REFERENCE.core_mass_flow
    assert design.bypass_ratio == REFERENCE.bypass_ratio
    assert design.fan_efficiency == REFERENCE.fan_efficiency
    assert design.hpt_efficiency == REFERENCE.hpt_efficiency


def test_low_throttle_eventually_hits_the_existing_tet_floor():
    """throttle_design_point does not duplicate TurbofanDesignPoint's own
    "implausibly low TET" guard with a second bound — it reuses it. A low
    enough throttle on this reference design (TET 1650 K) scales TET below
    the existing 1000 K floor and the same ValueError propagates
    unmodified."""
    with pytest.raises(ValueError, match="implausibly low"):
        throttle_design_point(REFERENCE, 0.5)


def test_solve_off_design_at_full_throttle_matches_solve_cycle_exactly():
    """An end-to-end identity check, not just on the design point
    construction: solving through solve_off_design at throttle=1.0 must
    reproduce solve_cycle(REFERENCE)'s net thrust exactly, since it is
    solving the exact same design point."""
    direct = solve_cycle(REFERENCE)
    via_throttle = solve_off_design(REFERENCE, 1.0)
    assert via_throttle.net_thrust == direct.net_thrust


def test_net_thrust_falls_monotonically_as_throttle_is_reduced():
    throttles = [1.0, 0.9, 0.8, 0.7, 0.62]
    thrusts = [solve_off_design(REFERENCE, t).net_thrust for t in throttles]
    assert thrusts == sorted(thrusts, reverse=True)


def test_tsfc_worsens_monotonically_as_throttle_is_reduced():
    """Not obviously true a priori for every possible engine or throttle
    law — checked here as an actual property of this reference design and
    this scaling law, the same "verify, don't just assume" pattern the
    rest of this project holds itself to, rather than asserted as a
    general law of turbofans."""
    throttles = [1.0, 0.9, 0.8, 0.7, 0.62]
    tsfcs = [solve_off_design(REFERENCE, t).tsfc_g_per_kns for t in throttles]
    assert tsfcs == sorted(tsfcs)


def test_thermal_and_overall_efficiency_fall_monotonically_as_throttle_is_reduced():
    throttles = [1.0, 0.9, 0.8, 0.7, 0.62]
    thermal = [solve_off_design(REFERENCE, t).thermal_efficiency for t in throttles]
    overall = [solve_off_design(REFERENCE, t).overall_efficiency for t in throttles]
    assert thermal == sorted(thermal, reverse=True)
    assert overall == sorted(overall, reverse=True)


def test_part_throttle_produces_a_physically_plausible_cycle():
    """Not a precision check — a sanity floor, the same kind
    test_cycle.py's test_reference_design_produces_a_physically_plausible_
    cycle already runs on the full-throttle design."""
    cycle = solve_off_design(REFERENCE, 0.75)
    assert cycle.net_thrust > 0
    assert 5.0 < cycle.tsfc_g_per_kns < 40.0
    assert 0.0 < cycle.thermal_efficiency < 1.0
    assert 0.0 < cycle.fuel_air_ratio < 0.06
