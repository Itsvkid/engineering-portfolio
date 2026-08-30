"""Carter's rule: the deviation a real cascade adds that the tangent-mean
stagger rule (velocity_triangles.py) does not.

The tangent-mean rule places a blade's stagger between the two flow angles
it has to bridge, and this project's blades have, until now, been cut to
turn the flow by exactly the geometric camber angle -- a real circular-arc
cascade does not do that. The flow "deviates": it leaves closer to the
blade's own inlet direction than the blade's exit metal angle would suggest,
by an amount Carter's rule estimates as

    delta = m * theta * sqrt(s/c)          (all angles in the same units)
    m = 0.23 * (2a/c)^2 + beta2/500         (beta2 in DEGREES specifically)

For a circular-arc camber line (a/c = 0.5, so 2a/c = 1 -- exactly the blade
family blade_section.CircularArcSection builds), m = 0.23 + beta2/500. This
is the standard textbook form (e.g. Dixon, "Fluid Mechanics and
Thermodynamics of Turbomachinery"; Cohen, Rogers & Saravanamuttoo, "Gas
Turbine Theory") for a circular-arc cascade, not a project-specific
invention.

Single-pass, not iterative: `beta2` and `theta` in the formula are strictly
the blade's own metal angles, which depend on delta, which depends on them
-- a fully rigorous solve would iterate. This module uses the *flow* exit
angle and the *uncorrected* tangent-mean camber (already computed by
velocity_triangles.py) as the input, which is the standard single-pass
approximation used in preliminary design (deviation is a second-order
correction on top of an already-approximate stagger rule, so iterating to
convergence buys little at this level of fidelity) -- not presented as
exact.

No OpenCASCADE dependency -- pure arithmetic, tested without pyOCC.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Protocol


def carter_m(blade_exit_angle: float) -> float:
    """m for a circular-arc blade (2a/c = 1): m = 0.23 + beta2/500, with
    beta2 taken in DEGREES per the standard form even though this
    function's own argument and every other angle in this module is in
    radians, matching the rest of this project's convention."""
    return 0.23 + math.degrees(blade_exit_angle) / 500.0


def carter_deviation_angle(camber_angle: float, exit_flow_angle: float,
                            space_chord_ratio: float) -> float:
    """delta = m * theta * sqrt(s/c), radians in and out.

    camber_angle       theta, radians -- the tangent-mean-rule camber
                        (velocity_triangles.py's camber_angle(r)).
    exit_flow_angle     beta2 (or alpha2 for a stator), radians -- the flow
                        angle the blade row's free-vortex design requires
                        at exit.
    space_chord_ratio   s/c = pitch/chord = 1/solidity — see
                        BladeRow.solidity_at.
    """
    if space_chord_ratio <= 0:
        raise ValueError("space_chord_ratio must be positive")
    m = carter_m(exit_flow_angle)
    theta_deg = math.degrees(camber_angle)
    delta_deg = m * theta_deg * math.sqrt(space_chord_ratio)
    return math.radians(delta_deg)


class _AnglesAtRadius(Protocol):
    """The exact interface BladeRow._section_wire calls on `design` --
    stagger_angle(r) and camber_angle(r). RotorDesignPoint and
    StatorDesignPoint both satisfy this by duck typing already (see
    blade.py's own docstring); DeviationCorrectedDesign below satisfies
    it too, which is what lets it stand in for either without any change
    to BladeRow or velocity_triangles.py.
    """

    def camber_angle(self, r: float) -> float: ...
    def stagger_angle(self, r: float) -> float: ...

    # Only one of these exists depending on whether `base` is a rotor or a
    # stator; DeviationCorrectedDesign below picks whichever is present at
    # construction time rather than requiring both.


@dataclass(frozen=True)
class DeviationCorrectedDesign:
    """Wraps a RotorDesignPoint or StatorDesignPoint, replacing its
    camber_angle/stagger_angle with Carter's-rule-corrected versions —
    duck-typing the exact interface BladeRow expects, so a BladeRow built
    with `design=DeviationCorrectedDesign(...)` gets deviation-corrected
    blade geometry with no change to blade.py or velocity_triangles.py at
    all. `base`'s own camber_angle/stagger_angle are untouched (frozen
    dataclasses, and this wrapper never mutates them) — the existing,
    already-validated blade rows in build.py keep using the base design
    directly and are unaffected by this class existing.

    space_chord_ratio    r -> s/c, typically
                         `lambda r: 1.0 / some_blade_row.solidity_at(r)` —
                         a plain callable rather than a BladeRow reference,
                         since solidity_at(r) does not itself depend on
                         `design` (it's pure chord/n_blades/radius
                         geometry), so the *same* blade geometry's solidity
                         can inform the correction that then produces a
                         *different* blade geometry's twist.
    """

    base: object
    space_chord_ratio: Callable[[float], float]

    def _exit_flow_angle(self, r: float) -> float:
        # RotorDesignPoint exposes relative_exit_angle; StatorDesignPoint
        # exposes exit_angle. Trying the rotor name first and falling back
        # keeps this wrapper working for either without importing either
        # class here (avoiding a needless coupling this module doesn't
        # otherwise have).
        if hasattr(self.base, "relative_exit_angle"):
            return self.base.relative_exit_angle(r)
        return self.base.exit_angle(r)

    def _inlet_flow_angle(self, r: float) -> float:
        if hasattr(self.base, "relative_inlet_angle"):
            return self.base.relative_inlet_angle(r)
        return self.base.inlet_angle(r)

    def deviation_angle(self, r: float) -> float:
        return carter_deviation_angle(
            self.base.camber_angle(r), self._exit_flow_angle(r),
            self.space_chord_ratio(r),
        )

    def camber_angle(self, r: float) -> float:
        """theta_blade = theta_flow + delta — the blade needs MORE camber
        than the flow-implied turning, to compensate for under-turning the
        real flow by delta. See the module docstring for the beta2_blade =
        beta2_flow - delta derivation this follows from."""
        return self.base.camber_angle(r) + self.deviation_angle(r)

    def stagger_angle(self, r: float) -> float:
        """Same tangent-mean rule as the base design, applied to the
        corrected inlet/exit metal angles (inlet unchanged — zero
        incidence is still assumed; exit reduced by delta) rather than
        re-deriving stagger from the uncorrected flow angles."""
        beta1 = self._inlet_flow_angle(r)
        beta2_blade = self._exit_flow_angle(r) - self.deviation_angle(r)
        return math.atan(0.5 * (math.tan(beta1) + math.tan(beta2_blade)))
