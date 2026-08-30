"""A twin-spool, separate-exhaust turbofan cycle: freestream to both nozzle
exits, station by station.

Two spools, each a closed power balance: the LP turbine drives the fan and
booster and nothing else, the HP turbine drives the HP compressor and
nothing else. Every turbine's pressure ratio in this model is therefore an
output, not an input — it's whatever pressure drop produces the exact power
its compressor demands, solved via components.expand_for_work.

No pyOCC anywhere in this project. A cycle model is a thermodynamics
problem, not a geometry one — every test here runs in plain Python.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .atmosphere import at
from .components import (
    CDNozzleExit,
    NozzleExit,
    Station,
    cd_nozzle_exit,
    combust,
    compress,
    expand_for_work,
    nozzle_exit,
)
from .gas import AIR, COMBUSTION_GAS, GasProperties

TSFC_SI_TO_G_PER_KNS = 1.0e6  # kg/(N*s) -> g/(kN*s): the unit gas-turbine
                              # performance is conventionally reported in.


@dataclass(frozen=True)
class TurbofanDesignPoint:
    """Every input a twin-spool separate-exhaust turbofan cycle needs.

    Flight condition
        altitude            m
        mach                freestream Mach number

    Mass flow and bypass
        core_mass_flow      kg/s, through the core (compressors, turbines,
                             core nozzle)
        bypass_ratio        bypass mass flow / core mass flow

    Pressure ratios (each a compressor's own ratio, not cumulative)
        fan_pressure_ratio
        booster_pressure_ratio   the LPC, core stream only
        hpc_pressure_ratio

    Turbine entry temperature — the design input that fixes the cycle;
    fuel-air ratio is solved from it, not the other way round
        turbine_entry_temperature   K, station 4

    Efficiencies, pressure losses and gas properties all have defaults
    representative of a subsonic civil turbofan design point — not any one
    real engine. See the project README for why that distinction matters.
    """

    altitude: float
    mach: float
    core_mass_flow: float
    bypass_ratio: float
    fan_pressure_ratio: float
    booster_pressure_ratio: float
    hpc_pressure_ratio: float
    turbine_entry_temperature: float

    intake_pressure_recovery: float = 0.98
    fan_efficiency: float = 0.90
    booster_efficiency: float = 0.88
    hpc_efficiency: float = 0.87
    combustor_efficiency: float = 0.99
    hpt_efficiency: float = 0.90
    lpt_efficiency: float = 0.91
    mechanical_efficiency: float = 0.995
    core_nozzle_efficiency: float = 0.98
    bypass_nozzle_efficiency: float = 0.98

    combustor_pressure_loss: float = 0.04
    bypass_duct_pressure_loss: float = 0.01

    fuel_lhv: float = 43.0e6  # J/kg, kerosene

    cold_gas: GasProperties = field(default_factory=lambda: AIR)
    hot_gas: GasProperties = field(default_factory=lambda: COMBUSTION_GAS)

    def __post_init__(self) -> None:
        if self.altitude < 0:
            raise ValueError("altitude must be non-negative")
        if not 0 < self.mach < 1.2:
            raise ValueError("mach must be in (0, 1.2) — this is a subsonic-intake model")
        if self.core_mass_flow <= 0:
            raise ValueError("core_mass_flow must be positive")
        if self.bypass_ratio < 0:
            raise ValueError("bypass_ratio must be non-negative")
        for name in ("fan_pressure_ratio", "booster_pressure_ratio", "hpc_pressure_ratio"):
            if getattr(self, name) <= 1.0:
                raise ValueError(f"{name} must exceed 1")
        if self.turbine_entry_temperature <= 1000.0:
            raise ValueError("turbine_entry_temperature is implausibly low for a real cycle")

    @property
    def overall_pressure_ratio(self) -> float:
        return self.fan_pressure_ratio * self.booster_pressure_ratio * self.hpc_pressure_ratio


@dataclass(frozen=True)
class Stations:
    """Stagnation conditions at every named station, intake to turbine
    exit, plus both nozzle exits (static — that's what a nozzle produces).
    """

    fan_face: Station              # station 2
    fan_exit: Station               # station 21 / 13 — one fan, same T,p both streams
    bypass_nozzle_inlet: Station     # station 13, after duct pressure loss
    booster_exit: Station            # station 25
    hpc_exit: Station                 # station 3
    combustor_exit: Station           # station 4 — turbine entry temperature
    hpt_exit: Station                  # station 45
    lpt_exit: Station                   # station 5
    core_nozzle: NozzleExit | CDNozzleExit  # CDNozzleExit only via
                                             # solve_cycle_with_cd_nozzle
    bypass_nozzle: NozzleExit


@dataclass(frozen=True)
class TurbofanCycle:
    design: TurbofanDesignPoint
    stations: Stations
    fuel_air_ratio: float
    turbine_mass_flow: float
    ambient_pressure: float
    freestream_velocity: float

    @property
    def core_mass_flow(self) -> float:
        return self.design.core_mass_flow

    @property
    def bypass_mass_flow(self) -> float:
        return self.design.core_mass_flow * self.design.bypass_ratio

    @property
    def total_intake_mass_flow(self) -> float:
        return self.core_mass_flow + self.bypass_mass_flow

    @property
    def fuel_mass_flow(self) -> float:
        return self.core_mass_flow * self.fuel_air_ratio

    def _nozzle_area(self, nozzle: NozzleExit | CDNozzleExit, mass_flow: float,
                      gas: GasProperties) -> float:
        density = nozzle.p / (gas.r * nozzle.t)
        return mass_flow / (density * nozzle.velocity)

    @property
    def core_gross_thrust(self) -> float:
        """Momentum thrust plus, for a choked convergent nozzle, the extra
        pressure-thrust term for exit pressure above ambient. A CDNozzleExit
        has no `choked` attribute — getattr defaults it to False, which is
        exactly correct rather than a special case: an ideally-expanded C-D
        nozzle's exit pressure is ambient by construction, so the term this
        skips would evaluate to exactly zero anyway."""
        nz = self.stations.core_nozzle
        gross = self.turbine_mass_flow * nz.velocity
        if getattr(nz, "choked", False):
            area = self._nozzle_area(nz, self.turbine_mass_flow, self.design.hot_gas)
            gross += area * (nz.p - self.ambient_pressure)
        return gross

    @property
    def bypass_gross_thrust(self) -> float:
        nz = self.stations.bypass_nozzle
        gross = self.bypass_mass_flow * nz.velocity
        if nz.choked:
            area = self._nozzle_area(nz, self.bypass_mass_flow, self.design.cold_gas)
            gross += area * (nz.p - self.ambient_pressure)
        return gross

    @property
    def ram_drag(self) -> float:
        return self.total_intake_mass_flow * self.freestream_velocity

    @property
    def net_thrust(self) -> float:
        return self.core_gross_thrust + self.bypass_gross_thrust - self.ram_drag

    @property
    def tsfc(self) -> float:
        """kg fuel / (N thrust * s) — SI-consistent but conventionally
        reported as g/(kN*s); see tsfc_g_per_kns."""
        return self.fuel_mass_flow / self.net_thrust

    @property
    def tsfc_g_per_kns(self) -> float:
        return self.tsfc * TSFC_SI_TO_G_PER_KNS

    @property
    def jet_kinetic_power(self) -> float:
        """Rate of kinetic energy the engine adds to the flow relative to
        freestream — core jet + bypass jet, minus the intake's share. The
        fraction of fuel heat that becomes organised jet KE, before any of
        it becomes useful thrust power; the numerator of thermal
        efficiency.

        Uses gross-thrust-per-unit-mass-flow as each jet's velocity, not
        the raw nozzle exit velocity — a first version used the raw exit
        velocity and produced a propulsive efficiency above 1 on the
        reference design, an impossibility caught by exactly the kind of
        physical-bound check this project's tests run. The cause: a
        choked nozzle's exit pressure exceeds ambient, so its gross thrust
        (self.core_gross_thrust / bypass_gross_thrust) includes a pressure
        term the raw exit velocity's kinetic energy doesn't account for.
        Dividing gross thrust by mass flow folds that pressure term into an
        equivalent momentum-only velocity, keeping the kinetic-energy
        accounting consistent with the thrust the nozzle actually
        produces. The two coincide exactly when a nozzle is unchoked,
        where there is no pressure term to fold in.
        """
        core_ke = 0.5 * self.turbine_mass_flow * self.core_effective_velocity ** 2
        bypass_ke = 0.5 * self.bypass_mass_flow * self.bypass_effective_velocity ** 2
        intake_ke = 0.5 * self.total_intake_mass_flow * self.freestream_velocity ** 2
        return core_ke + bypass_ke - intake_ke

    @property
    def core_effective_velocity(self) -> float:
        return self.core_gross_thrust / self.turbine_mass_flow

    @property
    def bypass_effective_velocity(self) -> float:
        """0 for a pure turbojet (bypass_ratio=0) — there is no bypass
        stream to carry kinetic energy, and dividing zero gross thrust by
        zero mass flow would otherwise raise rather than answer "none"."""
        if self.bypass_mass_flow == 0.0:
            return 0.0
        return self.bypass_gross_thrust / self.bypass_mass_flow

    @property
    def fuel_heat_rate(self) -> float:
        return self.fuel_mass_flow * self.design.fuel_lhv

    @property
    def thermal_efficiency(self) -> float:
        return self.jet_kinetic_power / self.fuel_heat_rate

    @property
    def thrust_power(self) -> float:
        return self.net_thrust * self.freestream_velocity

    @property
    def propulsive_efficiency(self) -> float:
        return self.thrust_power / self.jet_kinetic_power

    @property
    def overall_efficiency(self) -> float:
        return self.thrust_power / self.fuel_heat_rate


def solve_cycle(design: TurbofanDesignPoint) -> TurbofanCycle:
    """Assemble every station from the design point, intake to both
    nozzles, solving each turbine's pressure ratio against the power its
    spool demands."""
    atm = at(design.altitude)
    v0 = design.mach * atm.sound_speed

    t0_stagnation = atm.temperature * (
        1.0 + 0.5 * (design.cold_gas.gamma - 1.0) * design.mach ** 2
    )
    # p0/p = (T0/T)^(1/exponent) — isentropic_temperature_ratio expects a
    # pressure ratio and returns a temperature ratio, the inverse of what's
    # needed here, so this relation is applied directly rather than through
    # that helper.
    p0_stagnation = atm.pressure * (t0_stagnation / atm.temperature) ** (
        1.0 / design.cold_gas.exponent
    )

    fan_face = Station(t=t0_stagnation, p=p0_stagnation * design.intake_pressure_recovery)

    fan_exit = compress(fan_face, design.fan_pressure_ratio, design.fan_efficiency,
                        design.cold_gas)
    bypass_nozzle_inlet = Station(
        t=fan_exit.t, p=fan_exit.p * (1.0 - design.bypass_duct_pressure_loss)
    )

    booster_exit = compress(fan_exit, design.booster_pressure_ratio,
                            design.booster_efficiency, design.cold_gas)
    hpc_exit = compress(booster_exit, design.hpc_pressure_ratio,
                        design.hpc_efficiency, design.cold_gas)

    combustor_exit, f = combust(
        hpc_exit, design.turbine_entry_temperature, design.fuel_lhv,
        design.combustor_efficiency, design.combustor_pressure_loss,
        design.cold_gas, design.hot_gas,
    )

    turbine_mass_flow = design.core_mass_flow * (1.0 + f)

    hpc_power = design.core_mass_flow * design.cold_gas.cp * (hpc_exit.t - booster_exit.t)
    hpt_work_required = (hpc_power / design.mechanical_efficiency) / turbine_mass_flow
    hpt_exit = expand_for_work(combustor_exit, hpt_work_required, design.hpt_efficiency,
                               design.hot_gas)

    total_fan_mass_flow = design.core_mass_flow * (1.0 + design.bypass_ratio)
    fan_power = total_fan_mass_flow * design.cold_gas.cp * (fan_exit.t - fan_face.t)
    booster_power = design.core_mass_flow * design.cold_gas.cp * (booster_exit.t - fan_exit.t)
    lpt_work_required = ((fan_power + booster_power) / design.mechanical_efficiency) / turbine_mass_flow
    lpt_exit = expand_for_work(hpt_exit, lpt_work_required, design.lpt_efficiency,
                               design.hot_gas)

    core_nozzle = nozzle_exit(lpt_exit, atm.pressure, design.core_nozzle_efficiency,
                              design.hot_gas)
    bypass_nozzle = nozzle_exit(bypass_nozzle_inlet, atm.pressure,
                                design.bypass_nozzle_efficiency, design.cold_gas)

    stations = Stations(
        fan_face=fan_face, fan_exit=fan_exit, bypass_nozzle_inlet=bypass_nozzle_inlet,
        booster_exit=booster_exit, hpc_exit=hpc_exit, combustor_exit=combustor_exit,
        hpt_exit=hpt_exit, lpt_exit=lpt_exit, core_nozzle=core_nozzle,
        bypass_nozzle=bypass_nozzle,
    )

    return TurbofanCycle(
        design=design, stations=stations, fuel_air_ratio=f,
        turbine_mass_flow=turbine_mass_flow, ambient_pressure=atm.pressure,
        freestream_velocity=v0,
    )


def solve_cycle_with_cd_nozzle(design: TurbofanDesignPoint) -> TurbofanCycle:
    """Same cycle as solve_cycle, but the core nozzle is an ideally-expanded
    convergent-divergent one rather than convergent-only — see
    components.cd_nozzle_exit.

    Reuses solve_cycle for every station up to and including the LPT exit,
    since a C-D nozzle only changes what happens to the flow after that;
    recomputing the whole station-by-station solve a second time here would
    risk the two silently diverging if one were ever edited and not the
    other. Only the bypass stream keeps its convergent nozzle — a civil
    turbofan's bypass pressure ratio is low enough it essentially never
    chokes, so there is nothing for a C-D bypass nozzle to recover.
    """
    cycle = solve_cycle(design)
    cd_core_nozzle = cd_nozzle_exit(
        cycle.stations.lpt_exit, cycle.ambient_pressure,
        design.core_nozzle_efficiency, design.hot_gas,
    )
    cd_stations = replace(cycle.stations, core_nozzle=cd_core_nozzle)
    return replace(cycle, stations=cd_stations)
