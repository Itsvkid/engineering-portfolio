"""Perfect-gas thermodynamics for a gas turbine cycle.

Two different gases run through this engine, not one. Air enters the intake
at roughly 1005 J/(kg·K), gamma 1.4. By the time it leaves the combustor it
is air plus burned kerosene, at a different specific heat and gamma —
roughly 1244 J/(kg·K), 1.333 — because a diatomic-dominated gas has picked up
CO2 and H2O, which raises cp and lowers gamma. A cycle model that reuses air
properties across the combustor is quietly wrong by a percent or two on
every downstream number, which is small enough to hide and large enough to
matter.

No dependency on anything else in this project — this module is the physics
constants and the isentropic relations, not the engine built from them.
"""

from __future__ import annotations

from dataclasses import dataclass

R_UNIVERSAL = 8.314462618  # J/(mol*K), unused directly but documents where R comes from

AIR = None  # set below, after GasProperties is defined
COMBUSTION_GAS = None


@dataclass(frozen=True)
class GasProperties:
    """cp, J/(kg*K); gamma, dimensionless. R follows from the two: for a
    perfect gas, cp - cv = R and gamma = cp/cv, so R = cp*(1 - 1/gamma)."""

    cp: float
    gamma: float

    def __post_init__(self) -> None:
        if self.cp <= 0:
            raise ValueError("cp must be positive")
        if self.gamma <= 1.0:
            raise ValueError("gamma must be greater than 1")

    @property
    def r(self) -> float:
        return self.cp * (1.0 - 1.0 / self.gamma)

    @property
    def exponent(self) -> float:
        """(gamma-1)/gamma — the exponent every isentropic T-p relation
        uses. Named because it appears often enough to be worth not
        retyping the ratio each time."""
        return (self.gamma - 1.0) / self.gamma


AIR = GasProperties(cp=1005.0, gamma=1.4)
COMBUSTION_GAS = GasProperties(cp=1244.0, gamma=1.333)


def isentropic_temperature_ratio(pressure_ratio: float, gas: GasProperties) -> float:
    """T2/T1 for an isentropic process with pressure ratio p2/p1.

    Works in both directions: pressure_ratio > 1 (compression) raises T,
    pressure_ratio < 1 (expansion) lowers it — the same formula either way,
    which is the point of writing it once here rather than once per
    component.
    """
    return pressure_ratio ** gas.exponent


def isentropic_area_mach_ratio(mach: float, gas: GasProperties) -> float:
    """A/A* for isentropic flow of a perfect gas at Mach number `mach` — the
    standard compressible-flow area-Mach relation. A* is the area at which
    the flow is exactly sonic; this ratio is what a duct's cross-section
    has to do, at every station, for isentropic flow to actually reach
    `mach` there. It has a minimum of 1 at M=1 and rises on both sides —
    the reason a nozzle accelerating flow past Mach 1 has to diverge again
    rather than keep narrowing: a converging duct alone cannot supply the
    larger area a supersonic exit needs.

    Used in test_components.py as an independent check on cd_nozzle_exit:
    mass-flow continuity between the throat and the exit gives one route to
    the exit/throat area ratio, this closed form (evaluated at the exit
    Mach number alone) gives a second, and the two have to agree — but only
    at zero loss, where the flow really is isentropic throughout.
    """
    if mach <= 0:
        raise ValueError("mach must be positive")
    exponent = (gas.gamma + 1.0) / (2.0 * (gas.gamma - 1.0))
    bracket = (2.0 / (gas.gamma + 1.0)) * (1.0 + 0.5 * (gas.gamma - 1.0) * mach ** 2)
    return (1.0 / mach) * bracket ** exponent


def ideal_brayton_efficiency(overall_pressure_ratio: float,
                              gas: GasProperties = AIR) -> float:
    """Thermal efficiency of the ideal (loss-free, 100%-efficient) Brayton
    cycle, eta = 1 - 1/OPR^((gamma-1)/gamma).

    This is the textbook result this project's flagship test checks the
    full component-by-component cycle model against — a turbofan's ideal
    thermal efficiency depends only on overall pressure ratio, not bypass
    ratio, because how the fan/LPT work is split between core and bypass
    jets is a propulsive-efficiency question, not a thermal one. See
    test_cycle.py for where a real TurbofanCycle is checked against this,
    not just this formula checked against itself.
    """
    if overall_pressure_ratio <= 1.0:
        raise ValueError("overall_pressure_ratio must exceed 1")
    return 1.0 - 1.0 / isentropic_temperature_ratio(overall_pressure_ratio, gas)
