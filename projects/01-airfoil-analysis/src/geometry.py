"""NACA 4-digit airfoil geometry: camberline, thickness, surface coordinates,
and the closed-form thin-airfoil-theory predictions the panel method is
checked against — the same species of check project 08 runs against the
ideal Brayton formula: an independent route to the same answer.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Naca4:
    """A NACA 4-digit section, e.g. "0012" -> Naca4(m=0.0, p=0.0, t=0.12)."""

    m: float  # max camber, fraction of chord (first digit / 100)
    p: float  # location of max camber, fraction of chord (second digit / 10)
    t: float  # max thickness, fraction of chord (last two digits / 100)
    name: str

    @staticmethod
    def parse(code: str) -> "Naca4":
        if len(code) != 4 or not code.isdigit():
            raise ValueError(f"expected a 4-digit NACA code, got {code!r}")
        m = int(code[0]) / 100.0
        p = int(code[1]) / 10.0
        t = int(code[2:]) / 100.0
        return Naca4(m=m, p=p, t=t, name=f"NACA {code}")

    def camber(self, x: np.ndarray) -> np.ndarray:
        """Camberline y_c(x), x in [0, 1]. Zero for a symmetric section."""
        if self.m == 0.0 or self.p == 0.0:
            return np.zeros_like(x)
        yc = np.where(
            x < self.p,
            self.m / self.p**2 * (2 * self.p * x - x**2),
            self.m / (1 - self.p) ** 2 * ((1 - 2 * self.p) + 2 * self.p * x - x**2),
        )
        return yc

    def camber_slope(self, x: np.ndarray) -> np.ndarray:
        """dy_c/dx, needed for both surface-normal placement and thin
        airfoil theory's zero-lift-angle integral."""
        if self.m == 0.0 or self.p == 0.0:
            return np.zeros_like(x)
        return np.where(
            x < self.p,
            2 * self.m / self.p**2 * (self.p - x),
            2 * self.m / (1 - self.p) ** 2 * (self.p - x),
        )

    def thickness(self, x: np.ndarray) -> np.ndarray:
        """Half-thickness y_t(x). Closed-trailing-edge coefficients (the
        -0.1036 variant, not the classic open-TE -0.1015): a panel method's
        Kutta condition wants panel 1 and panel N to actually meet, not
        leave a finite TE gap for the solver to paper over.
        """
        t = self.t
        return 5 * t * (
            0.2969 * np.sqrt(x)
            - 0.1260 * x
            - 0.3516 * x**2
            + 0.2843 * x**3
            - 0.1036 * x**4
        )

    def surface(self, n_per_side: int = 100) -> tuple[np.ndarray, np.ndarray]:
        """Panel-ready coordinates, cosine-spaced to cluster points at the
        leading and trailing edges (where curvature is highest), starting
        at the trailing edge, over the upper surface to the nose, and back
        along the lower surface to the trailing edge — the loop direction a
        panel method's control points and outward normals assume.
        """
        beta = np.linspace(0, np.pi, n_per_side)
        x = (1 - np.cos(beta)) / 2  # 0 -> 1, dense near both ends

        yc = self.camber(x)
        dyc = self.camber_slope(x)
        yt = self.thickness(x)
        theta = np.arctan(dyc)

        xu = x - yt * np.sin(theta)
        yu = yc + yt * np.cos(theta)
        xl = x + yt * np.sin(theta)
        yl = yc - yt * np.cos(theta)

        # Upper surface trailing edge -> leading edge, then lower surface
        # leading edge -> trailing edge. Drop the duplicated leading-edge
        # point where the two halves meet.
        xs = np.concatenate([xu[::-1], xl[1:]])
        ys = np.concatenate([yu[::-1], yl[1:]])
        return xs, ys

    def thin_airfoil_zero_lift_angle(self) -> float:
        """alpha_L0 = -(1/pi) * integral_0^pi (dyc/dx)(cos(theta0) - 1) dtheta0,
        with x0 = (1 - cos theta0)/2 — the standard closed-form thin airfoil
        theory result (e.g. Anderson, *Fundamentals of Aerodynamics*).
        Exactly zero for a symmetric section by construction, since dyc/dx
        is identically zero — that symmetry is itself the first check on
        this formula, not just on the panel method.
        """
        theta0 = np.linspace(1e-6, np.pi - 1e-6, 2000)
        x0 = (1 - np.cos(theta0)) / 2
        dyc = self.camber_slope(x0)
        integrand = dyc * (np.cos(theta0) - 1)
        return -np.trapezoid(integrand, theta0) / np.pi

    def thin_airfoil_lift_slope(self) -> float:
        """dCl/dalpha = 2*pi per radian — exact in thin airfoil theory,
        independent of camber. Kept as a named method (rather than a bare
        2*np.pi at the call site) so every place that uses it says why."""
        return 2 * np.pi
