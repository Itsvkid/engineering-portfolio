"""A nacelle meridian profile: a CSTCurve mapped onto a physical axial
length, with the properties checked against the solid it will become.

No OpenCASCADE dependency — everything here is closed-form or numerical
integration over the curve, independent of whatever the geometry kernel does
with it. That independence is the point: nacelle.py's measured_volume() is
checked against predicted_volume() here precisely because they share no
code, the same "independent route" pattern projects 04 and 06 use.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .cst import CSTCurve


@dataclass(frozen=True)
class NacelleProfile:
    """length    axial length, highlight to trailing edge, m.
    curve     the CSTCurve giving radius as a function of normalized
              station psi = x / length.
    n_points  stations used for integration and sampling.
    """

    length: float
    curve: CSTCurve
    n_points: int = 400

    def __post_init__(self) -> None:
        if self.length <= 0:
            raise ValueError("length must be positive")
        if self.n_points < 20:
            raise ValueError(f"n_points={self.n_points} is too coarse to "
                              f"integrate accurately")

    @property
    def highlight_radius(self) -> float:
        return self.curve.r0

    @property
    def trailing_radius(self) -> float:
        return self.curve.r1

    def radius_at(self, x: float) -> float:
        """r(x), x measured from the highlight, 0 to length."""
        return self.curve(x / self.length)

    def _stations(self, n: int | None = None) -> list[float]:
        n = n or self.n_points
        return [i * self.length / (n - 1) for i in range(n)]

    def meridian_points(self, n: int | None = None) -> list[tuple[float, float]]:
        """(x, r) pairs, highlight to trailing edge."""
        return [(x, self.radius_at(x)) for x in self._stations(n)]

    def max_radius(self) -> tuple[float, float]:
        """Where the profile is widest, and by how much — measured by
        scanning the sampled curve, not a direct input. Same relationship
        as NACA4.max_thickness_station in the wing project: the weights are
        the design variables, this is what they produce."""
        best_x, best_r = 0.0, 0.0
        for x, r in self.meridian_points():
            if r > best_r:
                best_x, best_r = x, r
        return best_x, best_r

    def predicted_volume(self) -> float:
        """V = pi * integral of r(x)^2 dx — the disk-integration volume of
        the solid of revolution, Simpson's rule. Independent of whatever
        BRepPrimAPI_MakeRevol does with the same curve in nacelle.py."""
        xs = self._stations()
        ys = [math.pi * r * r for _, r in self.meridian_points()]
        return _simpson(xs, ys)

    def predicted_lateral_area(self) -> float:
        """S = 2*pi * integral of r(x) * sqrt(1 + r'(x)^2) dx — the curved
        (non-cap) surface area of the solid of revolution. r'(x) by central
        difference on the same sampling; fine enough sampling makes the
        discretisation error negligible next to the tolerance the kernel
        comparison is checked against (see test_nacelle.py)."""
        xs = self._stations()
        rs = [r for _, r in self.meridian_points()]
        h = xs[1] - xs[0]
        integrand = []
        for i, (x, r) in enumerate(zip(xs, rs)):
            if i == 0:
                drdx = (rs[1] - rs[0]) / h
            elif i == len(xs) - 1:
                drdx = (rs[-1] - rs[-2]) / h
            else:
                drdx = (rs[i + 1] - rs[i - 1]) / (2 * h)
            integrand.append(2 * math.pi * r * math.sqrt(1 + drdx * drdx))
        return _simpson(xs, integrand)

    def predicted_total_surface_area(self) -> float:
        """Lateral area plus the two flat end caps — what a solid built by
        revolving the *closed* meridian profile (curve + axis) actually
        bounds, and so what nacelle.py's kernel-measured total should
        match."""
        lateral = self.predicted_lateral_area()
        caps = math.pi * self.highlight_radius**2 + math.pi * self.trailing_radius**2
        return lateral + caps


def internal_clearance_ok(external: NacelleProfile, internal: NacelleProfile,
                           margin: float = 0.0) -> bool:
    """True if `internal`'s radius stays strictly inside `external`'s (minus
    an optional minimum wall-thickness margin) at every sampled station —
    the geometric precondition for the two to bound a valid hollow shell
    without self-intersecting when revolved. Checked numerically rather than
    only at the two endpoints: a curve can satisfy r0_int < r0_ext and
    r1_int < r1_ext while still crossing the external curve somewhere in
    between, since each is an independent CST curve free to bulge on its
    own. The two profiles must share the same axial length for "at every
    station" to mean the same x on both curves.
    """
    if abs(external.length - internal.length) > 1e-9:
        raise ValueError("external and internal profiles must share the same length")
    n = max(external.n_points, internal.n_points)
    stations = [i * external.length / (n - 1) for i in range(n)]
    return all(internal.radius_at(x) + margin < external.radius_at(x) for x in stations)


def material_volume(external: NacelleProfile, internal: NacelleProfile) -> float:
    """Volume of solid material between two concentric axisymmetric
    profiles sharing an axis and axial domain — external swept volume minus
    internal swept volume. Independent of nacelle.py's kernel measurement of
    the same hollow solid, the same "independent route" pattern the rest of
    this project holds itself to. Callers are expected to have already
    checked `internal_clearance_ok` — this function does not, since it is
    pure arithmetic on two numbers that are individually always well-defined
    regardless of whether the shell they'd bound together is valid.
    """
    return external.predicted_volume() - internal.predicted_volume()


def material_surface_area(external: NacelleProfile, internal: NacelleProfile) -> float:
    """Total area of the material shell between two profiles: both
    surfaces' lateral (curved) area, plus the two annular end caps where
    they're joined by real material thickness — the trailing edge and the
    highlight/lip. Each cap is the area of a washer, pi*(R_outer^2 -
    R_inner^2), not the full disk NacelleProfile.predicted_total_surface_area
    uses for a solid (single-profile) nacelle, since a hollow shell's ends
    are rings, not discs.
    """
    lateral = external.predicted_lateral_area() + internal.predicted_lateral_area()
    te_cap = math.pi * (external.trailing_radius ** 2 - internal.trailing_radius ** 2)
    lip_cap = math.pi * (external.highlight_radius ** 2 - internal.highlight_radius ** 2)
    return lateral + te_cap + lip_cap


def _simpson(xs: list[float], ys: list[float]) -> float:
    """Composite Simpson's rule on a uniform grid.

    h is taken directly from the grid spacing (xs[1]-xs[0]), not from
    dividing the total span by the panel count used in the Simpson sum — an
    earlier version did that and silently used the wrong h whenever the
    panel count needed adjusting for parity, understating a plain cylinder's
    known volume by 0.25%. NacelleProfile.n_points needs an odd count for a
    pure Simpson pass; an even count falls back to one trapezoid panel at
    the end, which is exact for the same reason the rest of this function
    being exact on a cylinder matters: a cylinder's integrand is constant,
    and the trapezoid rule is exact on a constant too.
    """
    n = len(xs) - 1
    if n < 1:
        return 0.0
    h = xs[1] - xs[0]
    m = n if n % 2 == 0 else n - 1
    total = ys[0] + ys[m]
    for i in range(1, m):
        total += ys[i] * (4 if i % 2 else 2)
    result = total * h / 3.0
    if m < n:  # one leftover panel, trapezoid
        result += (ys[m] + ys[n]) * h / 2.0
    return result
