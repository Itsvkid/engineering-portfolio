"""NACA 4-digit airfoil section generation.

Coordinates follow the standard definition: chord along +x from the leading
edge at the origin, thickness along z, unit chord. Scaling and placement are
the wing's job, not this module's.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Thickness distribution coefficients. The last one closes the trailing edge:
# the original NACA report uses -0.1015, which leaves a finite gap at x=1 and
# an open wire that will not loft into a solid. -0.1036 closes it.
_A = (0.2969, -0.1260, -0.3516, 0.2843)
_A4_CLOSED = -0.1036
_A4_OPEN = -0.1015


@dataclass(frozen=True)
class NACA4:
    """A NACA 4-digit section, e.g. NACA4.from_code("2412").

    max_camber        m, as a fraction of chord
    camber_position   p, as a fraction of chord
    thickness         t, as a fraction of chord
    """

    max_camber: float
    camber_position: float
    thickness: float
    closed_trailing_edge: bool = True

    @classmethod
    def from_code(cls, code: str, closed_trailing_edge: bool = True) -> "NACA4":
        if len(code) != 4 or not code.isdigit():
            raise ValueError(f"expected four digits, got {code!r}")
        m = int(code[0]) / 100.0
        p = int(code[1]) / 10.0
        t = int(code[2:]) / 100.0
        if m > 0 and p == 0:
            raise ValueError(
                f"{code}: non-zero camber with camber position 0 is undefined"
            )
        return cls(m, p, t, closed_trailing_edge)

    @property
    def is_symmetric(self) -> bool:
        return self.max_camber == 0.0

    def half_thickness(self, x: float) -> float:
        """Thickness distribution yt(x), half the total at that station."""
        a4 = _A4_CLOSED if self.closed_trailing_edge else _A4_OPEN
        return 5.0 * self.thickness * (
            _A[0] * math.sqrt(x)
            + _A[1] * x
            + _A[2] * x**2
            + _A[3] * x**3
            + a4 * x**4
        )

    def camber(self, x: float) -> tuple[float, float]:
        """Camber line height and its slope at x. Returns (yc, dyc/dx)."""
        m, p = self.max_camber, self.camber_position
        if m == 0.0:
            return 0.0, 0.0
        if x < p:
            return (m / p**2) * (2 * p * x - x**2), (2 * m / p**2) * (p - x)
        return (
            (m / (1 - p) ** 2) * ((1 - 2 * p) + 2 * p * x - x**2),
            (2 * m / (1 - p) ** 2) * (p - x),
        )

    def surfaces(self, n: int = 120) -> tuple[list, list]:
        """Upper and lower surface points, each leading edge to trailing edge.

        Cosine spacing, so points bunch where curvature is highest. Uniform
        spacing puts too few points at the leading edge, and the resulting
        surface is visibly faceted exactly where a reviewer looks first.
        """
        if n < 20:
            raise ValueError(f"n={n} is too coarse to represent a section")

        upper, lower = [], []
        for i in range(n):
            beta = math.pi * i / (n - 1)
            x = 0.5 * (1.0 - math.cos(beta))
            yt = self.half_thickness(x)
            yc, dyc = self.camber(x)
            theta = math.atan(dyc)
            upper.append((x - yt * math.sin(theta), yc + yt * math.cos(theta)))
            lower.append((x + yt * math.sin(theta), yc - yt * math.cos(theta)))
        return upper, lower

    def max_thickness_station(self, n: int = 2001) -> tuple[float, float]:
        """Where the section is thickest, and by how much. Returns (x/c, t/c)."""
        best_x, best_t = 0.0, 0.0
        for i in range(n):
            x = i / (n - 1)
            t = 2.0 * self.half_thickness(x)
            if t > best_t:
                best_x, best_t = x, t
        return best_x, best_t
