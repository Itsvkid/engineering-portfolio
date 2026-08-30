"""Component thermodynamics: compressors, turbines, combustor, nozzles.
No pyOCC — runs anywhere."""

from __future__ import annotations

import math

import pytest

from src.components import (
    Station,
    cd_nozzle_exit,
    combust,
    compress,
    expand_for_work,
    expand_to_pressure,
    nozzle_exit,
)
from src.gas import AIR, COMBUSTION_GAS, isentropic_area_mach_ratio

INLET = Station(t=300.0, p=100000.0)


def test_compress_rejects_pressure_ratio_at_or_below_one():
    with pytest.raises(ValueError):
        compress(INLET, 1.0, 0.9, AIR)


def test_compress_rejects_efficiency_out_of_range():
    with pytest.raises(ValueError):
        compress(INLET, 5.0, 0.0, AIR)
    with pytest.raises(ValueError):
        compress(INLET, 5.0, 1.5, AIR)


def test_compress_raises_pressure_by_exactly_the_given_ratio():
    out = compress(INLET, 4.0, 0.85, AIR)
    assert out.p == pytest.approx(INLET.p * 4.0)


def test_compress_with_perfect_efficiency_matches_isentropic_relation():
    out = compress(INLET, 4.0, 1.0, AIR)
    expected_t = INLET.t * 4.0 ** AIR.exponent
    assert out.t == pytest.approx(expected_t)


def test_lossy_compressor_needs_more_temperature_rise_than_ideal():
    """The module docstring's whole point: efficiency < 1 means MORE
    delta-T for the same pressure ratio, not less."""
    ideal = compress(INLET, 4.0, 1.0, AIR)
    lossy = compress(INLET, 4.0, 0.85, AIR)
    assert (lossy.t - INLET.t) > (ideal.t - INLET.t)


def test_expand_to_pressure_rejects_exit_pressure_above_inlet():
    with pytest.raises(ValueError):
        expand_to_pressure(INLET, INLET.p * 2, 0.9, AIR)


def test_expand_to_pressure_with_perfect_efficiency_matches_isentropic_relation():
    out = expand_to_pressure(INLET, INLET.p / 4.0, 1.0, AIR)
    expected_t = INLET.t * (0.25) ** AIR.exponent
    assert out.t == pytest.approx(expected_t)


def test_lossy_expansion_drops_less_temperature_than_ideal():
    """Turbine-direction efficiency: an imperfect expansion recovers less
    of the available drop, so actual delta-T < ideal delta-T."""
    ideal = expand_to_pressure(INLET, INLET.p / 4.0, 1.0, AIR)
    lossy = expand_to_pressure(INLET, INLET.p / 4.0, 0.88, AIR)
    assert (INLET.t - lossy.t) < (INLET.t - ideal.t)


def test_expand_for_work_delivers_exactly_the_requested_work():
    """The whole point of work-matching: recompute delivered work from the
    resulting delta-T and confirm it equals what was asked for — the
    turbine-sizing identity every spool balance in cycle.py depends on."""
    required = 150000.0  # J/kg
    out = expand_for_work(INLET, required, 0.90, AIR)
    delivered = AIR.cp * (INLET.t - out.t)
    assert delivered == pytest.approx(required)


def test_expand_for_work_needs_a_bigger_pressure_ratio_when_lossy():
    """A lossy turbine has to drop through more pressure to deliver the
    same work as a perfect one — the opposite-looking but consistent
    partner of the compressor test above."""
    required = 100000.0
    ideal = expand_for_work(INLET, required, 1.0, AIR)
    lossy = expand_for_work(INLET, required, 0.85, AIR)
    ideal_pr = INLET.p / ideal.p
    lossy_pr = INLET.p / lossy.p
    assert lossy_pr > ideal_pr


def test_expand_for_work_rejects_work_exceeding_available_enthalpy():
    with pytest.raises(ValueError):
        expand_for_work(INLET, AIR.cp * INLET.t * 2, 0.9, AIR)


def test_expand_for_work_and_compress_are_consistent_round_trip():
    """Compress INLET by a pressure ratio, then ask a perfect turbine to
    deliver exactly that compressor's work — it must produce exactly the
    inverse pressure ratio, since with no losses anywhere the two
    processes are thermodynamic mirrors of each other."""
    compressed = compress(INLET, 5.0, 1.0, AIR)
    work_in = AIR.cp * (compressed.t - INLET.t)
    recovered = expand_for_work(compressed, work_in, 1.0, AIR)
    assert recovered.t == pytest.approx(INLET.t)
    assert recovered.p == pytest.approx(INLET.p, rel=1e-6)


def test_combust_rejects_exit_temperature_at_or_below_inlet():
    with pytest.raises(ValueError):
        combust(INLET, INLET.t, 43e6, 0.99, 0.04, AIR, COMBUSTION_GAS)


def test_combust_pressure_drops_by_exactly_the_loss_fraction():
    exit_station, _ = combust(INLET, 1500.0, 43e6, 0.99, 0.04, AIR, COMBUSTION_GAS)
    assert exit_station.p == pytest.approx(INLET.p * 0.96)


def test_combust_fuel_air_ratio_satisfies_its_own_energy_balance():
    """Recompute both sides of the energy equation the fuel-air ratio was
    solved from, and check they actually balance — the same "solve then
    verify" pattern project 06's free-vortex work identity uses."""
    exit_station, f = combust(INLET, 1500.0, 43e6, 0.99, 0.04, AIR, COMBUSTION_GAS)
    lhs = AIR.cp * INLET.t + f * 43e6 * 0.99
    rhs = (1.0 + f) * COMBUSTION_GAS.cp * exit_station.t
    assert lhs == pytest.approx(rhs)


def test_combust_higher_exit_temperature_needs_more_fuel():
    _, f_low = combust(INLET, 1400.0, 43e6, 0.99, 0.04, AIR, COMBUSTION_GAS)
    _, f_high = combust(INLET, 1700.0, 43e6, 0.99, 0.04, AIR, COMBUSTION_GAS)
    assert f_high > f_low


def test_nozzle_unchoked_expands_exactly_to_ambient_pressure():
    inlet = Station(t=1200.0, p=150000.0)
    result = nozzle_exit(inlet, 120000.0, 0.98, COMBUSTION_GAS)  # PR=1.25, well under critical
    assert not result.choked
    assert result.p == pytest.approx(120000.0)


def test_nozzle_chokes_above_the_critical_pressure_ratio():
    inlet = Station(t=1200.0, p=150000.0)
    result = nozzle_exit(inlet, 50000.0, 0.98, COMBUSTION_GAS)  # PR=3.0, well over critical
    assert result.choked


def test_choked_exit_velocity_equals_local_speed_of_sound():
    """The definition of choked: exit Mach is exactly 1, so exit velocity
    is exactly the local speed of sound at the exit static temperature —
    checked against the closed form, not just asserted true by the code
    that computed it."""
    inlet = Station(t=1200.0, p=150000.0)
    result = nozzle_exit(inlet, 50000.0, 0.98, COMBUSTION_GAS)
    assert result.choked
    expected_v = math.sqrt(COMBUSTION_GAS.gamma * COMBUSTION_GAS.r * result.t)
    assert result.velocity == pytest.approx(expected_v)


def test_choked_exit_temperature_is_independent_of_nozzle_efficiency():
    """T0 is conserved in adiabatic flow even with friction, and M=1 pins
    static temperature to T0*2/(gamma+1) regardless of loss — see the
    module docstring. A perfect and a lossy nozzle choked on the same
    inlet must land on the same exit temperature."""
    inlet = Station(t=1200.0, p=150000.0)
    perfect = nozzle_exit(inlet, 50000.0, 1.0, COMBUSTION_GAS)
    lossy = nozzle_exit(inlet, 50000.0, 0.90, COMBUSTION_GAS)
    assert perfect.choked and lossy.choked
    assert perfect.t == pytest.approx(lossy.t)


def test_choked_exit_pressure_is_lower_for_a_lossier_nozzle():
    """A lossy nozzle needs a BIGGER pressure ratio to reach the same
    (fixed) temperature drop — entropy generation means friction "wastes"
    some of the pressure drop's potential without cooling the gas
    proportionally as much. A bigger pressure ratio for the same inlet
    pressure means a LOWER exit pressure, hence less pressure thrust from
    an imperfect choked nozzle, not more. (An earlier version of this test
    asserted the opposite from a plausible-sounding but wrong intuition —
    worth recording since the direction is easy to get backwards.)"""
    inlet = Station(t=1200.0, p=150000.0)
    perfect = nozzle_exit(inlet, 50000.0, 1.0, COMBUSTION_GAS)
    lossy = nozzle_exit(inlet, 50000.0, 0.90, COMBUSTION_GAS)
    assert lossy.p < perfect.p


def test_nozzle_rejects_efficiency_out_of_range():
    inlet = Station(t=1200.0, p=150000.0)
    with pytest.raises(ValueError):
        nozzle_exit(inlet, 100000.0, 0.0, COMBUSTION_GAS)


def test_cd_nozzle_matches_unchoked_nozzle_exit_when_pressure_ratio_is_low():
    """Below the critical pressure ratio, a convergent-divergent nozzle and
    a plain convergent one are solving the identical problem — full
    expansion to ambient, nothing supersonic involved — so they have to
    agree exactly, not just approximately."""
    inlet = Station(t=1200.0, p=150000.0)
    conv = nozzle_exit(inlet, 120000.0, 0.98, COMBUSTION_GAS)  # PR=1.25
    cd = cd_nozzle_exit(inlet, 120000.0, 0.98, COMBUSTION_GAS)
    assert not conv.choked
    assert cd.mach < 1.0
    assert cd.t == pytest.approx(conv.t)
    assert cd.p == pytest.approx(conv.p)
    assert cd.velocity == pytest.approx(conv.velocity)


def test_cd_nozzle_reaches_supersonic_exit_where_a_convergent_nozzle_would_choke():
    inlet = Station(t=1200.0, p=150000.0)
    result = cd_nozzle_exit(inlet, 50000.0, 0.98, COMBUSTION_GAS)  # PR=3.0
    assert result.supersonic
    assert result.mach > 1.0


def test_cd_nozzle_exit_pressure_is_always_ambient():
    """The entire point of "ideally expanded": unlike a choked convergent
    nozzle, there is never leftover pressure thrust stranded at the exit."""
    inlet = Station(t=1200.0, p=150000.0)
    result = cd_nozzle_exit(inlet, 50000.0, 0.98, COMBUSTION_GAS)
    assert result.p == pytest.approx(50000.0)


def test_cd_nozzle_recovers_more_exit_velocity_than_a_choked_convergent_nozzle():
    """The whole motivation for building this: a C-D nozzle keeps
    accelerating flow past the throat instead of stranding the remaining
    pressure drop as thrust a convergent-only duct can't fully use."""
    inlet = Station(t=1200.0, p=150000.0)
    conv = nozzle_exit(inlet, 50000.0, 0.98, COMBUSTION_GAS)
    cd = cd_nozzle_exit(inlet, 50000.0, 0.98, COMBUSTION_GAS)
    assert conv.choked
    assert cd.velocity > conv.velocity


def test_cd_nozzle_rejects_efficiency_out_of_range():
    inlet = Station(t=1200.0, p=150000.0)
    with pytest.raises(ValueError):
        cd_nozzle_exit(inlet, 100000.0, 0.0, COMBUSTION_GAS)


def test_cd_nozzle_area_ratio_matches_the_closed_form_area_mach_relation_at_zero_loss():
    """An independent cross-check, not a re-run of the same formula: mass-
    flow continuity between the (known, exactly sonic) throat and the
    computed exit gives one route to the exit/throat area ratio; the
    standard isentropic area-Mach relation, evaluated at the exit Mach
    number alone, gives a completely separate one. They only have to agree
    where the flow really is isentropic throughout — efficiency=1, no loss
    anywhere — the same reason the ideal-Brayton check in test_cycle.py is
    isolated to the loss-free limit rather than run against a lossy design
    point."""
    gas = COMBUSTION_GAS
    inlet = Station(t=1200.0, p=150000.0)
    ambient = 50000.0  # PR=3.0, comfortably supersonic at exit

    exit_state = cd_nozzle_exit(inlet, ambient, 1.0, gas)
    assert exit_state.mach > 1.0

    t_throat = inlet.t * 2.0 / (gas.gamma + 1.0)
    v_throat = math.sqrt(gas.gamma * gas.r * t_throat)
    specific_work_to_throat = gas.cp * (inlet.t - t_throat)
    throat = expand_for_work(inlet, specific_work_to_throat, 1.0, gas)
    rho_throat = throat.p / (gas.r * t_throat)

    rho_exit = exit_state.p / (gas.r * exit_state.t)

    area_ratio_from_continuity = (rho_throat * v_throat) / (rho_exit * exit_state.velocity)
    area_ratio_from_closed_form = isentropic_area_mach_ratio(exit_state.mach, gas)

    assert area_ratio_from_continuity == pytest.approx(area_ratio_from_closed_form, rel=1e-6)
