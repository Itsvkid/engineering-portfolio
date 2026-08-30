"""Freestream static conditions consistent with NASA TM 110300's stated
test conditions at M = 0.79.

The report characterises its test point by Mach number and Reynolds number
per foot (3.2e6-4.2e6 across the M=0.60-0.92 range tested) — standard
practice for a pressurised transonic wind tunnel, which does not correspond
to any single free-flight altitude. It does not state a static temperature
or pressure directly.

This module backs out a static pressure that reproduces the report's stated
Reynolds number per foot at M=0.79, GIVEN a chosen static temperature
(288.15 K, ISA sea-level) — the temperature is a modelling choice (a
reasonable one for a temperature-controlled transonic tunnel, not something
the report states), the pressure is then solved for, not chosen, to match
the one number the report actually gives. This is the same "chosen input,
solved output, both documented as such" pattern the rest of this portfolio
uses for design parameters no source publishes (e.g. project 03's mach_dd).
"""

from __future__ import annotations

import math

from scipy.optimize import brentq

GAMMA_AIR = 1.4
R_AIR = 287.05287  # J/(kg*K), matching project 08's atmosphere.py constant
FOOT_TO_M = 0.3048

# Sutherland's law constants for air (standard values).
MU0 = 1.716e-5  # Pa*s, reference viscosity at T0
T0_SUTHERLAND = 273.15  # K
S_SUTHERLAND = 110.4  # K

STATIC_TEMPERATURE_K = 288.15  # ISA sea-level — a chosen input, see module docstring


def dynamic_viscosity(temperature: float) -> float:
    """Sutherland's law, Pa*s."""
    return (MU0 * (temperature / T0_SUTHERLAND) ** 1.5
            * (T0_SUTHERLAND + S_SUTHERLAND) / (temperature + S_SUTHERLAND))


def reynolds_per_foot(pressure: float, temperature: float, mach: float) -> float:
    """Re per foot for a perfect gas at (pressure, temperature), moving at
    `mach` — the same quantity the report reports its test conditions in."""
    density = pressure / (R_AIR * temperature)
    sound_speed = math.sqrt(GAMMA_AIR * R_AIR * temperature)
    velocity = mach * sound_speed
    mu = dynamic_viscosity(temperature)
    return density * velocity / mu * FOOT_TO_M


def static_pressure_for_target_reynolds(
    target_reynolds_per_foot: float, mach: float,
    temperature: float = STATIC_TEMPERATURE_K,
) -> float:
    """The static pressure that reproduces `target_reynolds_per_foot` at
    `mach` and `temperature`, solved numerically (Re scales linearly with
    pressure at fixed T and M, so this converges immediately — brentq over
    a generous bracket rather than solving the linear relation directly,
    matching this portfolio's convention of using a numerical root-find
    for any relation not worth deriving a closed form for)."""
    def residual(p: float) -> float:
        return reynolds_per_foot(p, temperature, mach) - target_reynolds_per_foot

    return brentq(residual, 1000.0, 500000.0, xtol=1.0)


def freestream_state(mach: float, target_reynolds_per_foot: float,
                      temperature: float = STATIC_TEMPERATURE_K) -> dict:
    """Static pressure, temperature, density, sound speed and velocity for
    a freestream condition consistent with the given Mach and Reynolds
    number per foot — everything OpenFOAM's boundary conditions need."""
    pressure = static_pressure_for_target_reynolds(target_reynolds_per_foot, mach, temperature)
    density = pressure / (R_AIR * temperature)
    sound_speed = math.sqrt(GAMMA_AIR * R_AIR * temperature)
    velocity = mach * sound_speed
    return {
        "mach": mach,
        "pressure_pa": pressure,
        "temperature_k": temperature,
        "density_kg_m3": density,
        "sound_speed_m_s": sound_speed,
        "velocity_m_s": velocity,
        "reynolds_per_foot": reynolds_per_foot(pressure, temperature, mach),
    }


def main() -> None:
    from .reference_data import MACH, REYNOLDS_PER_FOOT_RANGE

    target = sum(REYNOLDS_PER_FOOT_RANGE) / 2.0
    state = freestream_state(MACH, target)
    print(f"{'target Re/ft':<24}{target:.3e}  (report range "
          f"{REYNOLDS_PER_FOOT_RANGE[0]:.1e}-{REYNOLDS_PER_FOOT_RANGE[1]:.1e})")
    print(f"{'Mach':<24}{state['mach']:.2f}")
    print(f"{'static temperature':<24}{state['temperature_k']:.2f} K  "
          f"(chosen — ISA sea-level, see module docstring)")
    print(f"{'static pressure':<24}{state['pressure_pa']:.1f} Pa  (solved)")
    print(f"{'density':<24}{state['density_kg_m3']:.5f} kg/m^3")
    print(f"{'sound speed':<24}{state['sound_speed_m_s']:.2f} m/s")
    print(f"{'velocity':<24}{state['velocity_m_s']:.2f} m/s")
    print(f"{'recovered Re/ft':<24}{state['reynolds_per_foot']:.4e}  "
          f"(should equal target, above)")


if __name__ == "__main__":
    main()
