"""A deliberately simplified single-parameter throttle model.

This is NOT compressor-map-based off-design matching — real off-design
performance needs compressor and turbine characteristics (2D maps of
pressure ratio and mass flow against corrected speed) this project does not
have, and building or fabricating them is out of scope; see the project
README's Outstanding section for what a real off-design model needs beyond
this.

What this module does instead: a single throttle parameter, 1.0 at the
reference design point and falling toward idle, drives every compressor's
pressure ratio via the pressure-ratio-scales-with-speed-squared
approximation (Euler's turbomachinery work equation: specific work
w = U*deltaCw scales with the square of blade speed U at a fixed
velocity-triangle shape, the same physics project 06's free-vortex blade
design already leans on — and pressure rise follows work monotonically
through the compressor's efficiency), and scales turbine entry temperature
linearly, matching this project's own convention that TET is a chosen
design input rather than something solved for (see cycle.py's module
docstring).

Two things this simplification explicitly does NOT capture, on top of not
having real maps at all:

* Mass flow is held at its design value at every throttle setting. A real
  engine's mass flow falls at part throttle too — this is the same "held
  fixed, and that's a real limitation" choice
  notebooks/cycle_envelope_analysis.ipynb already documents for altitude;
  here it is throttle instead.
* Every component efficiency is held at its design value. A real
  compressor's efficiency varies across its map and is generally worse away
  from its design point — this model has no efficiency islands to draw
  that from.

throttle is one scalar standing in for both "how fast the spool is turning"
and "how much fuel is being burned." A real engine's spool speed and TET
are related but not the same throttle knob (a FADEC commands a target
speed; TET emerges from whatever fuel flow reaches it) — collapsing them
into one parameter is the single biggest simplification this module makes.
"""

from __future__ import annotations

from dataclasses import replace

from .cycle import TurbofanCycle, TurbofanDesignPoint, solve_cycle


def throttle_design_point(reference: TurbofanDesignPoint, throttle: float) -> TurbofanDesignPoint:
    """A part-throttle design point derived from `reference` — see the
    module docstring for exactly what this simplified approximation does
    and does not capture.

    throttle=1.0 returns `reference` itself, unmodified, not a
    floating-point round-trip through the scaling formula below — "full
    throttle is the reference design," not an approximation that happens
    to land close to it.

    How low throttle can go before the result stops being physically
    plausible depends on `reference.turbine_entry_temperature`, not on a
    number fixed here: turbine_entry_temperature scales linearly with
    throttle, and TurbofanDesignPoint's own validation already rejects
    anything implausibly low (see cycle.py's __post_init__) — that
    existing guard is reused rather than duplicated with a second,
    possibly-inconsistent bound in this module.
    """
    if not 0.0 < throttle <= 1.0:
        raise ValueError("throttle must be in (0, 1]")
    if throttle == 1.0:
        return reference

    def scaled_pressure_ratio(design_pressure_ratio: float) -> float:
        return 1.0 + (design_pressure_ratio - 1.0) * throttle ** 2

    return replace(
        reference,
        fan_pressure_ratio=scaled_pressure_ratio(reference.fan_pressure_ratio),
        booster_pressure_ratio=scaled_pressure_ratio(reference.booster_pressure_ratio),
        hpc_pressure_ratio=scaled_pressure_ratio(reference.hpc_pressure_ratio),
        turbine_entry_temperature=reference.turbine_entry_temperature * throttle,
    )


def solve_off_design(reference: TurbofanDesignPoint, throttle: float) -> TurbofanCycle:
    """Solve the cycle at a part-throttle design point derived from
    `reference` via throttle_design_point — see that function's docstring,
    and the module docstring, for exactly what this simplified off-design
    approximation does and does not capture."""
    return solve_cycle(throttle_design_point(reference, throttle))
