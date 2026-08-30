"""The assembled turbofan cycle. No pyOCC — runs anywhere.

These tests are what caught two real bugs during development: a propulsive
efficiency above 1 (physically impossible — see
test_propulsive_efficiency_never_exceeds_one and the fix documented in
TurbofanCycle.jet_kinetic_power) and a division by zero for a pure turbojet
(bypass_ratio=0 — see test_pure_turbojet_does_not_crash). Both are now
permanent regressions this suite guards against.
"""

from __future__ import annotations

import pytest

from src.cycle import TurbofanDesignPoint, solve_cycle, solve_cycle_with_cd_nozzle
from src.gas import AIR, ideal_brayton_efficiency

REFERENCE = TurbofanDesignPoint(
    altitude=10668.0, mach=0.78,
    core_mass_flow=40.0, bypass_ratio=6.0,
    fan_pressure_ratio=1.6, booster_pressure_ratio=1.6, hpc_pressure_ratio=14.0,
    turbine_entry_temperature=1650.0,
)


def _ideal(**overrides) -> TurbofanDesignPoint:
    """A loss-free design point: every efficiency 1, every pressure loss
    zero, one gas throughout — the limiting case the ideal-Brayton tests
    below are checked against.

    mach=0.01, not a realistic cruise Mach: ram compression is a real,
    correctly-modelled pressure rise this cycle includes (via freestream
    stagnation conditions) that the simple ideal_brayton_efficiency formula
    does not — that formula only knows about the compressor pressure
    ratio. At mach=0.78 the gap this creates is roughly 49%; at mach=0.01
    it is under 0.01%, small enough that these tests isolate the
    compressor/combustor/turbine thermodynamics cleanly rather than
    conflating them with ram effects the reference formula was never meant
    to capture.
    """
    defaults = dict(
        altitude=0.0, mach=0.01, core_mass_flow=40.0, bypass_ratio=0.0,
        fan_pressure_ratio=1.0001, booster_pressure_ratio=1.0001,
        hpc_pressure_ratio=2.0, turbine_entry_temperature=1650.0,
        intake_pressure_recovery=1.0, fan_efficiency=1.0, booster_efficiency=1.0,
        hpc_efficiency=1.0, combustor_efficiency=1.0, hpt_efficiency=1.0,
        lpt_efficiency=1.0, mechanical_efficiency=1.0, core_nozzle_efficiency=1.0,
        bypass_nozzle_efficiency=1.0, combustor_pressure_loss=0.0,
        bypass_duct_pressure_loss=0.0, cold_gas=AIR, hot_gas=AIR,
        fuel_lhv=43.0e6,
    )
    defaults.update(overrides)
    return TurbofanDesignPoint(**defaults)


# ── Design-point validation ─────────────────────────────────────────────


def test_rejects_supersonic_mach():
    with pytest.raises(ValueError):
        TurbofanDesignPoint(altitude=0, mach=1.5, core_mass_flow=40, bypass_ratio=6,
                            fan_pressure_ratio=1.6, booster_pressure_ratio=1.6,
                            hpc_pressure_ratio=14, turbine_entry_temperature=1650)


def test_rejects_pressure_ratio_at_or_below_one():
    with pytest.raises(ValueError):
        TurbofanDesignPoint(altitude=0, mach=0.5, core_mass_flow=40, bypass_ratio=6,
                            fan_pressure_ratio=1.0, booster_pressure_ratio=1.6,
                            hpc_pressure_ratio=14, turbine_entry_temperature=1650)


def test_overall_pressure_ratio_is_the_product_of_the_three_stages():
    assert REFERENCE.overall_pressure_ratio == pytest.approx(1.6 * 1.6 * 14.0)


# ── The two regression guards ───────────────────────────────────────────


def test_propulsive_efficiency_never_exceeds_one():
    """A physical bound, not a design target: no engine can deliver more
    thrust power than the kinetic power it adds to the flow, by energy
    conservation. Checked across several design points, not just the
    reference one, since the original bug (raw nozzle velocity in the
    kinetic-energy term, ignoring pressure thrust from a choked nozzle)
    only showed up when a nozzle was significantly underexpanded."""
    for bpr in (0.0, 2.0, 6.0, 10.0):
        for opr_hpc in (5.0, 14.0, 25.0):
            design = TurbofanDesignPoint(
                altitude=10668.0, mach=0.78, core_mass_flow=40.0, bypass_ratio=bpr,
                fan_pressure_ratio=1.6, booster_pressure_ratio=1.6,
                hpc_pressure_ratio=opr_hpc, turbine_entry_temperature=1650.0,
            )
            cycle = solve_cycle(design)
            assert cycle.propulsive_efficiency <= 1.0 + 1e-9, (bpr, opr_hpc)


def test_pure_turbojet_does_not_crash():
    """bypass_ratio=0 divides bypass_gross_thrust by bypass_mass_flow=0
    unless guarded — see bypass_effective_velocity."""
    design = TurbofanDesignPoint(
        altitude=10668.0, mach=0.78, core_mass_flow=40.0, bypass_ratio=0.0,
        fan_pressure_ratio=1.6, booster_pressure_ratio=1.6, hpc_pressure_ratio=14.0,
        turbine_entry_temperature=1650.0,
    )
    cycle = solve_cycle(design)
    assert cycle.bypass_effective_velocity == 0.0
    assert cycle.propulsive_efficiency <= 1.0


# ── Ideal-cycle limiting case ────────────────────────────────────────────


def test_ideal_cycle_matches_the_brayton_formula_when_unchoked():
    """The flagship test: with every efficiency at 1, no losses, one gas
    throughout, and an OPR low enough the core nozzle fully expands to
    ambient (not choked), thermal efficiency has to match the textbook
    ideal Brayton formula almost exactly — the two share no code."""
    design = _ideal(hpc_pressure_ratio=2.0)
    cycle = solve_cycle(design)
    assert not cycle.stations.core_nozzle.choked
    formula = ideal_brayton_efficiency(design.overall_pressure_ratio, AIR)
    assert cycle.thermal_efficiency == pytest.approx(formula, rel=2e-3)


def test_choked_nozzle_thermal_efficiency_never_exceeds_the_ideal_formula():
    """Once the core nozzle chokes, a convergent-only nozzle cannot fully
    expand the flow — real, unavoidable pressure thrust is left
    "stranded" as unconverted kinetic energy, a genuine thermodynamic loss
    the simple formula doesn't include. Real thermal efficiency must
    therefore sit at or below the formula's value, never above it, at
    every OPR tested."""
    for opr_hpc in (3.0, 5.0, 8.0, 14.0):
        design = _ideal(hpc_pressure_ratio=opr_hpc)
        cycle = solve_cycle(design)
        formula = ideal_brayton_efficiency(design.overall_pressure_ratio, AIR)
        assert cycle.thermal_efficiency <= formula + 1e-9, opr_hpc


def test_choking_penalty_grows_with_pressure_ratio():
    """The gap between the ideal formula and the actual (still loss-free!)
    thermal efficiency should widen as OPR rises and the core nozzle
    becomes more severely underexpanded — a monotonic physical trend, not
    noise. This is what confirmed the gap is a real aerodynamic effect
    rather than a bug: it moves predictably with the thing that causes it."""
    gaps = []
    for opr_hpc in (3.0, 5.0, 8.0, 14.0):
        design = _ideal(hpc_pressure_ratio=opr_hpc)
        cycle = solve_cycle(design)
        formula = ideal_brayton_efficiency(design.overall_pressure_ratio, AIR)
        gaps.append(formula - cycle.thermal_efficiency)
    assert gaps == sorted(gaps)
    assert all(g >= 0 for g in gaps)


def test_realistic_reference_design_thermal_efficiency_is_below_ideal():
    """The reference design (real component losses, high OPR, a choked
    core nozzle) must sit further below the ideal formula than the
    loss-free choked case does — both loss mechanisms (component
    inefficiency and nozzle underexpansion) stack in the same direction.
    """
    cycle = solve_cycle(REFERENCE)
    formula = ideal_brayton_efficiency(REFERENCE.overall_pressure_ratio, AIR)
    assert cycle.thermal_efficiency < formula


# ── Internal consistency ────────────────────────────────────────────────


def test_hpt_delivers_exactly_the_power_the_hpc_demands():
    """Recompute HP-spool power from the resulting stations and check it
    matches what the HPC actually drew, divided by mechanical efficiency —
    the turbine-sizing identity every spool in this cycle depends on."""
    cycle = solve_cycle(REFERENCE)
    s = cycle.stations
    hpc_power = cycle.core_mass_flow * REFERENCE.cold_gas.cp * (s.hpc_exit.t - s.booster_exit.t)
    hpt_power_delivered = cycle.turbine_mass_flow * REFERENCE.hot_gas.cp * (s.combustor_exit.t - s.hpt_exit.t)
    assert hpt_power_delivered == pytest.approx(hpc_power / REFERENCE.mechanical_efficiency, rel=1e-6)


def test_lpt_delivers_exactly_the_power_the_fan_and_booster_demand():
    cycle = solve_cycle(REFERENCE)
    s = cycle.stations
    total_fan_mass_flow = cycle.core_mass_flow * (1.0 + REFERENCE.bypass_ratio)
    fan_power = total_fan_mass_flow * REFERENCE.cold_gas.cp * (s.fan_exit.t - s.fan_face.t)
    booster_power = cycle.core_mass_flow * REFERENCE.cold_gas.cp * (s.booster_exit.t - s.fan_exit.t)
    lpt_power_delivered = cycle.turbine_mass_flow * REFERENCE.hot_gas.cp * (s.hpt_exit.t - s.lpt_exit.t)
    assert lpt_power_delivered == pytest.approx(
        (fan_power + booster_power) / REFERENCE.mechanical_efficiency, rel=1e-6
    )


def test_overall_efficiency_equals_thermal_times_propulsive():
    cycle = solve_cycle(REFERENCE)
    assert cycle.overall_efficiency == pytest.approx(
        cycle.thermal_efficiency * cycle.propulsive_efficiency
    )


def test_station_temperature_rises_monotonically_through_compression():
    s = solve_cycle(REFERENCE).stations
    temps = [s.fan_face.t, s.fan_exit.t, s.booster_exit.t, s.hpc_exit.t]
    assert temps == sorted(temps)


def test_station_temperature_falls_monotonically_through_expansion():
    s = solve_cycle(REFERENCE).stations
    temps = [s.combustor_exit.t, s.hpt_exit.t, s.lpt_exit.t]
    assert temps == sorted(temps, reverse=True)


def test_higher_turbine_entry_temperature_gives_more_thrust():
    hot = solve_cycle(TurbofanDesignPoint(
        altitude=10668.0, mach=0.78, core_mass_flow=40.0, bypass_ratio=6.0,
        fan_pressure_ratio=1.6, booster_pressure_ratio=1.6, hpc_pressure_ratio=14.0,
        turbine_entry_temperature=1750.0,
    ))
    cool = solve_cycle(REFERENCE)
    assert hot.net_thrust > cool.net_thrust


def test_reference_design_produces_a_physically_plausible_cycle():
    """Not a precision check — a sanity floor. If any of these drift
    outside a wide plausible band, something upstream broke in a way the
    more targeted tests above might not have been aimed at."""
    cycle = solve_cycle(REFERENCE)
    assert cycle.net_thrust > 0
    assert 5.0 < cycle.tsfc_g_per_kns < 40.0
    assert 0.0 < cycle.thermal_efficiency < 1.0
    assert 0.0 < cycle.propulsive_efficiency <= 1.0
    assert 0.0 < cycle.fuel_air_ratio < 0.06


# ── Convergent-divergent core nozzle ────────────────────────────────────


def test_cd_nozzle_core_is_supersonic_on_the_reference_design():
    """The README documents the reference design's core nozzle sitting at
    6.95x the critical pressure ratio, significantly underexpanded — a C-D
    nozzle built for exactly this design point has to actually be
    supersonic at exit, or this whole feature would be solving a problem
    the reference design doesn't have."""
    cycle = solve_cycle_with_cd_nozzle(REFERENCE)
    assert cycle.stations.core_nozzle.supersonic


def test_cd_nozzle_matches_every_upstream_station_of_the_convergent_solve():
    """solve_cycle_with_cd_nozzle reuses solve_cycle rather than
    recomputing the whole station stack — this is the regression test that
    the reuse actually happened: everything up to the LPT exit has to be
    bit-for-bit identical, since the C-D nozzle only changes what happens
    downstream of it."""
    conv = solve_cycle(REFERENCE)
    cd = solve_cycle_with_cd_nozzle(REFERENCE)
    for name in ("fan_face", "fan_exit", "booster_exit", "hpc_exit",
                 "combustor_exit", "hpt_exit", "lpt_exit", "bypass_nozzle"):
        assert getattr(cd.stations, name) == getattr(conv.stations, name)


def test_cd_nozzle_increases_net_thrust_over_the_choked_convergent_nozzle():
    """The entire motivation, checked at the cycle level rather than just
    the component level: recovering pressure thrust a convergent-only
    nozzle has to leave stranded as extra jet velocity has to show up as
    more net thrust on the same reference design, not just a locally higher
    nozzle exit velocity."""
    conv = solve_cycle(REFERENCE)
    cd = solve_cycle_with_cd_nozzle(REFERENCE)
    assert conv.stations.core_nozzle.choked
    assert cd.net_thrust > conv.net_thrust


def test_cd_nozzle_improves_tsfc_over_the_choked_convergent_nozzle():
    """More net thrust from the same fuel burn — fuel-air ratio is set by
    the combustor upstream of the nozzle, so it's identical between the two
    cycles — has to mean a lower (better) TSFC, not just higher thrust at
    the same specific fuel consumption."""
    conv = solve_cycle(REFERENCE)
    cd = solve_cycle_with_cd_nozzle(REFERENCE)
    assert cd.fuel_air_ratio == pytest.approx(conv.fuel_air_ratio)
    assert cd.tsfc_g_per_kns < conv.tsfc_g_per_kns


def test_cd_nozzle_core_exit_pressure_equals_ambient():
    cycle = solve_cycle_with_cd_nozzle(REFERENCE)
    assert cycle.stations.core_nozzle.p == pytest.approx(cycle.ambient_pressure)
