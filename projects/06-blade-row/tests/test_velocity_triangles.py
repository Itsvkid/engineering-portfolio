"""Free-vortex velocity triangles.

No pyOCC import anywhere in this file — these run in any Python with pytest,
which is also why CI can run them without the conda environment.
"""

from __future__ import annotations

import math

import pytest

from src.velocity_triangles import RotorDesignPoint, StatorDesignPoint

DP = RotorDesignPoint(
    axial_velocity=150.0, omega=800.0, mean_radius=0.35, exit_swirl_mean=80.0
)
SP = StatorDesignPoint(
    axial_velocity=150.0, mean_radius=0.35, inlet_swirl_mean=80.0
)


def test_rejects_nonpositive_axial_velocity():
    with pytest.raises(ValueError):
        RotorDesignPoint(axial_velocity=0.0, omega=800.0, mean_radius=0.35,
                          exit_swirl_mean=80.0)


def test_rejects_nonpositive_mean_radius():
    with pytest.raises(ValueError):
        RotorDesignPoint(axial_velocity=150.0, omega=800.0, mean_radius=0.0,
                          exit_swirl_mean=80.0)


def test_blade_speed_is_omega_r():
    for r in (0.25, 0.35, 0.45):
        assert DP.blade_speed(r) == pytest.approx(800.0 * r)


def test_exit_swirl_at_mean_radius_is_the_design_value():
    assert DP.exit_swirl(DP.mean_radius) == pytest.approx(DP.exit_swirl_mean)


def test_free_vortex_conserves_angular_momentum():
    """r * Cw2(r) constant is the definition of free-vortex — not a
    downstream consequence, so this pins the distribution itself."""
    k = DP.mean_radius * DP.exit_swirl_mean
    for r in (0.20, 0.30, 0.35, 0.40, 0.50):
        assert r * DP.exit_swirl(r) == pytest.approx(k)


def test_specific_work_is_constant_across_the_span():
    """The headline identity: free-vortex design exists specifically to make
    dW = U*Cw2 independent of radius. If this varied with r, the "free
    vortex" label on the design would be wrong, not just this test."""
    w_mean = DP.specific_work(DP.mean_radius)
    for r in (0.20, 0.25, 0.30, 0.40, 0.50, 0.60):
        assert DP.specific_work(r) == pytest.approx(w_mean, rel=1e-9)


def test_specific_work_matches_hand_calculation():
    # dW = U_mean * Cw2_mean directly, independent of the r*Cw2(r) route
    # test_free_vortex_conserves_angular_momentum takes above.
    expected = DP.omega * DP.mean_radius * DP.exit_swirl_mean
    assert DP.specific_work(DP.mean_radius) == pytest.approx(expected)


def test_relative_inlet_angle_grows_with_radius():
    """beta1 = atan(U/Ca); U grows with r, so beta1 must too."""
    radii = [0.20, 0.30, 0.40, 0.50]
    angles = [DP.relative_inlet_angle(r) for r in radii]
    assert angles == sorted(angles)


def test_relative_inlet_angle_hand_calculation():
    r = 0.35
    expected = math.atan(DP.blade_speed(r) / DP.axial_velocity)
    assert DP.relative_inlet_angle(r) == pytest.approx(expected)


def test_camber_angle_shrinks_toward_the_tip():
    """More turning is needed near the hub, where blade speed is smaller
    relative to the swirl being imparted — see the module docstring."""
    radii = [0.20, 0.30, 0.40, 0.50]
    cambers = [DP.camber_angle(r) for r in radii]
    assert cambers == sorted(cambers, reverse=True)


def test_stagger_angle_is_between_the_two_flow_angles():
    """The tangent-mean rule places stagger between beta1 and beta2 by
    construction — a stagger angle outside that bracket would mean the rule
    was implemented wrong, not that the flow was unusual."""
    for r in (0.20, 0.30, 0.40, 0.50):
        b1, b2 = DP.relative_inlet_angle(r), DP.relative_exit_angle(r)
        lo, hi = sorted((b1, b2))
        assert lo <= DP.stagger_angle(r) <= hi


def test_zero_swirl_gives_zero_camber():
    """No exit swirl means beta1 == beta2 — the blade does not need to turn
    the flow at all, so camber must be exactly zero."""
    no_turning = RotorDesignPoint(
        axial_velocity=150.0, omega=800.0, mean_radius=0.35, exit_swirl_mean=0.0
    )
    for r in (0.25, 0.35, 0.45):
        assert no_turning.camber_angle(r) == pytest.approx(0.0, abs=1e-12)


# ── StatorDesignPoint ────────────────────────────────────────────────────


def test_stator_rejects_nonpositive_axial_velocity():
    with pytest.raises(ValueError):
        StatorDesignPoint(axial_velocity=0.0, mean_radius=0.35,
                           inlet_swirl_mean=80.0)


def test_stator_rejects_nonpositive_mean_radius():
    with pytest.raises(ValueError):
        StatorDesignPoint(axial_velocity=150.0, mean_radius=0.0,
                           inlet_swirl_mean=80.0)


def test_stator_inlet_swirl_conserves_angular_momentum():
    k = SP.mean_radius * SP.inlet_swirl_mean
    for r in (0.20, 0.30, 0.35, 0.40, 0.50):
        assert r * SP.inlet_swirl(r) == pytest.approx(k)


def test_stator_default_exit_swirl_is_zero_everywhere():
    """The default job of a stage's stator: remove all the swirl."""
    for r in (0.20, 0.30, 0.35, 0.40, 0.50):
        assert SP.exit_swirl(r) == pytest.approx(0.0, abs=1e-12)
        assert SP.exit_angle(r) == pytest.approx(0.0, abs=1e-12)


def test_stator_inlet_angle_matches_rotor_exit_angle():
    """The stator's inlet is the rotor's exit by definition of a stage — if
    inlet_swirl_mean is set to the rotor's exit_swirl_mean (as it should be),
    the two angles must agree at every radius, not just the mean."""
    for r in (0.20, 0.30, 0.35, 0.40, 0.50):
        assert SP.inlet_angle(r) == pytest.approx(
            math.atan(DP.exit_swirl(r) / DP.axial_velocity)
        )


def test_stator_swirl_removed_is_constant_across_the_span():
    """Both inlet and exit swirl are separately free-vortex, so their
    difference times r has to be constant too — the stator's analogue of
    the rotor's constant specific-work identity."""
    removed_mean = SP.swirl_removed(SP.mean_radius)
    for r in (0.20, 0.25, 0.30, 0.40, 0.50, 0.60):
        assert SP.swirl_removed(r) == pytest.approx(removed_mean, rel=1e-9)


def test_stator_camber_equals_inlet_angle_when_fully_deswirling():
    """With exit_angle == 0 everywhere (the default), camber = inlet_angle
    exactly — there's no second angle left to subtract."""
    for r in (0.20, 0.30, 0.40, 0.50):
        assert SP.camber_angle(r) == pytest.approx(SP.inlet_angle(r))


def test_stator_partial_deswirl_leaves_smaller_camber():
    full = StatorDesignPoint(axial_velocity=150.0, mean_radius=0.35,
                              inlet_swirl_mean=80.0, exit_swirl_mean=0.0)
    partial = StatorDesignPoint(axial_velocity=150.0, mean_radius=0.35,
                                 inlet_swirl_mean=80.0, exit_swirl_mean=40.0)
    for r in (0.25, 0.35, 0.45):
        assert partial.camber_angle(r) < full.camber_angle(r)


def test_stator_stagger_is_between_inlet_and_exit_angle():
    for r in (0.20, 0.30, 0.40, 0.50):
        lo, hi = sorted((SP.inlet_angle(r), SP.exit_angle(r)))
        assert lo <= SP.stagger_angle(r) <= hi
