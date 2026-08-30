"""CST curves. No pyOCC import — runs anywhere."""

from __future__ import annotations

import pytest

from src.cst import CSTCurve


def test_rejects_empty_weights():
    with pytest.raises(ValueError):
        CSTCurve(r0=1.0, r1=0.5, weights=())


def test_rejects_nonpositive_class_exponents():
    with pytest.raises(ValueError):
        CSTCurve(r0=1.0, r1=0.5, weights=(0.1,), n1=0.0, n2=0.5)
    with pytest.raises(ValueError):
        CSTCurve(r0=1.0, r1=0.5, weights=(0.1,), n1=0.5, n2=-1.0)


def test_class_function_vanishes_at_both_ends():
    curve = CSTCurve(r0=1.0, r1=0.5, weights=(0.2, 0.3, 0.1))
    assert curve.class_value(0.0) == 0.0
    assert curve.class_value(1.0) == 0.0


def test_class_function_symmetric_when_exponents_match():
    curve = CSTCurve(r0=1.0, r1=0.5, weights=(0.2,), n1=0.7, n2=0.7)
    for psi in (0.1, 0.3, 0.45):
        assert curve.class_value(psi) == pytest.approx(curve.class_value(1 - psi))


def test_curve_hits_endpoint_values_exactly():
    """r(0)=r0 and r(1)=r1 regardless of the weights — the whole reason the
    linear baseline term was added on top of the ordinary CST curve."""
    curve = CSTCurve(r0=0.85, r1=0.42, weights=(3.0, -1.5, 2.2, 0.4))
    assert curve(0.0) == pytest.approx(0.85)
    assert curve(1.0) == pytest.approx(0.42)


def test_zero_weights_gives_the_linear_baseline_exactly():
    """No bump: the curve must be a straight line between the two ends."""
    curve = CSTCurve(r0=1.0, r1=0.4, weights=(0.0, 0.0, 0.0))
    for psi in (0.0, 0.25, 0.5, 0.75, 1.0):
        expected = (1 - psi) * 1.0 + psi * 0.4
        assert curve(psi) == pytest.approx(expected)


def test_equal_weights_give_a_constant_shape_value():
    """Partition of unity: the Bernstein basis sums to 1 at every psi, so
    equal weights A must make shape_value(psi) == A everywhere — not just
    at a few sampled points."""
    curve = CSTCurve(r0=1.0, r1=0.4, weights=(0.6, 0.6, 0.6, 0.6, 0.6))
    for psi in (0.05, 0.2, 0.4, 0.6, 0.8, 0.95):
        assert curve.shape_value(psi) == pytest.approx(0.6, abs=1e-9)


def test_order_matches_weight_count_minus_one():
    assert CSTCurve(r0=1.0, r1=0.5, weights=(0.1, 0.2, 0.3)).order == 2
    assert CSTCurve(r0=1.0, r1=0.5, weights=(0.1,)).order == 0


def test_positive_weights_bulge_above_the_baseline():
    curve = CSTCurve(r0=0.8, r1=0.6, weights=(1.0, 1.0, 1.0))
    mid_baseline = 0.5 * (0.8 + 0.6)
    assert curve(0.5) > mid_baseline
