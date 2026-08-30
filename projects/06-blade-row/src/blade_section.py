"""Circular-arc compressor blade sections.

A wing section (NACA4) is chosen for lift-to-drag; a compressor blade section
is chosen to turn the flow by a specified angle with minimum loss. The
circular-arc camberline is the classical first-pass answer: unlike a NACA
camberline, its shape is parameterised directly by the turning angle a
velocity triangle asks for (see velocity_triangles.py), which is exactly what
this project needs to hand it.

This is a stated simplification, not a full cascade design: real compressor
blades (NACA-65 series, C4/C7 British profiles) use a thickness distribution
matched to the camberline and a deviation correlation (Carter's rule) to
correct the geometric turning angle for what the flow actually achieves. This
module borrows only the camberline; the thickness envelope reuses the same
closed NACA4 distribution the wing project validated, because inventing a
second one would not make this section more correct, just differently
unvalidated.

Coordinates: unit chord along +x from the leading edge at the origin,
camber/thickness along z — the same convention the wing project's airfoil.py
uses, so a reviewer reading both does not have to relearn the axes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Thickness distribution, identical to the wing project's NACA4 — see that
# module's docstring for why the closed-trailing-edge coefficient is used.
_A = (0.2969, -0.1260, -0.3516, 0.2843)
_A4_CLOSED = -0.1036

_SMALL_ANGLE = 1e-9  # below this, treat the section as uncambered


@dataclass(frozen=True)
class CircularArcSection:
    """A circular-arc-camberline blade section.

    camber_angle_deg   total flow turning the camberline is built for, deg.
                        Positive turns the flow the way this project's rotor
                        needs (see velocity_triangles.camber_angle).
    thickness          t/c, fraction of chord.
    """

    camber_angle_deg: float
    thickness: float
    n_points: int = 120

    def __post_init__(self) -> None:
        if self.thickness <= 0:
            raise ValueError("thickness must be positive")

    @property
    def is_symmetric(self) -> bool:
        return abs(self.camber_angle_deg) < 1e-9

    def _radius(self) -> float:
        """R of the arc's circle, chord = 1: R = 0.5 / sin(theta/2)."""
        half = math.radians(self.camber_angle_deg) / 2.0
        return 0.5 / math.sin(half)

    def half_thickness(self, x: float) -> float:
        return 5.0 * self.thickness * (
            _A[0] * math.sqrt(x)
            + _A[1] * x
            + _A[2] * x**2
            + _A[3] * x**3
            + _A4_CLOSED * x**4
        )

    def camber(self, x: float) -> tuple[float, float]:
        """Camber line height and slope at x. Returns (yc, dyc/dx).

        The camberline is the arc of the circle through (0,0) and (1,0) whose
        half-chord subtends half the camber angle at the centre — the
        construction that makes the tangent turn by exactly camber_angle_deg
        from leading to trailing edge, which is the whole point of building
        it this way rather than fitting a generic curve.
        """
        if self.is_symmetric:
            return 0.0, 0.0
        r = self._radius()
        half = math.radians(self.camber_angle_deg) / 2.0
        yc_centre = -r * math.cos(half)
        dx = x - 0.5
        under_root = r * r - dx * dx
        # Guards float round-off at x = 0 and x = 1, where under_root should
        # be exactly (r*sin(half))**2 = 0.25 but can go fractionally negative.
        under_root = max(under_root, 0.0)
        yc = yc_centre + math.sqrt(under_root)
        slope = -dx / math.sqrt(under_root) if under_root > 0 else 0.0
        return yc, slope

    def surfaces(self, n: int | None = None) -> tuple[list, list]:
        """Upper and lower surface points, leading edge to trailing edge.

        Cosine spacing — see the wing project's airfoil.py for why: uniform
        spacing starves the leading edge of points precisely where curvature,
        and therefore visible faceting, is highest.
        """
        n = n or self.n_points
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
