"""Class-Shape Transformation (CST) curves — Kulfan & Bussoletti (2006).

CST is the standard way to parametrize an aerodynamic surface as a small set
of numbers rather than a point cloud: a "class function" fixes the general
family of shape (rounded nose, pointed tail, and so on), and a "shape
function" — a Bernstein-polynomial blend — is free to bend that class into
the specific curve wanted. Changing one weight reshapes the whole curve
smoothly; there is no control point to drag.

A standard airfoil CST curve pins both ends to zero (upper and lower surfaces
meet at the leading and trailing edges). A nacelle generatrix does not: the
highlight (inlet lip) and the fan-cowl trailing edge both sit at a real,
nonzero radius. CSTCurve below is the ordinary CST curve with a linear term
added to carry it between two arbitrary end values — the same fix used in
practice for CST-parametrized fuselage and nacelle profiles, not a
one-off invention for this project.

No OpenCASCADE dependency here — this module is the shape itself, not the
solid built from it, and is tested without ever starting pyOCC.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CSTCurve:
    """r(psi) = (1 - psi)*r0 + psi*r1 + C(psi) * S(psi; weights)

    psi          normalized station, 0 to 1 (leading to trailing).
    r0, r1       curve value at psi=0 and psi=1 — the highlight and
                 trailing-edge radii for a nacelle generatrix.
    weights      Bernstein coefficients A_0..A_n. Order n = len(weights)-1.
                 These are the actual design variables: shape is dialled in
                 by choosing weights, not by specifying where the peak ends
                 up — max_radius() in profile.py measures that back off the
                 result, the same relationship NACA4.max_thickness_station
                 has to the wing project's section.
    n1, n2       class-function exponents. 0.5/0.5 gives a class rounded at
                 both ends — the family an external nacelle cowl belongs to.
                 0.5/1.0 is the classic airfoil "round nose, sharp tail"
                 class; passed here for the same reason it works there.
    """

    r0: float
    r1: float
    weights: tuple[float, ...]
    n1: float = 0.5
    n2: float = 0.5

    def __post_init__(self) -> None:
        if len(self.weights) < 1:
            raise ValueError("need at least one weight")
        if self.n1 <= 0 or self.n2 <= 0:
            raise ValueError("n1 and n2 must be positive — the class "
                              "function must vanish at both ends")

    @property
    def order(self) -> int:
        return len(self.weights) - 1

    def class_value(self, psi: float) -> float:
        """C(psi) = psi^n1 * (1-psi)^n2. Exactly zero at psi=0 and psi=1
        for n1, n2 > 0 — which is what makes r(0)=r0 and r(1)=r1 exact
        below, not approximate."""
        if psi <= 0.0 or psi >= 1.0:
            return 0.0
        return psi**self.n1 * (1.0 - psi) ** self.n2

    def shape_value(self, psi: float) -> float:
        """S(psi) = sum_i A_i * B_i,n(psi), the Bernstein-basis blend of
        the weights. If every weight equals the same constant A, the
        Bernstein basis sums to 1 everywhere (a partition of unity) and
        this collapses to exactly A — checked in tests, not assumed."""
        n = self.order
        return sum(
            a * math.comb(n, i) * psi**i * (1.0 - psi) ** (n - i)
            for i, a in enumerate(self.weights)
        )

    def __call__(self, psi: float) -> float:
        baseline = (1.0 - psi) * self.r0 + psi * self.r1
        return baseline + self.class_value(psi) * self.shape_value(psi)
