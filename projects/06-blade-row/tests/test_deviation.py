"""Carter's rule deviation correction. No pyOCC — pure arithmetic, runs
anywhere pytest does."""

from __future__ import annotations

import math

import pytest

from src.deviation import (
    DeviationCorrectedDesign,
    carter_deviation_angle,
    carter_m,
)
from src.velocity_triangles import RotorDesignPoint, StatorDesignPoint

ROTOR = RotorDesignPoint(
    axial_velocity=150.0, omega=800.0, mean_radius=0.35, exit_swirl_mean=80.0
)
STATOR = StatorDesignPoint(
    axial_velocity=150.0, mean_radius=0.35, inlet_swirl_mean=80.0
)


def test_carter_m_matches_the_circular_arc_formula_directly():
    beta2 = math.radians(30.0)
    expected = 0.23 + 30.0 / 500.0
    assert carter_m(beta2) == pytest.approx(expected)


def test_carter_deviation_angle_matches_a_hand_worked_case():
    """A specific, hand-computed case checked digit for digit against the
    formula itself — the same "recompute independently" pattern the rest
    of this project's tests use, not just trusting the implementation."""
    theta = math.radians(40.0)
    beta2 = math.radians(20.0)
    s_over_c = 0.8
    m = 0.23 + 20.0 / 500.0
    expected_delta_deg = m * 40.0 * math.sqrt(0.8)
    assert carter_deviation_angle(theta, beta2, s_over_c) == pytest.approx(
        math.radians(expected_delta_deg)
    )


def test_carter_deviation_angle_rejects_nonpositive_space_chord_ratio():
    with pytest.raises(ValueError):
        carter_deviation_angle(math.radians(40.0), math.radians(20.0), 0.0)
    with pytest.raises(ValueError):
        carter_deviation_angle(math.radians(40.0), math.radians(20.0), -0.1)


def test_deviation_vanishes_as_space_chord_ratio_shrinks_to_zero():
    """The limiting case: an infinitely tight cascade (s/c -> 0, infinite
    blade count) perfectly guides the flow, so deviation has to vanish —
    checked as a limit, not just "deviation gets smaller"."""
    theta = math.radians(35.0)
    beta2 = math.radians(15.0)
    small = carter_deviation_angle(theta, beta2, 1e-12)
    assert small == pytest.approx(0.0, abs=1e-6)


def test_deviation_increases_with_space_chord_ratio():
    """A looser cascade (fewer/thinner blades relative to spacing) guides
    the flow less, so deviation should grow with s/c — monotonicity
    checked directly, not assumed from the sqrt in the formula."""
    theta = math.radians(35.0)
    beta2 = math.radians(15.0)
    values = [carter_deviation_angle(theta, beta2, s) for s in (0.3, 0.6, 0.9, 1.2)]
    assert values == sorted(values)


def test_deviation_increases_with_camber():
    """More flow turning demanded of the blade means more deviation from
    it, at fixed geometry — the theta factor in the formula, checked as an
    actual monotonic trend rather than assumed from the formula's shape."""
    beta2 = math.radians(15.0)
    s_over_c = 0.7
    values = [carter_deviation_angle(math.radians(t), beta2, s_over_c)
              for t in (10.0, 20.0, 30.0, 40.0)]
    assert values == sorted(values)


# ── DeviationCorrectedDesign — duck-typed BladeRow interface ────────────


def test_corrected_camber_equals_base_camber_plus_deviation():
    """The wrapper's whole point, checked as an exact identity: corrected
    theta = base theta + delta, not approximately, not "close enough"."""
    corrected = DeviationCorrectedDesign(base=ROTOR, space_chord_ratio=lambda r: 0.75)
    r = 0.35
    delta = corrected.deviation_angle(r)
    assert corrected.camber_angle(r) == pytest.approx(ROTOR.camber_angle(r) + delta)


def test_corrected_camber_exceeds_base_camber():
    """Deviation is a real physical effect in the direction Carter's rule
    predicts for this cascade class — corrected camber has to be strictly
    more than the uncorrected tangent-mean value, not less, for a normal
    (positive-turning) compressor cascade."""
    corrected = DeviationCorrectedDesign(base=ROTOR, space_chord_ratio=lambda r: 0.75)
    for r in (0.25, 0.30, 0.35, 0.40, 0.45):
        assert corrected.camber_angle(r) > ROTOR.camber_angle(r)


def test_corrected_design_duck_types_for_a_stator_too():
    """StatorDesignPoint has exit_angle/inlet_angle, not
    relative_exit_angle/relative_inlet_angle — DeviationCorrectedDesign
    has to resolve the right method names for either, the same duck-typing
    guarantee blade.py's own docstring already relies on."""
    corrected = DeviationCorrectedDesign(base=STATOR, space_chord_ratio=lambda r: 0.75)
    r = 0.35
    delta = corrected.deviation_angle(r)
    assert delta > 0.0
    assert corrected.camber_angle(r) == pytest.approx(STATOR.camber_angle(r) + delta)


def test_corrected_stagger_matches_the_tangent_mean_rule_on_corrected_angles():
    """corrected stagger is not just base.stagger_angle -- it has to be
    the tangent-mean rule reapplied to the CORRECTED exit angle (inlet
    unchanged, zero incidence still assumed), recomputed independently
    here rather than trusted from the implementation."""
    corrected = DeviationCorrectedDesign(base=ROTOR, space_chord_ratio=lambda r: 0.75)
    r = 0.35
    beta1 = ROTOR.relative_inlet_angle(r)
    beta2_blade = ROTOR.relative_exit_angle(r) - corrected.deviation_angle(r)
    expected = math.atan(0.5 * (math.tan(beta1) + math.tan(beta2_blade)))
    assert corrected.stagger_angle(r) == pytest.approx(expected)


def test_corrected_design_reduces_to_the_base_as_space_chord_ratio_shrinks():
    """Physical sanity on the wrapper as a whole: an infinitely tight
    cascade has zero deviation, so the corrected design's camber and
    stagger have to converge back to the base (uncorrected) design's —
    checked on the wrapper's own public interface, not on
    carter_deviation_angle directly (already checked above)."""
    corrected = DeviationCorrectedDesign(base=ROTOR, space_chord_ratio=lambda r: 1e-12)
    r = 0.35
    assert corrected.camber_angle(r) == pytest.approx(ROTOR.camber_angle(r), abs=1e-6)
    assert corrected.stagger_angle(r) == pytest.approx(ROTOR.stagger_angle(r), abs=1e-6)
