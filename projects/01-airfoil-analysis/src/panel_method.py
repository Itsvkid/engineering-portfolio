"""Hess-Smith panel method: constant-strength source panels (one unknown
strength per panel, satisfying flow tangency — the non-lifting thickness
effect) plus a single shared constant-strength vortex panel distribution
(one more unknown, satisfying the Kutta condition — circulation and lift).
The standard textbook formulation (Katz & Plotkin; Moran, *An Introduction
to Theoretical and Computational Aerodynamics*), inviscid and incompressible.

Panels are numbered trailing-edge -> leading edge (upper surface) -> trailing
edge (lower surface), matching Naca4.surface(). For that traversal direction
the outward normal is the tangent rotated -90 deg: (sin(phi), -cos(phi)).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _source_velocity(x: np.ndarray, y: np.ndarray, s_len: float) -> tuple[np.ndarray, np.ndarray]:
    """Velocity at (x, y), in a panel's own local frame, induced by that
    panel carrying unit-strength constant source density, panel spanning
    local x in [0, s_len]. Self-term (x, y) -> (s_len/2, 0) is undefined by
    the general formula (log of 0/0) and is overwritten by its known
    closed-form limit by the caller.
    """
    # Only the self-term (x, y) = (s_len/2, 0) makes r1_sq or r2_sq vanish,
    # for a well-formed panel geometry, and the caller overwrites that term
    # with its closed-form limit right after calling this — no need to
    # guard the log here for a case whose result is discarded anyway.
    r1_sq = x**2 + y**2
    r2_sq = (x - s_len) ** 2 + y**2
    with np.errstate(divide="ignore", invalid="ignore"):
        u = 1 / (4 * np.pi) * np.log(r1_sq / r2_sq)
    v = 1 / (2 * np.pi) * (np.arctan2(y, x - s_len) - np.arctan2(y, x))
    return u, v


def _vortex_velocity(x: np.ndarray, y: np.ndarray, s_len: float) -> tuple[np.ndarray, np.ndarray]:
    """Same panel, unit-strength constant vortex density. The vortex field
    is the source field rotated 90 deg — they are harmonic conjugates of
    the same fundamental (log r) solution — so u_vortex = v_source and
    v_vortex = -u_source."""
    u_s, v_s = _source_velocity(x, y, s_len)
    return v_s, -u_s


@dataclass
class PanelGeometry:
    xn: np.ndarray  # panel nodes, N+1 of them
    yn: np.ndarray
    xc: np.ndarray  # control points (panel midpoints), N of them
    yc: np.ndarray
    length: np.ndarray  # panel lengths, N
    phi: np.ndarray  # panel inclination, atan2(dy, dx), N
    n_panels: int

    @staticmethod
    def from_surface(x: np.ndarray, y: np.ndarray) -> "PanelGeometry":
        xc = 0.5 * (x[:-1] + x[1:])
        yc = 0.5 * (y[:-1] + y[1:])
        dx = np.diff(x)
        dy = np.diff(y)
        length = np.hypot(dx, dy)
        phi = np.arctan2(dy, dx)
        return PanelGeometry(x, y, xc, yc, length, phi, len(xc))

    @property
    def normal(self) -> np.ndarray:
        """Outward unit normals, (N, 2) — see module docstring for why the
        -90 deg rotation, not +90 deg, is the outward one for this panel
        traversal direction."""
        return np.stack([np.sin(self.phi), -np.cos(self.phi)], axis=1)

    @property
    def tangent(self) -> np.ndarray:
        return np.stack([np.cos(self.phi), np.sin(self.phi)], axis=1)


def _influence_matrices(geo: PanelGeometry) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Us, Vs, Uv, Vv[i, j]: global-frame (u, v) induced at control point i
    by a unit-strength source (Us, Vs) or vortex (Uv, Vv) panel j."""
    n = geo.n_panels
    Us = np.zeros((n, n))
    Vs = np.zeros((n, n))
    Uv = np.zeros((n, n))
    Vv = np.zeros((n, n))

    for j in range(n):
        cphi, sphi = np.cos(geo.phi[j]), np.sin(geo.phi[j])
        dx = geo.xc - geo.xn[j]
        dy = geo.yc - geo.yn[j]
        # Rotate control points into panel j's local frame (panel along
        # local +x from 0 to length[j]). The sign on y_loc is the one that
        # makes local +y coincide with the panel's own outward normal —
        # gotten backwards on the first pass (caught by the self-induced-
        # velocity test below coming out at exactly -0.5 everywhere instead
        # of the textbook +0.5: a uniform sign flip, not a per-panel bug).
        x_loc = dx * cphi + dy * sphi
        y_loc = dx * sphi - dy * cphi

        us_loc, vs_loc = _source_velocity(x_loc, y_loc, geo.length[j])
        uv_loc, vv_loc = _vortex_velocity(x_loc, y_loc, geo.length[j])

        # Self-term: control point j sits exactly on its own panel's
        # midpoint (x_loc = length/2, y_loc = 0), where the general formula
        # divides 0/0. Overwrite with the closed-form limit, verified in
        # tests against the well-known textbook results (source: 0 tangential
        # / +0.5 normal induced by itself; vortex: +0.5 tangential / 0 normal).
        us_loc[j], vs_loc[j] = 0.0, 0.5
        uv_loc[j], vv_loc[j] = 0.5, 0.0

        # Rotate back to global frame. The global->local transform above,
        # [[cphi, sphi], [sphi, -cphi]], flips one axis (it's a reflection,
        # to make local +y the outward normal — see the comment above), so
        # it is its own inverse: the same matrix converts local velocities
        # back to global, it isn't the usual +phi rotation.
        Us[:, j] = us_loc * cphi + vs_loc * sphi
        Vs[:, j] = us_loc * sphi - vs_loc * cphi
        Uv[:, j] = uv_loc * cphi + vv_loc * sphi
        Vv[:, j] = uv_loc * sphi - vv_loc * cphi

    return Us, Vs, Uv, Vv


@dataclass
class PanelSolution:
    geo: PanelGeometry
    alpha: float  # radians
    sigma: np.ndarray  # source strengths, N
    gamma: float  # single shared vortex strength
    v_tangential: np.ndarray  # surface tangential velocity / V_inf, N
    cp: np.ndarray  # pressure coefficient, N
    cl: float  # from Kutta-Joukowski circulation, not surface integration
    cl_surface: float  # from Cp integration, an independent cross-check


def solve(geo: PanelGeometry, alpha_rad: float, v_inf: float = 1.0) -> PanelSolution:
    n = geo.n_panels
    Us, Vs, Uv, Vv = _influence_matrices(geo)
    normal = geo.normal
    tangent = geo.tangent

    freestream = v_inf * np.array([np.cos(alpha_rad), np.sin(alpha_rad)])
    freestream_normal = normal @ freestream
    freestream_tangential = tangent @ freestream

    # Normal-velocity (tangency) equations, one per panel.
    A = np.zeros((n + 1, n + 1))
    b = np.zeros(n + 1)
    A[:n, :n] = Us * normal[:, [0]] + Vs * normal[:, [1]]
    A[:n, n] = (Uv * normal[:, [0]] + Vv * normal[:, [1]]).sum(axis=1)
    b[:n] = -freestream_normal

    # Kutta condition: tangential speed at the two trailing-edge panels
    # (index 0 and N-1) sums to zero — the standard Hess-Smith form.
    Bt = Us * tangent[:, [0]] + Vs * tangent[:, [1]]
    Ct_per_panel = Uv * tangent[:, [0]] + Vv * tangent[:, [1]]
    Ct = Ct_per_panel.sum(axis=1)
    A[n, :n] = Bt[0, :] + Bt[n - 1, :]
    A[n, n] = Ct[0] + Ct[n - 1]
    b[n] = -(freestream_tangential[0] + freestream_tangential[n - 1])

    x = np.linalg.solve(A, b)
    sigma = x[:n]
    gamma = x[n]

    v_t = freestream_tangential + Bt @ sigma + Ct * gamma
    v_over_vinf = v_t / v_inf
    cp = 1 - v_over_vinf**2

    # Kutta-Joukowski: total circulation is the shared vortex strength times
    # the total wetted perimeter it's distributed over. The minus sign is
    # this solver's circulation-sign convention, not a universal constant —
    # caught by checking against unambiguous physics (positive alpha on a
    # symmetric section must give positive Cl) rather than by re-deriving
    # the panel-velocity rotation by hand a second time: cl_surface below,
    # an independent route via direct Cp integration, already had the
    # correct sign, so this is the term that needed flipping to match it.
    circulation = gamma * geo.length.sum()
    cl = -2 * circulation / v_inf

    # Independent check: integrate -Cp * (normal . y-hat) * ds around the
    # surface directly, then resolve lift from the resulting force
    # coefficients — should agree with the Kutta-Joukowski value above if
    # the solve is self-consistent.
    force = -(cp[:, None] * geo.length[:, None] * normal).sum(axis=0)
    cl_surface = force[1] * np.cos(alpha_rad) - force[0] * np.sin(alpha_rad)

    return PanelSolution(geo, alpha_rad, sigma, gamma, v_over_vinf, cp, cl, cl_surface)
