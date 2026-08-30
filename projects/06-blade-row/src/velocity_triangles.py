"""Free-vortex velocity triangles for an axial compressor rotor row.

This is what makes a blade row a different geometry problem from a wing: a
wing's washout is a chosen shape parameter, but a rotor blade's spanwise twist
is not free to choose — it is set by the flow. Blade speed U = omega * r grows
from hub to tip, so a blade that did not twist with it would present the wrong
angle to the incoming flow everywhere except one radius.

Free-vortex design (r * Cw = const) is the classical way to choose the swirl
distribution: it is the one distribution that makes the specific work done on
the flow, Euler's dW = U * (Cw2 - Cw1), come out constant across the span. A
non-constant span-loading would need a radial pressure gradient the flow can't
supply without secondary motion — this is why free-vortex is the textbook
default, not an arbitrary pick.

A rotor is only half a stage. It adds swirl to do work on the flow, but that
swirl is kinetic energy the machine cannot use downstream of the rotor and a
duct or combustor cannot accept — something stationary has to take it back
out. StatorDesignPoint below is that row's velocity triangle: no blade speed,
because a stator does not move, so the flow angles it bridges are absolute
angles, not relative ones, and it turns the flow rather than doing work on it.

No OpenCASCADE dependency here. This module is pure arithmetic — it is what
decides each blade's twist, not what draws it — and it is tested without ever
starting the pyOCC environment.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RotorDesignPoint:
    """A free-vortex rotor design, specified at the mean radius.

    axial_velocity   Ca, m/s. Assumed constant with radius (a free-vortex
                     design's other defining assumption alongside r*Cw=const).
    omega            rotor angular speed, rad/s.
    mean_radius      r_m, m — where exit swirl below is specified.
    exit_swirl_mean  Cw2 at the mean radius, m/s. Inlet is axial (Cw1 = 0
                     everywhere): the simplest rotor case, no inlet guide
                     vanes turning the flow before it arrives.
    """

    axial_velocity: float
    omega: float
    mean_radius: float
    exit_swirl_mean: float

    def __post_init__(self) -> None:
        if self.axial_velocity <= 0:
            raise ValueError("axial_velocity must be positive")
        if self.mean_radius <= 0:
            raise ValueError("mean_radius must be positive")

    def blade_speed(self, r: float) -> float:
        """U(r) = omega * r."""
        return self.omega * r

    def exit_swirl(self, r: float) -> float:
        """Cw2(r) = Cw2_mean * r_mean / r — the free-vortex distribution.

        Angular momentum per unit mass, r*Cw, is what free-vortex holds
        constant, so this is just that constant divided back out by r.
        """
        return self.exit_swirl_mean * self.mean_radius / r

    def specific_work(self, r: float) -> float:
        """Euler work per unit mass, dW = U * (Cw2 - Cw1) = U * Cw2.

        The point of a free-vortex design: this comes out the same at every
        radius, not just at the mean. See test_velocity_triangles.py for the
        identity this implies — it is checked there, not assumed here.
        """
        return self.blade_speed(r) * self.exit_swirl(r)

    def relative_inlet_angle(self, r: float) -> float:
        """beta1(r), radians, from the axial direction.

        Inlet is axial in the absolute frame (Cw1 = 0), so in the blade's
        rotating frame the flow arrives at the blade speed itself, working
        against Ca.
        """
        return math.atan(self.blade_speed(r) / self.axial_velocity)

    def relative_exit_angle(self, r: float) -> float:
        """beta2(r), radians, from the axial direction."""
        return math.atan(
            (self.blade_speed(r) - self.exit_swirl(r)) / self.axial_velocity
        )

    def camber_angle(self, r: float) -> float:
        """Flow turning required of the blade at r, beta1(r) - beta2(r)."""
        return self.relative_inlet_angle(r) - self.relative_exit_angle(r)

    def stagger_angle(self, r: float) -> float:
        """Blade stagger (setting) angle at r, by the tangent-mean rule.

        gamma = atan(0.5 * (tan(beta1) + tan(beta2))) is the standard
        preliminary-design estimate for where a circular-arc blade's chord
        line should sit between the two flow angles it has to bridge — not
        exact for a real cascade (that needs a deviation correlation, e.g.
        Carter's rule, which this project does not implement yet), but the
        right order-of-magnitude answer and the one used to place sections
        in blade.py.
        """
        return math.atan(
            0.5 * (math.tan(self.relative_inlet_angle(r))
                   + math.tan(self.relative_exit_angle(r)))
        )


@dataclass(frozen=True)
class StatorDesignPoint:
    """A free-vortex stator design, in the absolute frame.

    A stator sits downstream of a rotor and removes (some or all of) the
    swirl the rotor added — its inlet is the rotor's exit, so
    inlet_swirl_mean here is normally the same number as the upstream
    RotorDesignPoint.exit_swirl_mean. The two rows are one continuous flow,
    not two independent designs, and passing a different number is how that
    connection would silently break.

    axial_velocity   Ca, m/s, same constant-with-radius assumption as the
                     rotor.
    mean_radius      r_m, m.
    inlet_swirl_mean Cw at inlet, mean radius — the rotor's exit swirl.
    exit_swirl_mean  Cw at exit, mean radius. 0.0 (the default) removes all
                     swirl, the usual job of a stage's last stator; nonzero
                     leaves swirl for a following rotor to work with.
    """

    axial_velocity: float
    mean_radius: float
    inlet_swirl_mean: float
    exit_swirl_mean: float = 0.0

    def __post_init__(self) -> None:
        if self.axial_velocity <= 0:
            raise ValueError("axial_velocity must be positive")
        if self.mean_radius <= 0:
            raise ValueError("mean_radius must be positive")

    def inlet_swirl(self, r: float) -> float:
        """Free-vortex distribution, same law as the rotor's exit swirl."""
        return self.inlet_swirl_mean * self.mean_radius / r

    def exit_swirl(self, r: float) -> float:
        return self.exit_swirl_mean * self.mean_radius / r

    def inlet_angle(self, r: float) -> float:
        """alpha_in(r), radians, from the axial direction — an absolute
        angle: a stator does not move, so there is no relative frame to
        convert from, unlike the rotor's beta angles."""
        return math.atan(self.inlet_swirl(r) / self.axial_velocity)

    def exit_angle(self, r: float) -> float:
        return math.atan(self.exit_swirl(r) / self.axial_velocity)

    def swirl_removed(self, r: float) -> float:
        """r * (Cw_in - Cw_out) — the stator's equivalent of the rotor's
        specific_work identity. Both inlet and exit swirl are separately
        free-vortex (r*Cw = const each), so their difference times r is a
        constant too; see test_velocity_triangles.py for where this is
        checked rather than assumed."""
        return r * (self.inlet_swirl(r) - self.exit_swirl(r))

    def camber_angle(self, r: float) -> float:
        """Flow turning required of the blade at r, alpha_in(r) - alpha_out(r)."""
        return self.inlet_angle(r) - self.exit_angle(r)

    def stagger_angle(self, r: float) -> float:
        """Same tangent-mean rule as the rotor's stagger_angle — see that
        method's docstring for what it does and does not capture."""
        return math.atan(
            0.5 * (math.tan(self.inlet_angle(r)) + math.tan(self.exit_angle(r)))
        )
