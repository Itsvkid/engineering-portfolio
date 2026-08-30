"""Meridional flowpath sizing: how much the annulus needs to narrow across
a stage to keep pace with the falling specific volume of the gas as it's
compressed, and where the converged hub/tip radii land.

Pure arithmetic — no pyOCC. See annulus.py/stage.py for where these radii
turn into an actual revolved hub/casing surface.
"""

from __future__ import annotations

import math


def annulus_area(hub_radius: float, tip_radius: float) -> float:
    """A = pi * (r_tip^2 - r_hub^2) — the flow area at one axial station."""
    return math.pi * (tip_radius**2 - hub_radius**2)


def converging_annulus_exit(hub_radius_in: float, tip_radius_in: float,
                             area_ratio: float) -> tuple[float, float]:
    """Hub/tip radius at the exit of a converging annulus, holding mean
    radius constant while the flow area shrinks by `area_ratio`
    (exit area / inlet area) — the standard preliminary-design convention,
    since it keeps blade speed at the mean radius the same row to row and
    so leaves a free-vortex design's own `mean_radius` untouched: only the
    span each row's blade covers needs to change, not the velocity
    triangle it's built from.

    `area_ratio` is a chosen input, not derived from a thermodynamic
    calculation of the actual density rise across the stage — picked to
    sit in a plausible single-stage subsonic range (0.85-0.95 is typical),
    the same "plausible range, not reverse-engineered" standard the rest
    of this project holds its numbers to. A full derivation from continuity
    and a real compression process would need a stage thermodynamic model
    this project does not have (that is project 08's territory, for a
    turbofan cycle rather than one isolated stage).
    """
    if not 0 < area_ratio <= 1:
        raise ValueError(
            "area_ratio must be in (0, 1] — an annulus that expands rather "
            "than converges is a different design problem this function "
            "does not model, and area_ratio <= 0 is not a physical area"
        )
    mean_radius = 0.5 * (hub_radius_in + tip_radius_in)
    area_out = area_ratio * annulus_area(hub_radius_in, tip_radius_in)
    span_out = area_out / (2 * math.pi * mean_radius)
    return mean_radius - span_out / 2, mean_radius + span_out / 2


def cone_frustum_volume(r1: float, r2: float, height: float) -> float:
    """V = (pi*h/3) * (r1^2 + r1*r2 + r2^2) — the closed-form volume of a
    conical frustum, used to check the cone-segment transition duct in
    annulus.py against an independent route rather than only trusting
    BRepCheck_Analyzer's validity flag. Collapses to a plain cylinder's
    pi*r^2*h when r1 == r2, which is itself a check on this formula.
    """
    return (math.pi * height / 3.0) * (r1**2 + r1 * r2 + r2**2)
