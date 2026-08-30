"""Ties the panel method (inviscid Cl, surface velocity) to the boundary-
layer module (viscous Cd, one side at a time) into an alpha-sweep polar for
one airfoil at a given Reynolds number.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .boundary_layer import develop
from .geometry import Naca4
from .panel_method import PanelGeometry, solve

AIR_KINEMATIC_VISCOSITY = 1.5e-5  # m^2/s, sea-level standard atmosphere


@dataclass
class PolarPoint:
    alpha_deg: float
    cl: float
    cd: float
    upper_separated: bool
    lower_separated: bool


def _split_at_stagnation(geo: PanelGeometry, v_tangential: np.ndarray):
    """The panel-method surface loop runs TE(upper) -> LE -> TE(lower) as
    one continuous traversal, but a boundary layer develops *outward* from
    the stagnation point in both directions. Splits the loop there and
    returns each side's arc length and edge-speed magnitude, in traversal
    order away from the stagnation point — what `develop()` expects.
    """
    i_stag = int(np.argmin(np.abs(v_tangential)))
    upper_idx = list(range(i_stag, -1, -1))
    lower_idx = list(range(i_stag, geo.n_panels))

    def arc_and_speed(idx):
        px, py = geo.xc[idx], geo.yc[idx]
        ds = np.hypot(np.diff(px), np.diff(py))
        arc = np.concatenate([[0.0], np.cumsum(ds)])
        speed = np.abs(v_tangential[idx])
        return arc, speed

    return arc_and_speed(upper_idx), arc_and_speed(lower_idx)


def polar_point(geo: PanelGeometry, alpha_deg: float, reynolds: float, chord: float = 1.0) -> PolarPoint:
    sol = solve(geo, alpha_rad=np.radians(alpha_deg), v_inf=1.0)
    v_inf_actual = reynolds * AIR_KINEMATIC_VISCOSITY / chord
    (up_arc, up_speed), (lo_arc, lo_speed) = _split_at_stagnation(geo, sol.v_tangential)

    up = develop(up_arc * chord, up_speed * v_inf_actual, AIR_KINEMATIC_VISCOSITY, u_ref=v_inf_actual)
    lo = develop(lo_arc * chord, lo_speed * v_inf_actual, AIR_KINEMATIC_VISCOSITY, u_ref=v_inf_actual)

    return PolarPoint(
        alpha_deg=alpha_deg,
        cl=sol.cl,
        cd=up.cd_side + lo.cd_side,
        upper_separated=up.separated_at is not None,
        lower_separated=lo.separated_at is not None,
    )


def sweep(code: str, alphas_deg, reynolds: float, n_per_side: int = 160) -> list[PolarPoint]:
    airfoil = Naca4.parse(code)
    x, y = airfoil.surface(n_per_side)
    geo = PanelGeometry.from_surface(x, y)
    return [polar_point(geo, a, reynolds) for a in alphas_deg]
