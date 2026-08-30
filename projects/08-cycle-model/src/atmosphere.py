"""International Standard Atmosphere, troposphere and lower stratosphere.

Self-contained rather than imported from the flight-performance-calculator
project — this portfolio's projects each stay independently runnable, the
same choice project 06 and 07 made for their own export.py.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

T0 = 288.15       # sea-level temperature, K
P0 = 101325.0     # sea-level pressure, Pa
LAPSE = 0.0065    # tropospheric lapse rate, K/m
G0 = 9.80665      # m/s^2
R_AIR = 287.05287 # J/(kg*K)
TROPOPAUSE = 11000.0  # m
T_STRATOSPHERE = T0 - LAPSE * TROPOPAUSE  # 216.65 K, constant above 11 km
GAMMA_AIR = 1.4


@dataclass(frozen=True)
class AtmosphereState:
    temperature: float  # K
    pressure: float      # Pa

    @property
    def sound_speed(self) -> float:
        return math.sqrt(GAMMA_AIR * R_AIR * self.temperature)


def at(altitude: float) -> AtmosphereState:
    """Static temperature and pressure at `altitude`, m, ISO 2533."""
    if altitude < 0:
        raise ValueError("altitude must be non-negative")
    if altitude <= TROPOPAUSE:
        t = T0 - LAPSE * altitude
        p = P0 * (t / T0) ** (G0 / (LAPSE * R_AIR))
        return AtmosphereState(t, p)

    p_tropopause = P0 * (T_STRATOSPHERE / T0) ** (G0 / (LAPSE * R_AIR))
    p = p_tropopause * math.exp(-G0 * (altitude - TROPOPAUSE) / (R_AIR * T_STRATOSPHERE))
    return AtmosphereState(T_STRATOSPHERE, p)
