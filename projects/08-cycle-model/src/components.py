"""Component thermodynamics: compressors, turbines, the combustor, nozzles.

Every function takes stagnation conditions in and returns stagnation
conditions out — the working currency of a cycle model, since stagnation
temperature tracks work and heat addition directly through h0 = cp*T0.

Two genuinely different problems show up as "efficiency" here, not one:

* A compressor's pressure ratio is a design choice; efficiency tells you how
  much MORE temperature rise (work in) an imperfect machine needs to reach
  it — divide the ideal delta-T by efficiency.
* A turbine's shaft work is fixed by whatever it has to drive (a compressor
  on the same spool); efficiency tells you how much MORE pressure ratio an
  imperfect machine needs to deliver that work — the ideal delta-T needed
  is the required actual delta-T divided by efficiency again, but for the
  opposite physical reason.

Both conventions are used correctly below, and mixing them up is the
single easiest way to build a cycle model that runs without error and
produces a turbine larger or smaller than the engine it's bolted to.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .gas import GasProperties, isentropic_temperature_ratio


@dataclass(frozen=True)
class Station:
    t: float  # stagnation temperature, K
    p: float  # stagnation pressure, Pa


@dataclass(frozen=True)
class NozzleExit:
    t: float          # static temperature at the exit plane, K
    p: float          # static pressure at the exit plane, Pa
    velocity: float   # m/s
    choked: bool


@dataclass(frozen=True)
class CDNozzleExit:
    """Exit state of an ideally-expanded convergent-divergent nozzle: the
    diverging section is sized so the flow always expands all the way to
    ambient static pressure, whatever that takes — unlike NozzleExit's
    convergent-only `choked` case, `p` here is never left above ambient, so
    there is no separate pressure-thrust bookkeeping to do at the cycle
    level (see cycle.TurbofanCycle.core_gross_thrust).

    `mach` says whether the diverging section is doing anything: mach <= 1
    means the flow never needed to accelerate past a plain convergent
    throat and this is physically identical to nozzle_exit's unchoked case;
    mach > 1 means the diverging section is recovering, as extra jet
    velocity, pressure energy a convergent-only nozzle would have to leave
    stranded at the throat.
    """
    t: float          # static temperature at the exit plane, K
    p: float          # static pressure at the exit plane, Pa
    velocity: float   # m/s
    mach: float

    @property
    def supersonic(self) -> bool:
        return self.mach > 1.0


def compress(inlet: Station, pressure_ratio: float, efficiency: float,
             gas: GasProperties) -> Station:
    """A compressor or fan stage. See the module docstring for why the
    ideal delta-T is divided by efficiency, not multiplied."""
    if pressure_ratio <= 1.0:
        raise ValueError("pressure_ratio must exceed 1 for a compressor")
    if not 0 < efficiency <= 1.0:
        raise ValueError("efficiency must be in (0, 1]")
    ideal_ratio = isentropic_temperature_ratio(pressure_ratio, gas)
    delta_t_ideal = inlet.t * (ideal_ratio - 1.0)
    delta_t_actual = delta_t_ideal / efficiency
    return Station(t=inlet.t + delta_t_actual, p=inlet.p * pressure_ratio)


def expand_to_pressure(inlet: Station, exit_pressure: float, efficiency: float,
                        gas: GasProperties) -> Station:
    """Expand to a known exit pressure — the unchoked-nozzle problem, and
    the general turbine relation with pressure ratio as the given quantity
    rather than required work. Actual delta-T is efficiency times the ideal
    delta-T: an imperfect expansion recovers less of the available drop."""
    if exit_pressure >= inlet.p:
        raise ValueError("exit_pressure must be below inlet.p for an expansion")
    if not 0 < efficiency <= 1.0:
        raise ValueError("efficiency must be in (0, 1]")
    ideal_ratio = isentropic_temperature_ratio(exit_pressure / inlet.p, gas)
    delta_t_ideal = inlet.t * (1.0 - ideal_ratio)
    delta_t_actual = efficiency * delta_t_ideal
    return Station(t=inlet.t - delta_t_actual, p=exit_pressure)


def expand_for_work(inlet: Station, specific_work_required: float,
                     efficiency: float, gas: GasProperties) -> Station:
    """A turbine stage sized to deliver exactly `specific_work_required`
    (J/kg) — the work-matching problem every turbine in this cycle actually
    solves, since its pressure ratio is not a free choice, it's whatever
    drop produces the power the compressor on its shaft demands.

    Also reused, unmodified, for a choked nozzle's pressure: "what pressure
    ratio does a lossy expansion need to produce a known enthalpy drop" is
    the same question whether that enthalpy becomes shaft work or jet
    kinetic energy.
    """
    if not 0 < efficiency <= 1.0:
        raise ValueError("efficiency must be in (0, 1]")
    if specific_work_required <= 0:
        raise ValueError("specific_work_required must be positive")
    delta_t_actual = specific_work_required / gas.cp
    if delta_t_actual >= inlet.t:
        raise ValueError(
            "required turbine work exceeds available enthalpy at this "
            "inlet temperature — this design point cannot be matched"
        )
    delta_t_ideal = delta_t_actual / efficiency
    t_exit_ideal = inlet.t - delta_t_ideal
    pressure_ratio = (inlet.t / t_exit_ideal) ** (1.0 / gas.exponent)
    return Station(t=inlet.t - delta_t_actual, p=inlet.p / pressure_ratio)


def combust(inlet: Station, exit_temperature: float, lhv: float,
            efficiency: float, pressure_loss_fraction: float,
            cold_gas: GasProperties, hot_gas: GasProperties) -> tuple[Station, float]:
    """Heat addition to a specified exit (turbine entry) temperature —
    TET is the design input here, not an output. Returns the exit station
    and the fuel-air ratio f = mdot_fuel/mdot_air solving

        mdot_air*cp_cold*T_in + mdot_fuel*LHV*eta = (mdot_air+mdot_fuel)*cp_hot*T_exit

    Pressure drops by pressure_loss_fraction regardless of f — a real
    combustor's total-pressure loss is dominated by flame-stabilising
    geometry (swirlers, dilution holes), not by how much fuel is burned.
    """
    if exit_temperature <= inlet.t:
        raise ValueError("combustor exit temperature must exceed inlet temperature")
    if not 0 < efficiency <= 1.0:
        raise ValueError("efficiency must be in (0, 1]")
    if not 0 <= pressure_loss_fraction < 1:
        raise ValueError("pressure_loss_fraction must be in [0, 1)")
    numerator = hot_gas.cp * exit_temperature - cold_gas.cp * inlet.t
    denominator = efficiency * lhv - hot_gas.cp * exit_temperature
    if denominator <= 0:
        raise ValueError(
            "fuel LHV is too low relative to the requested TET — no finite "
            "fuel-air ratio balances this energy equation"
        )
    f = numerator / denominator
    exit_station = Station(t=exit_temperature, p=inlet.p * (1.0 - pressure_loss_fraction))
    return exit_station, f


def nozzle_exit(inlet: Station, ambient_pressure: float, efficiency: float,
                 gas: GasProperties) -> NozzleExit:
    """A convergent nozzle: expands to ambient pressure if it can, chokes
    (exit Mach 1) if the available pressure ratio exceeds the critical
    value for this gas.

    The choked exit temperature is exact regardless of loss — T0 is
    conserved in adiabatic flow even with friction, and M=1 pins static
    temperature to T0*2/(gamma+1) by definition. What efficiency changes in
    the choked case is the pressure needed to reach that fixed temperature
    drop, which is exactly the turbine work-matching problem again:
    expand_for_work with the (known, fixed) enthalpy drop as the required
    work.
    """
    if not 0 < efficiency <= 1.0:
        raise ValueError("efficiency must be in (0, 1]")
    critical_pressure_ratio = ((gas.gamma + 1.0) / 2.0) ** (1.0 / gas.exponent)
    available_pressure_ratio = inlet.p / ambient_pressure

    if available_pressure_ratio < critical_pressure_ratio:
        exit_station = expand_to_pressure(inlet, ambient_pressure, efficiency, gas)
        velocity = math.sqrt(2.0 * gas.cp * (inlet.t - exit_station.t))
        return NozzleExit(t=exit_station.t, p=exit_station.p, velocity=velocity,
                          choked=False)

    t_exit = inlet.t * 2.0 / (gas.gamma + 1.0)
    velocity = math.sqrt(gas.gamma * gas.r * t_exit)
    specific_work_required = gas.cp * (inlet.t - t_exit)
    matched = expand_for_work(inlet, specific_work_required, efficiency, gas)
    return NozzleExit(t=t_exit, p=matched.p, velocity=velocity, choked=True)


def cd_nozzle_exit(inlet: Station, ambient_pressure: float, efficiency: float,
                    gas: GasProperties) -> CDNozzleExit:
    """An ideally-expanded convergent-divergent nozzle: the diverging
    section is sized so the flow always expands isentropically all the way
    to ambient static pressure, choked or not.

    This is the same energy relation nozzle_exit's unchoked branch already
    uses — expand_to_pressure to get the exit temperature, then
    v = sqrt(2*cp*deltaT) from stagnation-enthalpy conservation — with the
    M=1 cap removed. That cap exists in nozzle_exit only because a
    convergent-only duct is physically stuck at it: the area keeps
    shrinking, so it cannot keep accelerating flow past the throat. A
    diverging section removes that constraint, and "ideally expanded" means
    it is sized to keep expanding the flow, supersonically if the pressure
    ratio calls for it, down to exactly ambient pressure.

    This models one specific design condition, not a fixed nozzle geometry
    — a real C-D nozzle sized for one pressure ratio over- or
    under-expands at any other. Off-design nozzle behaviour is not modelled
    here; see the project README's Outstanding section.
    """
    if not 0 < efficiency <= 1.0:
        raise ValueError("efficiency must be in (0, 1]")
    exit_station = expand_to_pressure(inlet, ambient_pressure, efficiency, gas)
    velocity = math.sqrt(2.0 * gas.cp * (inlet.t - exit_station.t))
    speed_of_sound = math.sqrt(gas.gamma * gas.r * exit_station.t)
    mach = velocity / speed_of_sound
    return CDNozzleExit(t=exit_station.t, p=exit_station.p, velocity=velocity, mach=mach)
