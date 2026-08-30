"""Viscous drag estimate built on top of the inviscid panel-method edge
velocity: Thwaites' method for the laminar momentum thickness, Michel's
criterion for transition, a flat-plate-equivalent correlation for the
turbulent run to the trailing edge, and the Squire-Young formula to turn
trailing-edge momentum thickness into a profile-drag coefficient.

This is a real but deliberately *approximate* method, and it's approximate
in a specific, documented way, not quietly: the turbulent segment reuses a
flat-plate skin-friction correlation (Schlichting) rather than a fully
pressure-gradient-coupled turbulent integral method (e.g. Head's method) —
adequate to see whether a symmetric and a cambered section separate their
drag differently and by roughly how much, not a claim of CFD-grade Cd. See
the project README for what that trade-off does and does not cover.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def thwaites_l(lam: np.ndarray) -> np.ndarray:
    """White's power-law fit to Thwaites' tabulated shear function,
    dimensionless wall shear S(lambda) = tau_w*theta/(mu*U):
    l(lambda) = (lambda + 0.09)^0.62. Zero, by construction, at exactly
    lambda = -0.09 — the widely-cited Thwaites separation value — which a
    first-pass quadratic fit (0.22 + 1.57*lambda - 1.8*lambda**2, a
    different, also-real approximation from the same literature) does not
    reproduce: its own root sits at lambda = -0.123, caught by a test that
    checked -0.09 and found -0.123 instead. Clipped at zero for
    lambda < -0.09 rather than raising a fractional power of a negative
    number — flow has separated there, and there is no attached-flow shear
    left for the formula to describe.
    """
    return np.where(lam > -0.09, np.maximum(lam + 0.09, 0.0) ** 0.62, 0.0)


@dataclass
class BoundaryLayerResult:
    x: np.ndarray  # arc length from stagnation, m (or chord fractions if c=1)
    u_edge: np.ndarray
    theta: np.ndarray
    lam: np.ndarray
    separated_at: float | None  # arc-length station, or None if it doesn't
    transitioned_at: float | None
    theta_te: float
    h_te: float
    cd_side: float  # Squire-Young profile-drag contribution from this side


def _thwaites_theta(x: np.ndarray, u_edge: np.ndarray, nu: float) -> np.ndarray:
    """Thwaites' momentum-integral solution, theta^2 = 0.45*nu/U^6 *
    integral(U^5 dx), starting from theta = 0 at the stagnation point
    (x[0]). `u_edge` must be > 0 throughout (true just downstream of a
    front stagnation point on an attached flow) — the analysis stops at
    separation regardless, well before U could reverse.
    """
    u5 = np.maximum(u_edge, 1e-9) ** 5
    integral = np.concatenate([[0.0], np.cumsum(0.5 * (u5[1:] + u5[:-1]) * np.diff(x))])
    theta_sq = 0.45 * nu / np.maximum(u_edge, 1e-9) ** 6 * integral
    return np.sqrt(np.maximum(theta_sq, 0.0))


def michel_transition_index(x: np.ndarray, u_edge: np.ndarray, theta: np.ndarray, nu: float) -> int | None:
    """Michel's criterion: transition where Re_theta exceeds
    1.174*(1 + 22400/Re_x)*Re_x**0.46 — an empirical correlation for
    natural transition location, standard in boundary-layer texts (e.g.
    Cebeci & Bradshaw) as a simple alternative to solving an amplification
    (e_^9) equation."""
    re_x = np.maximum(u_edge, 1e-9) * x / nu
    re_theta = u_edge * theta / nu
    re_theta_crit = 1.174 * (1 + 22400 / np.maximum(re_x, 1.0)) * re_x**0.46
    exceeded = np.where(re_theta > re_theta_crit)[0]
    return int(exceeded[0]) if exceeded.size else None


def _separation_index(lam: np.ndarray) -> int | None:
    below = np.where(thwaites_l(lam) <= 0)[0]
    return int(below[0]) if below.size else None


def develop(x: np.ndarray, u_edge: np.ndarray, nu: float, u_ref: float) -> BoundaryLayerResult:
    """Run Thwaites from the stagnation point, hand off to a flat-plate
    turbulent correlation at transition (Michel) or separation, whichever
    comes first, and report the trailing-edge state.

    `u_ref` is the actual freestream speed, not `u_edge[-1]` — an earlier
    version conflated the two, passing the local panel-method edge velocity
    at the last station in for both `u_te` *and* `u_ref` in the
    Squire-Young calls below. That erases the exact ratio (u_te/u_ref)
    Squire-Young exists to use: how much the pressure recovery near the
    trailing edge has already reduced the local edge speed below the true
    freestream, which is what lets a momentum thickness measured on the
    body get extrapolated into a *far-wake* drag coefficient at all.
    """
    theta = _thwaites_theta(x, u_edge, nu)
    dudx = np.gradient(u_edge, x)
    lam = theta**2 / nu * dudx

    sep_idx = _separation_index(lam)
    trans_idx = michel_transition_index(x, u_edge, theta, nu)

    # Whichever happens first (in arc length) ends the laminar run — a
    # separated laminar boundary layer doesn't stay laminar-attached long
    # enough for Michel's criterion to still apply past that point.
    candidates = [i for i in (sep_idx, trans_idx) if i is not None]
    cutoff = min(candidates) if candidates else len(x) - 1

    if sep_idx is not None and sep_idx == cutoff:
        # Separated (or the panel-method edge velocity implies it would):
        # momentum thickness at separation stands in for the trailing-edge
        # value — the flat-plate turbulent correlation below assumes an
        # attached boundary layer and isn't meaningful past separation.
        # Reported, not hidden: BoundaryLayerResult.separated_at flags it.
        theta_te = theta[cutoff]
        h_stagnation_free = 2.0  # nominal, laminar, at/near separation
        return BoundaryLayerResult(
            x, u_edge, theta, lam,
            separated_at=float(x[cutoff]),
            transitioned_at=(float(x[trans_idx]) if trans_idx is not None and trans_idx < cutoff else None),
            theta_te=theta_te, h_te=h_stagnation_free,
            cd_side=_squire_young(theta_te, h_stagnation_free, u_edge[cutoff], u_ref),
        )

    if trans_idx is None:
        # Never transitioned or separated within this run — fully laminar
        # to the trailing edge (only plausible at the low end of the Re
        # range this project covers; reported so it's visible, not silently
        # extrapolated as if it were the normal case).
        theta_te = theta[-1]
        h_te = 2.0 + 4.14 * (0.25 - lam[-1]) if lam[-1] < 0 else 2.61 - 3.75 * lam[-1]
        return BoundaryLayerResult(
            x, u_edge, theta, lam, separated_at=None, transitioned_at=None,
            theta_te=theta_te, h_te=float(h_te),
            cd_side=_squire_young(theta_te, float(h_te), u_edge[-1], u_ref),
        )

    # Turbulent from transition to the trailing edge, flat-plate
    # equivalent (Schlichting): momentum thickness grows via the
    # flat-plate momentum-integral identity d(theta)/dx = Cf/2, which
    # drops the pressure-gradient term the laminar Thwaites stage kept —
    # the documented simplification this module's docstring flags.
    theta_trans = theta[trans_idx]
    x_run = x[trans_idx:] - x[trans_idx]
    u_run = u_edge[trans_idx:]
    theta_turb = _grow_turbulent_theta(x_run, u_run, theta_trans, nu)
    theta_te = theta_turb[-1]
    h_te = 1.4  # typical flat-plate turbulent shape factor, attached flow
    return BoundaryLayerResult(
        x, u_edge, theta, lam, separated_at=None, transitioned_at=float(x[trans_idx]),
        theta_te=theta_te, h_te=h_te,
        cd_side=_squire_young(theta_te, h_te, u_edge[-1], u_ref),
    )


def _grow_turbulent_theta(x_run: np.ndarray, u_run: np.ndarray, theta0: float, nu: float) -> np.ndarray:
    """Integrate d(theta)/dx = Cf(Re_theta)/2 with the Schlichting flat-
    plate correlation Cf = 0.074 / Re_x^0.2 (Re_x measured from the start
    of this turbulent run, valid Re_x < 1e7), forward-Euler with the grid
    already given — the panel method's cosine spacing is already dense
    near the leading edge and coarser aft, which is the opposite of what
    this integration would ideally want, but the momentum thickness varies
    slowly enough over the aft, coarse-panel region that it doesn't matter
    at the tolerance this estimate is honest about."""
    theta = np.empty_like(x_run)
    theta[0] = theta0
    for i in range(1, len(x_run)):
        re_x = max(u_run[i - 1] * max(x_run[i - 1], 1e-6) / nu, 1.0)
        cf = 0.074 / re_x**0.2
        dx = x_run[i] - x_run[i - 1]
        theta[i] = theta[i - 1] + 0.5 * cf * dx
    return theta


def _squire_young(theta_te: float, h_te: float, u_te: float, u_ref: float) -> float:
    """Squire-Young formula: profile drag from one side's trailing-edge
    momentum thickness and shape factor, extrapolated to the freestream —
    the standard way a boundary-layer method reports a drag coefficient
    without integrating surface shear directly. `u_ref` is the freestream
    speed (chord = 1, so this returns a drag coefficient directly).
    """
    return 2 * theta_te * (u_te / u_ref) ** ((5 + h_te) / 2)
